"""Research tools — web search when available, otherwise labeled local knowledge."""

from __future__ import annotations

from langchain_core.tools import tool

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

LOCAL_KNOWLEDGE: dict[str, list[dict]] = {
    "full stack developer": [
        {
            "title": "MDN JavaScript Guide",
            "summary": "Core language concepts interviewers expect for JS-heavy roles.",
            "source": "MDN Web Docs (local knowledge entry)",
            "url": "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide",
            "topics": ["JavaScript", "Web APIs"],
        },
        {
            "title": "React Official Docs — Learn React",
            "summary": "Component model, hooks, and data flow fundamentals.",
            "source": "react.dev (local knowledge entry)",
            "url": "https://react.dev/learn",
            "topics": ["React"],
        },
        {
            "title": "Node.js Guides",
            "summary": "Server-side JS, modules, and HTTP basics.",
            "source": "nodejs.org (local knowledge entry)",
            "url": "https://nodejs.org/en/learn",
            "topics": ["Node.js", "REST APIs"],
        },
    ],
    "software engineer": [
        {
            "title": "Interview DS&A patterns",
            "summary": "Arrays, hash maps, trees, graphs, and complexity analysis.",
            "source": "CareerPilot local knowledge",
            "url": None,
            "topics": ["Data Structures", "Algorithms"],
        },
        {
            "title": "System design primer topics",
            "summary": "Load balancing, caching, databases, and scalability trade-offs.",
            "source": "CareerPilot local knowledge",
            "url": None,
            "topics": ["System Design"],
        },
    ],
    "default": [
        {
            "title": "Role fundamentals checklist",
            "summary": "Core concepts, hands-on practice, and behavioural storytelling.",
            "source": "CareerPilot local knowledge",
            "url": None,
            "topics": ["Fundamentals", "Interview Prep"],
        }
    ],
}


def _local_research(query: str, role: str) -> list[dict]:
    key = role.strip().lower()
    items = LOCAL_KNOWLEDGE.get(key) or []
    if not items:
        for k, v in LOCAL_KNOWLEDGE.items():
            if k in key or key in k:
                items = v
                break
    if not items:
        items = LOCAL_KNOWLEDGE["default"]

    results = []
    for item in items:
        results.append(
            {
                **item,
                "source_type": "local_knowledge",
                "query": query,
                "label": "LOCAL_KNOWLEDGE_TOOL — not live web browsing",
            }
        )
    return results


def _web_research(query: str, max_results: int = 5) -> list[dict]:
    """Attempt DuckDuckGo search. Raises if package/network unavailable."""
    from duckduckgo_search import DDGS

    results: list[dict] = []
    with DDGS() as ddgs:
        for row in ddgs.text(query, max_results=max_results):
            results.append(
                {
                    "title": row.get("title") or "Untitled",
                    "summary": row.get("body") or "",
                    "source": "duckduckgo_search",
                    "source_type": "web",
                    "url": row.get("href"),
                    "topics": [query],
                    "label": "WEB_RESEARCH_TOOL",
                }
            )
    return results


@tool
def research_topics(query: str, target_role: str = "", max_results: int = 5) -> dict:
    """
    Research interview topics and learning resources for a query/role.

    Tries live DuckDuckGo search when ENABLE_WEB_RESEARCH=true.
    Falls back to a clearly labeled local knowledge tool otherwise.

    Args:
        query: Research query (skills, technologies, interview topics).
        target_role: Optional role context.
        max_results: Max web results to return.
    """
    settings = get_settings()
    used = "local_knowledge"
    items: list[dict] = []
    error: str | None = None

    if settings.enable_web_research:
        try:
            items = _web_research(query, max_results=max_results)
            used = "web"
        except Exception as exc:  # noqa: BLE001
            error = str(exc)
            logger.warning("Web research failed (%s); using local knowledge tool", exc)
            items = _local_research(query, target_role or query)
            used = "local_knowledge_fallback"
    else:
        items = _local_research(query, target_role or query)

    return {
        "tool": "research_topics",
        "query": query,
        "target_role": target_role,
        "backend_used": used,
        "error": error,
        "results": items,
        "count": len(items),
    }
