"""Skill-gap analysis tool — hierarchical role → skill → subskill mapping."""

from __future__ import annotations

from typing import Any, Literal

from langchain_core.tools import tool

SkillStatus = Literal["strong", "developing", "needs_improvement"]
SkillPriority = Literal["high", "medium", "low"]

# Curated hierarchical catalogs (local tool — not live labor-market data).
ROLE_SKILL_CATALOG: dict[str, dict[str, Any]] = {
    "full stack developer": {
        "skills": [
            {
                "name": "JavaScript",
                "subskills": ["Closures", "Promises", "Async/await", "Event loop"],
                "default_priority": "high",
            },
            {
                "name": "TypeScript",
                "subskills": ["Types", "Interfaces", "Generics"],
                "default_priority": "medium",
            },
            {
                "name": "React",
                "subskills": ["Components", "Props", "State", "Hooks", "Rendering"],
                "default_priority": "high",
            },
            {
                "name": "Node.js",
                "subskills": ["Modules", "HTTP servers", "Middleware", "Async I/O"],
                "default_priority": "medium",
            },
            {
                "name": "REST APIs",
                "subskills": ["Resources", "Status codes", "Validation", "Error handling"],
                "default_priority": "high",
            },
            {
                "name": "SQL Databases",
                "subskills": ["Queries", "Indexes", "Joins", "Transactions"],
                "default_priority": "medium",
            },
            {
                "name": "Git",
                "subskills": ["Branching", "Pull requests", "Conflict resolution"],
                "default_priority": "low",
            },
            {
                "name": "System Design Basics",
                "subskills": ["Caching", "Load balancing", "Scalability trade-offs"],
                "default_priority": "medium",
            },
            {
                "name": "Testing",
                "subskills": ["Unit tests", "Integration tests", "Test doubles"],
                "default_priority": "high",
            },
            {
                "name": "Authentication",
                "subskills": ["Sessions", "JWT", "OAuth basics"],
                "default_priority": "medium",
            },
        ],
        "priority": ["JavaScript", "React", "REST APIs", "Testing"],
    },
    "frontend developer": {
        "skills": [
            {
                "name": "HTML/CSS",
                "subskills": ["Semantic HTML", "Flexbox", "Grid", "Responsive layout"],
                "default_priority": "medium",
            },
            {
                "name": "JavaScript",
                "subskills": ["DOM", "Async programming", "Modules"],
                "default_priority": "high",
            },
            {
                "name": "TypeScript",
                "subskills": ["Types", "Interfaces", "Strict mode"],
                "default_priority": "high",
            },
            {
                "name": "React",
                "subskills": ["Components", "State management", "Hooks", "Performance"],
                "default_priority": "high",
            },
            {
                "name": "Web Performance",
                "subskills": ["Bundling", "Lazy loading", "Core Web Vitals"],
                "default_priority": "high",
            },
            {
                "name": "Accessibility",
                "subskills": ["ARIA", "Keyboard navigation", "Contrast"],
                "default_priority": "medium",
            },
            {
                "name": "Testing",
                "subskills": ["Component tests", "E2E basics"],
                "default_priority": "medium",
            },
            {
                "name": "Git",
                "subskills": ["Branching", "Code review"],
                "default_priority": "low",
            },
        ],
        "priority": ["JavaScript", "React", "Web Performance", "TypeScript"],
    },
    "backend developer": {
        "skills": [
            {
                "name": "Python or Node.js",
                "subskills": ["Language idioms", "Async patterns", "Packaging"],
                "default_priority": "high",
            },
            {
                "name": "REST APIs",
                "subskills": ["Resources", "Status codes", "Validation", "Versioning"],
                "default_priority": "high",
            },
            {
                "name": "SQL Databases",
                "subskills": ["Schema design", "Indexes", "Query plans"],
                "default_priority": "high",
            },
            {
                "name": "Caching",
                "subskills": ["Redis patterns", "Invalidation", "TTL"],
                "default_priority": "medium",
            },
            {
                "name": "Authentication",
                "subskills": ["JWT", "OAuth", "RBAC"],
                "default_priority": "medium",
            },
            {
                "name": "System Design",
                "subskills": ["Services", "Queues", "Consistency"],
                "default_priority": "high",
            },
            {
                "name": "Testing",
                "subskills": ["Unit tests", "Integration tests", "Contract tests"],
                "default_priority": "high",
            },
            {
                "name": "Docker Basics",
                "subskills": ["Images", "Compose", "Networking"],
                "default_priority": "medium",
            },
            {
                "name": "Git",
                "subskills": ["Branching", "Reviews"],
                "default_priority": "low",
            },
        ],
        "priority": ["REST APIs", "SQL Databases", "System Design", "Testing"],
    },
    "data scientist": {
        "skills": [
            {
                "name": "Python",
                "subskills": ["Pandas", "NumPy", "Scripting"],
                "default_priority": "high",
            },
            {
                "name": "Statistics",
                "subskills": ["Distributions", "Hypothesis testing", "Bias"],
                "default_priority": "high",
            },
            {
                "name": "SQL",
                "subskills": ["Joins", "Aggregations", "Window functions"],
                "default_priority": "high",
            },
            {
                "name": "Machine Learning Basics",
                "subskills": ["Supervised learning", "Validation", "Overfitting"],
                "default_priority": "high",
            },
            {
                "name": "Experiment Design",
                "subskills": ["A/B testing", "Metrics", "Sample size"],
                "default_priority": "medium",
            },
            {
                "name": "Data Visualization",
                "subskills": ["Charts", "Storytelling", "Dashboards"],
                "default_priority": "medium",
            },
            {
                "name": "Communication",
                "subskills": ["Stakeholder updates", "Result write-ups"],
                "default_priority": "medium",
            },
        ],
        "priority": ["Python", "Statistics", "Machine Learning Basics", "SQL"],
    },
    "devops engineer": {
        "skills": [
            {
                "name": "Linux",
                "subskills": ["Shell", "Processes", "Permissions"],
                "default_priority": "high",
            },
            {
                "name": "CI/CD",
                "subskills": ["Pipelines", "Artifacts", "Gates"],
                "default_priority": "high",
            },
            {
                "name": "Docker",
                "subskills": ["Images", "Registries", "Compose"],
                "default_priority": "high",
            },
            {
                "name": "Kubernetes Basics",
                "subskills": ["Pods", "Services", "Deployments"],
                "default_priority": "medium",
            },
            {
                "name": "Cloud Fundamentals",
                "subskills": ["IAM", "Networking", "Managed services"],
                "default_priority": "high",
            },
            {
                "name": "Monitoring",
                "subskills": ["Metrics", "Logs", "Alerts"],
                "default_priority": "high",
            },
            {
                "name": "Infrastructure as Code",
                "subskills": ["Terraform basics", "Idempotency"],
                "default_priority": "medium",
            },
            {
                "name": "Git",
                "subskills": ["Branching", "Reviews"],
                "default_priority": "low",
            },
        ],
        "priority": ["CI/CD", "Docker", "Cloud Fundamentals", "Monitoring"],
    },
    "software engineer": {
        "skills": [
            {
                "name": "Data Structures",
                "subskills": ["Arrays", "Hash maps", "Trees", "Graphs"],
                "default_priority": "high",
            },
            {
                "name": "Algorithms",
                "subskills": ["Sorting", "Searching", "Complexity analysis"],
                "default_priority": "high",
            },
            {
                "name": "System Design",
                "subskills": ["APIs", "Caching", "Databases", "Trade-offs"],
                "default_priority": "high",
            },
            {
                "name": "One Backend Language",
                "subskills": ["Syntax", "Standard library", "Debugging"],
                "default_priority": "medium",
            },
            {
                "name": "SQL",
                "subskills": ["Queries", "Indexes"],
                "default_priority": "medium",
            },
            {
                "name": "Testing",
                "subskills": ["Unit tests", "Edge cases"],
                "default_priority": "high",
            },
            {
                "name": "Git",
                "subskills": ["Branching", "Reviews"],
                "default_priority": "low",
            },
            {
                "name": "Problem Solving",
                "subskills": ["Decomposition", "Trade-offs"],
                "default_priority": "high",
            },
            {
                "name": "Communication",
                "subskills": ["STAR stories", "Clarity"],
                "default_priority": "medium",
            },
        ],
        "priority": ["Data Structures", "Algorithms", "System Design", "Problem Solving"],
    },
}

