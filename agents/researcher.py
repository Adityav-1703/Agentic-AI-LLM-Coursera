"""Research agent — uses research tools, returns structured sources."""

from __future__ import annotations

import json
from typing import Any

from app.agents.helpers import activity, llm, message, update_memory
from app.core.logging import get_logger, log_span
from app.graph.state import CareerState
from app.tools.research import research_topics

logger = get_logger(__name__)


def researcher_node(state: CareerState) -> dict[str, Any]:
    with log_span(logger, "researcher_node", session_id=state.get("session_id")):
        role = state.get("target_role") or "software engineer"
        gaps = state.get("priority_skills") or state.get("skill_gaps") or ["fundamentals"]
        query = f"{role} interview preparation {' '.join(gaps[:3])}"

        tool_result = research_topics.invoke(
            {"query": query, "target_role": role, "max_results": 5}
        )
        results = list(tool_result.get("results") or [])

        # Secondary query on top gap
        if gaps:
            extra = research_topics.invoke(
                {
                    "query": f"{gaps[0]} interview questions and learning resources",
                    "target_role": role,
                    "max_results": 3,
                }
            )
            results.extend(extra.get("results") or [])

        # Deduplicate by title
        seen: set[str] = set()
        deduped: list[dict] = []
        for item in results:
            title = (item.get("title") or "").strip().lower()
            if title and title not in seen:
                seen.add(title)
                deduped.append(item)

        sufficient = len(deduped) >= 1
        notes = ""
        try:
            client = llm()
            refined = client.complete_json(
                system=(
                    "You are a research agent. Summarize tool results. Do not invent URLs. "
                    "Return JSON: topics (list), notes (str), research_sufficient (bool)."
                ),
                user=(
                    f"Tool backend: {tool_result.get('backend_used')}\n"
                    f"Results: {json.dumps(deduped)[:4000]}\n"
                    f"OFFLINE_HINT_JSON: {json.dumps({'topics': gaps, 'notes': 'Tool-backed research.', 'research_sufficient': sufficient})}"
                ),
            )
            notes = refined.get("notes") or ""
            if "research_sufficient" in refined:
                sufficient = bool(refined["research_sufficient"]) or sufficient
        except Exception as exc:  # noqa: BLE001
            logger.warning("Research LLM summarize skipped: %s", exc)

        mem = update_memory(
            state,
            research_count=len(deduped),
            research_backend=tool_result.get("backend_used"),
        )

        summary = (
            f"Collected {len(deduped)} research items via "
            f"{tool_result.get('backend_used')}."
            + (f" {notes}" if notes else "")
        )

        return {
            "current_agent": "researcher",
            "research_results": deduped,
            "research_sufficient": sufficient,
            "workflow_status": "researching",
            "memory": mem,
            "agent_messages": [
                message(
                    "researcher",
                    summary,
                    backend=tool_result.get("backend_used"),
                    error=tool_result.get("error"),
                )
            ],
            "activity_log": [
                activity(
                    "researcher",
                    "research",
                    summary,
                    tool="research_topics",
                    count=len(deduped),
                    user_summary=(
                        f"Found {len(deduped)} learning resources"
                        + (
                            " (local fallback catalog)."
                            if "local" in str(tool_result.get("backend_used"))
                            else "."
                        )
                    ),
                )
            ],
        }
