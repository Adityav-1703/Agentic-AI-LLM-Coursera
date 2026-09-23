"""Human-in-the-loop node — pauses for clarification or plan confirmation."""

from __future__ import annotations

from typing import Any

from langgraph.types import interrupt

from app.agents.helpers import activity, message, update_memory
from app.graph.state import CareerState


def human_gate_node(state: CareerState) -> dict[str, Any]:
    """
    Interrupt the graph so the API can collect a human decision.

    Resume payload shapes:
      {"action": "clarify", "target_role": "...", "user_goal": "..."}
      {"action": "approve"}
      {"action": "modify", "modifications": "..."}
      {"action": "restart"}
    """
    status = state.get("workflow_status")

    if status == "awaiting_clarification" or state.get("needs_clarification"):
        payload = {
            "type": "clarification",
            "title": "We need a bit more detail",
            "question": state.get("clarification_question")
            or "Please clarify your target role and goal.",
            "session_id": state.get("session_id"),
        }
        decision = interrupt(payload)
        action = (decision or {}).get("action", "clarify")
        if action == "restart":
            return {
                "current_agent": "human",
                "skills": [],
                "priority_skills": [],
                "skill_gaps": [],
                "skill_assessments": [],
                "research_results": [],
                "research_sufficient": False,
                "study_plan": None,
                "plan_confirmed": False,
                "interview_questions": [],
                "evaluation_results": [],
                "final_report": None,
                "needs_clarification": False,
                "workflow_status": "initialized",
                "agent_messages": [message("human", "Workflow restart requested.")],
                "activity_log": [
                    activity(
                        "human",
                        "restart",
                        "User restarted workflow",
                        user_summary="Preparation restarted.",
                    )
                ],
            }

        new_role = (decision or {}).get("target_role") or state.get("target_role")
        new_goal = (decision or {}).get("user_goal") or state.get("user_goal")
        mem = update_memory(state, clarified=True)
        return {
            "current_agent": "human",
            "target_role": new_role,
            "user_goal": new_goal,
            "needs_clarification": False,
            "clarification_question": None,
            "skills": [],
            "skill_assessments": [],
            "workflow_status": "analyzing",
            "memory": mem,
            "agent_messages": [
                message("human", f"Clarified target role: {new_role}")
            ],
            "activity_log": [
                activity(
                    "human",
                    "clarify",
                    f"Role set to {new_role}",
                    user_summary=f"Updated target role to {new_role}.",
                )
            ],
        }

    priority = state.get("priority_skills") or state.get("skill_gaps") or []
    plan = state.get("study_plan") or {}
    weeks = plan.get("weeks") or []
    payload = {
        "type": "plan_confirmation",
        "title": "Your personalized plan is ready for review.",
        "message": (
            "Review your priority skills, duration, and daily commitment before continuing."
        ),
        "priority_skills": priority,
        "focus_areas": priority[:5],
        "available_days": state.get("available_days") or plan.get("total_days"),
        "hours_per_day": state.get("hours_per_day") or plan.get("hours_per_day"),
        "week_themes": [w.get("theme") for w in weeks[:4]],
        "study_plan_preview": {
            "total_days": plan.get("total_days"),
            "hours_per_day": plan.get("hours_per_day"),
            "weeks": weeks[:4],
            "first_three_days": (plan.get("days") or [])[:3],
        },
        "options": ["approve", "modify", "restart"],
        "session_id": state.get("session_id"),
    }
    decision = interrupt(payload)
    action = (decision or {}).get("action", "approve")

    if action == "restart":
        return {
            "current_agent": "human",
            "skills": [],
            "priority_skills": [],
            "skill_gaps": [],
            "skill_assessments": [],
            "research_results": [],
            "research_sufficient": False,
            "study_plan": None,
            "plan_confirmed": False,
            "plan_modifications": None,
            "interview_questions": [],
            "user_answers": [],
            "evaluation_results": [],
            "final_report": None,
            "workflow_status": "initialized",
            "agent_messages": [message("human", "Workflow restart requested.")],
            "activity_log": [
                activity(
                    "human",
                    "restart",
                    "User restarted workflow",
                    user_summary="Preparation restarted.",
                )
            ],
        }

    if action == "modify":
        mods = (decision or {}).get("modifications") or ""
        return {
            "current_agent": "human",
            "plan_confirmed": False,
            "plan_modifications": mods,
            "study_plan": None,
            "workflow_status": "planning_study",
            "agent_messages": [
                message("human", f"Plan modification requested: {mods}")
            ],
            "activity_log": [
                activity(
                    "human",
                    "modify_plan",
                    mods,
                    user_summary="Requested plan changes.",
                )
            ],
        }

    plan = dict(state.get("study_plan") or {})
    plan["confirmed"] = True
    mem = update_memory(state, plan_confirmed=True)
    return {
        "current_agent": "human",
        "study_plan": plan,
        "plan_confirmed": True,
        "plan_modifications": None,
        "workflow_status": "interviewing",
        "memory": mem,
        "agent_messages": [message("human", "Study plan approved.")],
        "activity_log": [
            activity(
                "human",
                "approve_plan",
                "User approved study plan",
                user_summary="Study plan confirmed.",
            )
        ],
    }
