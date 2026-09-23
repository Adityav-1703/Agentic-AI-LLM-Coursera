"""Report agent — consolidates multi-agent outputs into a final report."""

from __future__ import annotations

from typing import Any

from app.agents.helpers import activity, message, update_memory
from app.core.logging import get_logger, log_span
from app.graph.state import CareerState
from app.tools.progress import generate_final_report, track_progress

logger = get_logger(__name__)


def report_agent_node(state: CareerState) -> dict[str, Any]:
    with log_span(logger, "report_agent_node", session_id=state.get("session_id")):
        questions = state.get("interview_questions") or []
        answers = state.get("user_answers") or []
        plan = state.get("study_plan") or {}
        assessments = state.get("skill_assessments") or []
        progress = track_progress.invoke(
            {
                "total_questions": len(questions),
                "answered_questions": len(answers),
                "evaluations": state.get("evaluation_results") or [],
                "study_days_total": int(plan.get("total_days") or 0),
                "study_days_completed": int(
                    (state.get("memory") or {}).get("study_days_completed") or 0
                ),
                "research_count": len(state.get("research_results") or []),
                "skill_assessed": len(assessments),
                "skill_total": len(assessments) or len(state.get("skills") or []),
            }
        )

        report = generate_final_report.invoke(
            {
                "target_role": state.get("target_role") or "Unknown role",
                "skill_gaps": state.get("skill_gaps") or [],
                "research_results": state.get("research_results") or [],
                "study_plan": plan,
                "interview_questions": questions,
                "evaluation_results": state.get("evaluation_results") or [],
                "progress": progress,
                "available_days": int(state.get("available_days") or 30),
                "hours_per_day": float(state.get("hours_per_day") or 2.0),
            }
        )

        mem = update_memory(state, report_generated=True, progress=progress)
        summary = f"Final report ready for {report.get('target_role')}."

        return {
            "current_agent": "report_agent",
            "final_report": report,
            "workflow_status": "completed",
            "next_agent": "end",
            "memory": mem,
            "agent_messages": [
                message("report_agent", summary, tool="generate_final_report")
            ],
            "activity_log": [
                activity(
                    "report_agent",
                    "final_report",
                    summary,
                    tool="generate_final_report",
                    user_summary="Generated your CareerPilot assessment report.",
                )
            ],
        }
