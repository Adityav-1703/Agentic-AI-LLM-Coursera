"""Career Analyst agent — role analysis and hierarchical skill map."""

from __future__ import annotations

import json
from typing import Any

from app.agents.helpers import activity, llm, message, update_memory
from app.core.logging import get_logger, log_span
from app.graph.state import CareerState
from app.tools.skill_analysis import analyze_skill_gaps

logger = get_logger(__name__)


def career_analyst_node(state: CareerState) -> dict[str, Any]:
    with log_span(logger, "career_analyst_node", session_id=state.get("session_id")):
        role = state.get("target_role") or state.get("user_goal") or ""
        level = state.get("experience_level") or "intermediate"
        known = list((state.get("memory") or {}).get("known_skills") or [])

        tool_result = analyze_skill_gaps.invoke(
            {
                "target_role": role,
                "experience_level": level,
                "known_skills": known,
            }
        )

        notes = tool_result.get("notes", "")
        priority = tool_result.get("priority_skills") or []
        gaps = tool_result.get("skill_gaps") or []
        skills = tool_result.get("skills") or []
        assessments = tool_result.get("skill_assessments") or []
        target = tool_result.get("target_role") or role
        needs = bool(tool_result.get("needs_clarification"))
        question = tool_result.get("clarification_question")

        try:
            client = llm()
            refined = client.complete_json(
                system=(
                    "You are a career analyst. Given a tool-produced skill map, refine "
                    "notes only. Do not invent unrelated skills or change the skill list. "
                    "Return JSON: notes, needs_clarification, clarification_question."
                ),
                user=(
                    f"User goal: {state.get('user_goal')}\n"
                    f"Tool result summary: role={target}, skills={len(skills)}, gaps={gaps}\n"
                    f"OFFLINE_HINT_JSON: {json.dumps({'notes': notes, 'needs_clarification': needs, 'clarification_question': question})}"
                ),
            )
            notes = refined.get("notes") or notes
            if "needs_clarification" in refined:
                needs = bool(refined["needs_clarification"])
            if refined.get("clarification_question"):
                question = refined["clarification_question"]
        except Exception as exc:  # noqa: BLE001
            logger.warning("Career analyst LLM refine skipped: %s", exc)

        goal = (state.get("user_goal") or "").strip()
        if len(goal) < 8 and not state.get("target_role"):
            needs = True
            question = question or (
                "Please specify the target role and timeframe more clearly "
                "(e.g., 'Full Stack Developer interview in 30 days')."
            )

        mem = update_memory(
            state,
            target_role=target,
            priority_skills=priority,
            skill_gaps=gaps,
            role_key=tool_result.get("role_key"),
        )

        summary = (
            f"Skill map for {target}: {len(skills)} skills, "
            f"{len(gaps)} gaps. Priority: {', '.join(priority[:5])}."
        )
        user_summary = (
            f"Completed your skill assessment for {target}. "
            f"Priority focus: {', '.join(priority[:3]) or 'core fundamentals'}."
        )

        return {
            "current_agent": "career_analyst",
            "target_role": target,
            "skills": skills,
            "priority_skills": priority,
            "skill_gaps": gaps,
            "skill_assessments": assessments,
            "needs_clarification": needs,
            "clarification_question": question,
            "workflow_status": (
                "awaiting_clarification" if needs else "analyzing"
            ),
            "memory": mem,
            "agent_messages": [message("career_analyst", summary, tool=tool_result)],
            "activity_log": [
                activity(
                    "career_analyst",
                    "skill_map",
                    summary,
                    tool="analyze_skill_gaps",
                    user_summary=user_summary,
                )
            ],
        }
