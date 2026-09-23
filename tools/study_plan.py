"""Study-plan generation tool — week → day → topic → subtopics schedule."""

from __future__ import annotations

from typing import Any

from langchain_core.tools import tool

from app.tools.calculator import calculate_study_hours
from app.tools.skill_analysis import subskills_for


def _week_theme(skill_names: list[str], week_index: int) -> str:
    if not skill_names:
        return f"Week {week_index} Foundations"
    # Group consecutive skills into a theme label
    chunk = skill_names[: min(3, len(skill_names))]
    if len(chunk) == 1:
        return f"{chunk[0]} Foundations"
    if len(chunk) == 2:
        return f"{chunk[0]} & {chunk[1]}"
    return f"{chunk[0]}, {chunk[1]} & {chunk[2]}"


@tool
def generate_study_plan(
    skill_gaps: list[str],
    days: int,
    hours_per_day: float,
    experience_level: str = "intermediate",
    role_key: str = "",
) -> dict:
    """
    Convert skill gaps into a week/day study plan with balanced activity types.

    Args:
        skill_gaps: Skills to prioritize (catalog skill names preferred).
        days: Preparation window in days.
        hours_per_day: Daily study budget.
        experience_level: beginner | intermediate | advanced
        role_key: Optional role key for subskill lookup.
    """
    if not skill_gaps:
        skill_gaps = ["Fundamentals", "Problem Solving"]
    days = max(1, int(days))
    hours_per_day = max(0.5, float(hours_per_day))

    budget = calculate_study_hours.invoke(
        {"days": days, "hours_per_day": hours_per_day}
    )
    gaps = skill_gaps[: max(4, min(len(skill_gaps), 10))]

    schedule: list[dict[str, Any]] = []
    for day in range(1, days + 1):
        focus = gaps[(day - 1) % len(gaps)]
        subtopics = subskills_for(focus, role_key or None)[:4]
        phase = (day - 1) % 4
        theory = coding = revision = mock = 0.0
        tasks: list[str] = []

        if phase == 0:
            theory = round(hours_per_day * 0.6, 2)
            coding = round(hours_per_day * 0.4, 2)
            tasks = [
                f"Study: {', '.join(subtopics[:3]) or focus}",
                f"Take notes on {focus} fundamentals",
                f"Complete 1 guided exercise on {focus}",
            ]
            topic_title = f"{focus} Core Concepts"
        elif phase == 1:
            coding = round(hours_per_day * 0.7, 2)
            theory = round(hours_per_day * 0.3, 2)
            tasks = [
                f"Practice problems for {focus}",
                "Time-box coding and note complexity",
                "Review mistakes from previous day",
            ]
            topic_title = f"{focus} Practice"
        elif phase == 2:
            revision = round(hours_per_day * 0.5, 2)
            coding = round(hours_per_day * 0.5, 2)
            tasks = [
                f"Revise weak points in {focus}",
                "Re-solve one previous problem without notes",
                "Summarize trade-offs in your own words",
            ]
            topic_title = f"{focus} Revision"
        else:
            mock = round(hours_per_day * 0.5, 2)
            revision = round(hours_per_day * 0.3, 2)
            coding = round(hours_per_day * 0.2, 2)
            tasks = [
                f"Mock interview focused on {focus}",
                "Record answers and self-critique",
                "Update your weakness checklist",
            ]
            topic_title = f"{focus} Mock Interview"

        if experience_level.lower() == "beginner" and day <= max(3, days // 5):
            theory = round(hours_per_day * 0.7, 2)
            coding = round(hours_per_day * 0.3, 2)
            mock = 0.0
            revision = 0.0
            tasks = [
                f"Foundations deep-dive: {', '.join(subtopics[:2]) or focus}",
                "Follow one trusted tutorial section",
                "Build a tiny demo snippet",
            ]
            topic_title = f"{focus} Foundations"

        schedule.append(
            {
                "day": day,
                "week": ((day - 1) // 7) + 1,
                "focus": focus,
                "topic": topic_title,
                "subtopics": subtopics,
                "theory_hours": theory,
                "coding_hours": coding,
                "revision_hours": revision,
                "mock_interview_hours": mock,
                "tasks": tasks,
                "completed": False,
            }
        )

    # Build week groupings
    weeks: list[dict[str, Any]] = []
    max_week = max((d["week"] for d in schedule), default=1)
    for w in range(1, max_week + 1):
        week_days = [d for d in schedule if d["week"] == w]
        focuses = list(dict.fromkeys(d["focus"] for d in week_days))
        weeks.append(
            {
                "week": w,
                "theme": _week_theme(focuses, w),
                "focus_skills": focuses,
                "days": [d["day"] for d in week_days],
            }
        )

    return {
        "tool": "generate_study_plan",
        "total_days": days,
        "hours_per_day": hours_per_day,
        "days": schedule,
        "weeks": weeks,
        "budget": budget,
        "balance_notes": (
            "Plan balances theory, coding, revision, and mock interviews, "
            "organized by week and topic. Generated by local scheduling tool."
        ),
        "confirmed": False,
    }