LEVEL_STATUS_BIAS: dict[str, dict[str, SkillStatus]] = {
    "beginner": {
        "default": "needs_improvement",
        "Git": "developing",
        "Communication": "developing",
    },
    "intermediate": {
        "default": "developing",
        "Git": "strong",
        "HTML/CSS": "strong",
    },
    "advanced": {
        "default": "strong",
        "System Design": "developing",
        "System Design Basics": "developing",
        "Testing": "developing",
    },
}


def _normalize_role(role: str) -> str:
    key = role.strip().lower()
    aliases = {
        "fullstack": "full stack developer",
        "full-stack developer": "full stack developer",
        "full stack": "full stack developer",
        "front end developer": "frontend developer",
        "front-end developer": "frontend developer",
        "back end developer": "backend developer",
        "back-end developer": "backend developer",
        "ml engineer": "data scientist",
        "sde": "software engineer",
    }
    return aliases.get(key, key)


def resolve_catalog(target_role: str) -> tuple[str, dict[str, Any]]:
    role_key = _normalize_role(target_role)
    catalog = ROLE_SKILL_CATALOG.get(role_key)
    if not catalog:
        for key, value in ROLE_SKILL_CATALOG.items():
            if key in role_key or role_key in key:
                return key, value
        return "software engineer", ROLE_SKILL_CATALOG["software engineer"]
    return role_key, catalog


