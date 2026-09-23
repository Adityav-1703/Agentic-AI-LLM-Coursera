"""Calculator tool — deterministic math for study-hour budgeting."""

from __future__ import annotations

from langchain_core.tools import tool


@tool
def calculate_study_hours(days: int, hours_per_day: float) -> dict:
    """
    Calculate total preparation hours and suggested allocation buckets.

    Args:
        days: Number of preparation days available.
        hours_per_day: Hours the user can study each day.
    """
    if days < 1:
        raise ValueError("days must be >= 1")
    if hours_per_day <= 0:
        raise ValueError("hours_per_day must be > 0")

    total = round(days * hours_per_day, 2)
    # Balanced split: theory 30%, coding 40%, revision 20%, mock 10%
    return {
        "tool": "calculate_study_hours",
        "days": days,
        "hours_per_day": hours_per_day,
        "total_hours": total,
        "allocation": {
            "theory": round(total * 0.30, 2),
            "coding": round(total * 0.40, 2),
            "revision": round(total * 0.20, 2),
            "mock_interview": round(total * 0.10, 2),
        },
    }
