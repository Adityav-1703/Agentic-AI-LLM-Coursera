"""Interview question generator tool."""

from __future__ import annotations

import hashlib

from langchain_core.tools import tool

BANK: dict[str, dict[str, list[dict]]] = {
    "default": {
        "technical": [
            {
                "prompt": "Explain how you would design a REST API for a simple resource and why.",
                "expected_signals": ["resources", "status codes", "validation", "errors"],
            },
            {
                "prompt": "What is the difference between authentication and authorization?",
                "expected_signals": ["identity", "permissions", "examples"],
            },
            {
                "prompt": "How do indexes improve database read performance, and what are the trade-offs?",
                "expected_signals": ["lookup speed", "write cost", "storage"],
            },
        ],
        "behavioral": [
            {
                "prompt": "Tell me about a time you disagreed with a teammate. How did you resolve it?",
                "expected_signals": ["context", "action", "result", "reflection"],
            },
            {
                "prompt": "Describe a project that slipped schedule. What did you change?",
                "expected_signals": ["ownership", "communication", "mitigation"],
            },
        ],
        "coding": [
            {
                "prompt": "Write a function that returns the first non-repeating character in a string.",
                "expected_signals": ["hash map", "complexity", "edge cases"],
            },
            {
                "prompt": "Implement a function to merge two sorted arrays into one sorted array.",
                "expected_signals": ["two pointers", "O(n) time", "tests"],
            },
        ],
    },
    "full stack developer": {
        "technical": [
            {
                "prompt": "How does the React reconciliation/virtual DOM idea help UI updates?",
                "expected_signals": ["diffing", "declarative UI", "performance nuance"],
            },
            {
                "prompt": "Compare SQL and NoSQL for a user-profile service and when you'd choose each.",
                "expected_signals": ["consistency", "schema", "query patterns"],
            },
            {
                "prompt": "Walk through JWT-based auth for a SPA + API. What are the risks?",
                "expected_signals": ["access token", "refresh", "XSS", "storage"],
            },
        ],
        "behavioral": [
            {
                "prompt": "Describe shipping a feature across frontend and backend. How did you coordinate?",
                "expected_signals": ["API contract", "testing", "rollout"],
            }
        ],
        "coding": [
            {
                "prompt": "Implement rate limiting logic for an API endpoint (in-memory is fine).",
                "expected_signals": ["window", "counter", "edge cases"],
            },
            {
                "prompt": "Given nested comments JSON, write a function to flatten it for display.",
                "expected_signals": ["recursion/stack", "ordering", "tests"],
            },
        ],
    },
}


def _qid(category: str, prompt: str) -> str:
    digest = hashlib.sha1(f"{category}:{prompt}".encode()).hexdigest()[:10]
    return f"{category[:3]}_{digest}"


def _pick_bank(role: str) -> dict[str, list[dict]]:
    key = role.strip().lower()
    if key in BANK:
        return BANK[key]
    for k, v in BANK.items():
        if k != "default" and (k in key or key in k):
            return v
    return BANK["default"]


@tool
def generate_interview_questions(
    target_role: str,
    skill_gaps: list[str] | None = None,
    experience_level: str = "intermediate",
    count_per_category: int = 2,
) -> dict:
    """
    Generate technical, behavioural, and coding interview questions.

    Args:
        target_role: Role under preparation.
        skill_gaps: Optional gaps to bias question selection.
        experience_level: beginner | intermediate | advanced
        count_per_category: How many questions per category.
    """
    level = experience_level.lower().strip()
    difficulty = {
        "beginner": "beginner",
        "intermediate": "intermediate",
        "advanced": "advanced",
    }.get(level, "intermediate")

    bank = _pick_bank(target_role)
    gaps = [g.lower() for g in (skill_gaps or [])]
    questions: list[dict] = []

    for category in ("technical", "behavioral", "coding"):
        pool = list(bank.get(category) or BANK["default"][category])
        # Prefer prompts mentioning gap keywords
        if gaps:
            pool.sort(
                key=lambda q: sum(1 for g in gaps if g in q["prompt"].lower()),
                reverse=True,
            )
        for item in pool[: max(1, count_per_category)]:
            questions.append(
                {
                    "id": _qid(category, item["prompt"]),
                    "category": category,
                    "difficulty": difficulty,
                    "prompt": item["prompt"],
                    "expected_signals": item.get("expected_signals", []),
                }
            )

    return {
        "tool": "generate_interview_questions",
        "target_role": target_role,
        "difficulty": difficulty,
        "questions": questions,
        "count": len(questions),
    }