def subskills_for(skill_name: str, role_key: str | None = None) -> list[str]:
    catalogs = (
        [ROLE_SKILL_CATALOG[role_key]]
        if role_key and role_key in ROLE_SKILL_CATALOG
        else list(ROLE_SKILL_CATALOG.values())
    )
    for catalog in catalogs:
        for skill in catalog["skills"]:
            if skill["name"].lower() == skill_name.lower():
                return list(skill.get("subskills") or [])
    return [f"{skill_name} fundamentals"]


def map_topic_to_skill(topic: str, role_key: str) -> str | None:
    """Map an evidence topic / signal to a catalog skill name when possible."""
    t = topic.strip().lower()
    if not t:
        return None
    _, catalog = resolve_catalog(role_key)
    for skill in catalog["skills"]:
        name = skill["name"]
        if name.lower() == t or t in name.lower() or name.lower() in t:
            return name
        for sub in skill.get("subskills") or []:
            if sub.lower() == t or t in sub.lower() or sub.lower() in t:
                return name
    # Common aliases
    aliases = {
        "resources": "REST APIs",
        "status codes": "REST APIs",
        "validation": "REST APIs",
        "errors": "REST APIs",
        "error handling": "REST APIs",
        "jwt": "Authentication",
        "hooks": "React",
        "components": "React",
        "promises": "JavaScript",
        "async": "JavaScript",
        "indexes": "SQL Databases",
        "unit tests": "Testing",
    }
    for key, skill in aliases.items():
        if key in t:
            # Prefer skill if it exists in this role catalog
            names = {s["name"] for s in catalog["skills"]}
            if skill in names:
                return skill
            if skill == "SQL Databases" and "SQL" in names:
                return "SQL"
    return None


def _status_for(
    skill_name: str,
    *,
    level: str,
    known: set[str],
    priority_names: set[str],
) -> SkillStatus:
    if skill_name.lower() in known:
        return "strong"
    bias = LEVEL_STATUS_BIAS.get(level, LEVEL_STATUS_BIAS["intermediate"])
    if skill_name in bias:
        return bias[skill_name]  # type: ignore[return-value]
    status: SkillStatus = bias.get("default", "developing")  # type: ignore[assignment]
    if level == "advanced" and skill_name in priority_names:
        return "developing"
    if level == "beginner" and skill_name in priority_names:
        return "needs_improvement"
    return status


