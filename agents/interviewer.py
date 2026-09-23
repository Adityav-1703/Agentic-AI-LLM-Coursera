"""Interview agent — generates mock interview question sets via tools."""

from __future__ import annotations

import json
from typing import Any

from app.agents.helpers import activity, llm, message, update_memory
from app.core.logging import get_logger, log_span
from app.graph.state import CareerState
from app.tools.interview import generate_interview_questions

logger = get_logger(__name__)


def interviewer_node(state: CareerState) -> dict[str, Any]:
    with log_span(logger, "interviewer_node", session_id=state.get("session_id")):
        role = state.get("target_role") or "Software Engineer"
        gaps = state.get("skill_gaps") or state.get("priority_skills") or []
        level = state.get("experience_level") or "intermediate"

        tool_result = generate_interview_questions.invoke(
            {
                "target_role": role,
                "skill_gaps": list(gaps),
                "experience_level": level,
                "count_per_category": 2,
            }
        )
        questions = list(tool_result.get("questions") or [])

        try:
            client = llm()
            client.complete_json(
                system=(
                    "You are an interview coach. Acknowledge the question set. "
                    "Return JSON: session_intro (str)."
                ),
                user=(
                    f"Role={role}, level={level}, count={len(questions)}\n"
                    f"OFFLINE_HINT_JSON: {json.dumps({'session_intro': f'Mock interview ready for {role}.'})}"
                ),
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Interviewer LLM intro skipped: %s", exc)

        prev = list((state.get("memory") or {}).get("previous_question_ids") or [])
        ids = [q["id"] for q in questions]
        mem = update_memory(
            state,
            previous_question_ids=list(dict.fromkeys(prev + ids)),
            last_interview_count=len(questions),
        )

        summary = (
            f"Generated {len(questions)} interview questions "
            f"(difficulty={tool_result.get('difficulty')})."
        )

        return {
            "current_agent": "interviewer",
            "interview_questions": questions,
            "workflow_status": "interviewing",
            "memory": mem,
            "agent_messages": [
                message("interviewer", summary, tool="generate_interview_questions")
            ],
            "activity_log": [
                activity(
                    "interviewer",
                    "generate_questions",
                    summary,
                    tool="generate_interview_questions",
                    count=len(questions),
                    user_summary=f"Prepared {len(questions)} interview practice questions.",
                )
            ],
        }
