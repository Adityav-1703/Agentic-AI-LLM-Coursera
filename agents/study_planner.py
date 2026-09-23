"""Study Planner agent — converts gaps into a week/day schedule; HITL follows."""

from __future__ import annotations

import json
from typing import Any

from app.agents.helpers import activity, llm, message, update_memory
from app.core.logging import get_logger, log_span
from app.graph.state import CareerState
from app.tools.study_plan import generate_study_plan

logger = get_logger(__name__)


def study_planner_node(state: CareerState) -> dict[str, Any]:
    with log_span(logger, "study_planner_node", session_id=state.get("session_id")):
        gaps = (
            state.get("skill_gaps")
            or state.get("priority_skills")
            or state.get("skills")
            or ["Fundamentals"]
        )

        if state.get("major_weaknesses"):
            weak_topics: list[str] = []
            for ev in state.get("evaluation_results") or []:
                for topic in ev.get("mapped_skill_gaps") or []:
                    t = str(topic).strip()
                    if t:
                        weak_topics.append(t)
                for topic in ev.get("study_next") or []:
                    t = str(topic).strip()
                    if not t or len(t) > 60:
                        continue
                    if t.endswith(".") or t.count(" ") >= 6:
                        continue
                    weak_topics.append(t)
            if weak_topics:
                gaps = list(dict.fromkeys(weak_topics + list(gaps)))

        mods = (state.get("plan_modifications") or "").strip()
        if mods:
            extra = [p.strip() for p in mods.replace(";", ",").split(",") if p.strip()]
            gaps = list(dict.fromkeys(extra + list(gaps)))

        days = int(state.get("available_days") or 30)
        hours = float(state.get("hours_per_day") or 2.0)
        level = state.get("experience_level") or "intermediate"
        role_key = str((state.get("memory") or {}).get("role_key") or "")

        plan = generate_study_plan.invoke(
            {
                "skill_gaps": list(gaps)[:10],
                "days": days,
                "hours_per_day": hours,
                "experience_level": level,
                "role_key": role_key,
            }
        )

        try:
            client = llm()
            refined = client.complete_json(
                system=(
                    "You are a study planner. Optionally improve balance_notes. "
                    "Do not invent days. Return JSON with balance_notes."
                ),
                user=(
                    f"Plan meta: days={plan.get('total_days')}, hours={plan.get('hours_per_day')}, "
                    f"gaps={gaps}\nOFFLINE_HINT_JSON: {json.dumps({'balance_notes': plan.get('balance_notes')})}"
                ),
            )
            if refined.get("balance_notes"):
                plan["balance_notes"] = refined["balance_notes"]
        except Exception as exc:  # noqa: BLE001
            logger.warning("Study planner LLM notes skipped: %s", exc)

        plan["confirmed"] = False
        replanning = int(state.get("replanning_count") or 0)
        if state.get("major_weaknesses"):
            replanning += 1

        mem = update_memory(
            state,
            study_plan_days=plan.get("total_days"),
            last_plan_focus=gaps[:5],
        )

        summary = (
            f"Drafted {plan.get('total_days')}-day plan "
            f"({plan.get('hours_per_day')} h/day). Awaiting human confirmation."
        )
        user_summary = (
            f"Created your personalized {plan.get('total_days')}-day study plan "
            f"({plan.get('hours_per_day')} h/day)."
        )

        return {
            "current_agent": "study_planner",
            "study_plan": plan,
            "plan_confirmed": False,
            "skill_gaps": list(gaps)[:10],
            "major_weaknesses": False,
            "replanning_count": replanning,
            "workflow_status": "awaiting_plan_confirmation",
            "memory": mem,
            "agent_messages": [message("study_planner", summary, tool="generate_study_plan")],
            "activity_log": [
                activity(
                    "study_planner",
                    "draft_plan",
                    summary,
                    tool="generate_study_plan",
                    user_summary=user_summary,
                )
            ],
        }