def _priority_for(skill_name: str, priority_list: list[str], default: str) -> SkillPriority:
    if skill_name in priority_list[:2]:
        return "high"
    if skill_name in priority_list:
        return "high" if default == "high" else "medium"
    if default == "high":
        return "medium"
    if default == "low":
        return "low"
    return "medium"


def build_skill_assessments(
    target_role: str,
    experience_level: str = "intermediate",
    known_skills: list[str] | None = None,
    evidence_topics: list[str] | None = None,
) -> dict[str, Any]:
    known = {s.strip().lower() for s in (known_skills or []) if s.strip()}
    role_key, catalog = resolve_catalog(target_role)
    level = experience_level.strip().lower()
    priority_list: list[str] = list(catalog["priority"])
    priority_set = set(priority_list)

    evidence_by_skill: dict[str, list[str]] = {}
    for topic in evidence_topics or []:
        mapped = map_topic_to_skill(str(topic), role_key)
        if mapped:
            evidence_by_skill.setdefault(mapped, []).append(str(topic))

    assessments: list[dict[str, Any]] = []
    for skill in catalog["skills"]:
        name = skill["name"]
        status = _status_for(
            name, level=level, known=known, priority_names=priority_set
        )
        # Evidence of missing interview signals upgrades status toward needs_improvement
        evidence = list(dict.fromkeys(evidence_by_skill.get(name, [])))
        if evidence and status == "strong":
            status = "developing"
        if len(evidence) >= 2 and status == "developing":
            status = "needs_improvement"

        priority = _priority_for(name, priority_list, skill.get("default_priority", "medium"))
        why = None
        if status != "strong":
            if evidence:
                why = (
                    f"Interview answers missed related signals "
                    f"({', '.join(evidence[:3])})."
                )
            elif name in priority_list and not known:
                why = (
                    f"Priority skill for {role_key.title()} at {level} level; "
                    "not marked as already known."
                )
            else:
                why = (
                    f"Included in the {role_key.title()} role catalog and not marked "
                    "as a known strength."
                )

        assessments.append(
            {
                "name": name,
                "status": status,
                "priority": priority,
                "subskills": list(skill.get("subskills") or []),
                "evidence": evidence,
                "why_gap": why,
            }
        )

    skills = [a["name"] for a in assessments]
    gaps = [
        a["name"]
        for a in assessments
        if a["status"] in ("needs_improvement", "developing") and a["priority"] in ("high", "medium")
    ]
    # Prefer high-priority needs_improvement first
    gaps_sorted = sorted(
        [a for a in assessments if a["name"] in gaps],
        key=lambda a: (
            0 if a["status"] == "needs_improvement" else 1,
            0 if a["priority"] == "high" else 1,
            a["name"],
        ),
    )
    gap_names = [a["name"] for a in gaps_sorted]

    needs_clarification = len(target_role.strip()) < 3
    return {
        "tool": "analyze_skill_gaps",
        "source": "local_role_catalog",
        "target_role": role_key.title(),
        "role_key": role_key,
        "skills": skills,
        "priority_skills": priority_list,
        "skill_gaps": gap_names[:8],
        "skill_assessments": assessments,
        "needs_clarification": needs_clarification,
        "clarification_question": (
            "What specific role title are you targeting?"
            if needs_clarification
            else None
        ),
        "notes": (
            "Hierarchical skill map from CareerPilot local role catalog. "
            "Not live labor-market data. Gaps reflect catalog + level + known skills "
            "and optional interview evidence — not invented biography."
        ),
    }


@tool
def analyze_skill_gaps(
    target_role: str,
    experience_level: str = "intermediate",
    known_skills: list[str] | None = None,
) -> dict:
    """
    Produce a hierarchical skill map and likely gaps for a target role.

    This is a local catalog tool (not live job-market scraping).

    Args:
        target_role: Desired job title / role.
        experience_level: beginner | intermediate | advanced
        known_skills: Optional skills the user already claims.
    """
    return build_skill_assessments(
        target_role=target_role,
        experience_level=experience_level,
        known_skills=known_skills,
    )
