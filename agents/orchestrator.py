"""Orchestrator / supervisor agent — plans and routes, does not do specialist work."""

from __future__ import annotations

import json
from typing import Any

from app.agents.helpers import activity, llm, message, update_memory
from app.core.logging import get_logger, log_span
from app.graph.state import CareerState

logger = get_logger(__name__)


def _rule_based_route(state: CareerState) -> tuple[str, str, str]:
    """Deterministic routing used as primary control (LLM may refine reason)."""
    status = state.get("workflow_status", "initialized")
    if state.get("error"):
        return "end", "error", f"Stopping due to error: {state.get('error')}"

    if state.get("needs_clarification") and not state.get("target_role"):
        return (
            "human",
            "awaiting_clarification",
            "Career analyst needs a clearer target role.",
        )

    if not state.get("skills"):
        return "career_analyst", "analyzing", "Need a skill map for the target role."

    if not state.get("research_sufficient"):
        return "researcher", "researching", "Research required for resources/topics."

    if not state.get("study_plan"):
        return "study_planner", "planning_study", "Build a study plan from skill gaps."

    if state.get("study_plan") and not state.get("plan_confirmed"):
        return (
            "human",
            "awaiting_plan_confirmation",
            "Human confirmation required before finalizing the study plan.",
        )

    if state.get("major_weaknesses") and (state.get("replanning_count") or 0) < 2:
        return (
            "study_planner",
            "planning_study",
            "Evaluator found major weaknesses — replan study focus.",
        )

    if not state.get("interview_questions"):
        return "interviewer", "interviewing", "Generate interview practice questions."

    if state.get("user_answers") and len(state.get("user_answers") or []) > len(
        state.get("evaluation_results") or []
    ):
        return "evaluator", "evaluating", "New answers awaiting evaluation."

    # Explicit report request (after practice) — do not auto-report before answers.
    if state.get("ready_for_report") and not state.get("final_report"):
        return "report_agent", "reporting", "User requested final report generation."

    if state.get("final_report"):
        return "end", "completed", "Workflow complete."

    return (
        "end",
        "awaiting_answers",
        "Interview questions ready — submit answers or request the final report.",
    )


def orchestrator_node(state: CareerState) -> dict[str, Any]:
    with log_span(logger, "orchestrator_node", session_id=state.get("session_id")):
        next_agent, status, reason = _rule_based_route(state)

        # Optional LLM rationale (never overrides safety-critical routing without keys)
        rationale = reason
        try:
            client = llm()
            hint = {
                "suggested_next_agent": next_agent,
                "reason": reason,
                "workflow_complete": next_agent == "end",
            }
            data = client.complete_json(
                system=(
                    "You are the CareerPilot orchestrator. Confirm or lightly refine "
                    "the routing rationale. Return JSON with keys: next_agent, reason, "
                    "workflow_complete. Prefer the suggested next_agent unless clearly wrong."
                ),
                user=(
                    f"State summary: role={state.get('target_role')}, "
                    f"skills={bool(state.get('skills'))}, "
                    f"research={state.get('research_sufficient')}, "
                    f"plan={bool(state.get('study_plan'))}, "
                    f"confirmed={state.get('plan_confirmed')}, "
                    f"questions={len(state.get('interview_questions') or [])}, "
                    f"evals={len(state.get('evaluation_results') or [])}, "
                    f"report={bool(state.get('final_report'))}, "
                    f"major_weaknesses={state.get('major_weaknesses')}.\n"
                    f"OFFLINE_HINT_JSON: {json.dumps(hint)}"
                ),
            )
            if data.get("reason"):
                rationale = str(data["reason"])
            # Only allow LLM to change route among known agents if it matches rules loosely
            proposed = data.get("next_agent")
            allowed = {
                "career_analyst",
                "researcher",
                "study_planner",
                "interviewer",
                "evaluator",
                "report_agent",
                "human",
                "end",
            }
            if proposed in allowed and proposed == next_agent:
                next_agent = proposed
        except Exception as exc:  # noqa: BLE001
            logger.warning("Orchestrator LLM rationale skipped: %s", exc)

        mem = update_memory(
            state,
            last_route=next_agent,
            last_route_reason=rationale,
            target_role=state.get("target_role"),
        )

        return {
            "current_agent": "orchestrator",
            "next_agent": next_agent,
            "workflow_status": status,
            "memory": mem,
            "agent_messages": [
                message("orchestrator", f"Routing → {next_agent}. {rationale}")
            ],
            "activity_log": [
                activity(
                    "orchestrator",
                    "route",
                    rationale,
                    next_agent=next_agent,
                    user_summary=f"Routed preparation to the next step ({next_agent.replace('_', ' ')}).",
                )
            ],
        }
