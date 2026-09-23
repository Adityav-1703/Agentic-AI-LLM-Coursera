"""Career workflow service — bridges API ↔ LangGraph ↔ SQLite."""

from __future__ import annotations

import uuid
from typing import Any

from app.core.config import get_settings
from app.core.logging import get_logger, log_span
from app.graph.workflow import (
    get_state_snapshot,
    initial_state,
    resume_with_decision,
    run_until_pause,
)
from app.services.session_store import get_store
from app.tools.skill_analysis import analyze_skill_gaps

logger = get_logger(__name__)

AGENT_FLOW = [
    "orchestrator",
    "career_analyst",
    "researcher",
    "study_planner",
    "interviewer",
    "evaluator",
    "report_agent",
]

AGENT_TASKS = {
    "orchestrator": "Route the preparation workflow",
    "career_analyst": "Identify skill requirements",
    "researcher": "Research interview topics and resources",
    "study_planner": "Generate a personalized study plan",
    "interviewer": "Generate interview questions",
    "evaluator": "Evaluate interview responses",
    "report_agent": "Generate the final assessment report",
    "human": "Review and confirm the study plan",
}


def _completed_agents(state: dict[str, Any]) -> list[str]:
    seen: list[str] = []
    for event in state.get("activity_log") or []:
        agent = event.get("agent")
        if agent and agent not in seen:
            seen.append(agent)
    return seen


def _derive_agent_statuses(state: dict[str, Any]) -> list[dict[str, Any]]:
    completed = set(_completed_agents(state))
    current = state.get("current_agent")
    status = state.get("workflow_status") or ""
    interrupted = bool(state.get("interrupted"))
    pending = state.get("pending_interrupt")
    has_skills = bool(state.get("skills"))
    has_research = bool(state.get("research_sufficient"))
    has_plan = bool(state.get("study_plan"))
    plan_confirmed = bool(state.get("plan_confirmed"))
    has_questions = bool(state.get("interview_questions"))
    has_evals = bool(state.get("evaluation_results"))
    has_report = bool(state.get("final_report"))
    error = state.get("error")

    # Presence gates used to mark skipped only when workflow advanced past them
    presence = {
        "orchestrator": True,
        "career_analyst": has_skills,
        "researcher": has_research,
        "study_planner": has_plan,
        "interviewer": has_questions,
        "evaluator": has_evals,
        "report_agent": has_report,
    }

    rows: list[dict[str, Any]] = []
    for agent in AGENT_FLOW:
        row_status = "pending"
        reason = None
        if error and current == agent:
            row_status = "failed"
            reason = str(error)
        elif interrupted and pending and (
            (pending.get("type") == "plan_confirmation" and agent == "study_planner")
            or (status == "awaiting_plan_confirmation" and agent == "study_planner")
            or agent == "human"
            or (current == "human" and agent == "study_planner")
        ):
            if agent == "study_planner" and has_plan and not plan_confirmed:
                row_status = "needs_review"
                reason = "Waiting for plan approval"
            elif agent == "human" or (
                interrupted and agent == AGENT_FLOW[AGENT_FLOW.index("study_planner")]
            ):
                pass
        elif agent == current and status not in ("completed", "awaiting_answers"):
            if interrupted and pending:
                row_status = "waiting_for_user"
            else:
                row_status = "running"
        elif agent in completed or presence.get(agent):
            if agent == "study_planner" and has_plan and not plan_confirmed and interrupted:
                row_status = "needs_review"
                reason = "Plan ready for review"
            else:
                row_status = "completed"
        elif has_report or status == "completed":
            # Past agents that never ran while workflow finished elsewhere
            if not presence.get(agent) and agent not in completed:
                # Only mark skipped if later agents completed
                later_done = any(
                    presence.get(a) or a in completed
                    for a in AGENT_FLOW[AGENT_FLOW.index(agent) + 1 :]
                )
                if later_done:
                    row_status = "skipped"
                    reason = "Not required for this path"
        rows.append(
            {
                "id": agent,
                "label": agent.replace("_", " ").title().replace("Report Agent", "Report Agent"),
                "status": row_status,
                "task": AGENT_TASKS.get(agent, ""),
                "reason": reason,
            }
        )

    # Human row (HITL)
    human_status = "pending"
    human_reason = None
    if interrupted and pending:
        human_status = "waiting_for_user"
        human_reason = pending.get("title") or pending.get("message")
    elif plan_confirmed:
        human_status = "completed"
        human_reason = "Study plan approved"
    elif "human" in completed:
        human_status = "completed"

    # Insert human after study_planner for inspector display
    human_row = {
        "id": "human",
        "label": "Your review",
        "status": human_status,
        "task": AGENT_TASKS["human"],
        "reason": human_reason,
    }
    out: list[dict[str, Any]] = []
    for row in rows:
        out.append(row)
        if row["id"] == "study_planner":
            out.append(human_row)
    return out


def _interview_performance(state: dict[str, Any]) -> dict[str, Any]:
    evals = state.get("evaluation_results") or []
    by_cat: dict[str, list[float]] = {"technical": [], "behavioral": [], "coding": []}
    for e in evals:
        cat = (e.get("category") or "").lower()
        if cat in by_cat:
            by_cat[cat].append(float(e.get("score", 0)))
    scores = [float(e.get("score", 0)) for e in evals]
    overall = round(sum(scores) / len(scores), 2) if scores else None
    weakest: list[str] = []
    for e in evals:
        weakest.extend(e.get("mapped_skill_gaps") or [])
        for t in e.get("recommended_topics") or e.get("study_next") or []:
            if len(str(t)) <= 40:
                weakest.append(str(t))
    return {
        "overall": overall,
        "technical": round(sum(by_cat["technical"]) / len(by_cat["technical"]), 2)
        if by_cat["technical"]
        else None,
        "behavioral": round(sum(by_cat["behavioral"]) / len(by_cat["behavioral"]), 2)
        if by_cat["behavioral"]
        else None,
        "coding": round(sum(by_cat["coding"]) / len(by_cat["coding"]), 2)
        if by_cat["coding"]
        else None,
        "weakest_areas": list(dict.fromkeys(weakest))[:5],
        "criteria_weights": {
            "relevance": 0.30,
            "correctness_signals": 0.35,
            "structure": 0.20,
            "specificity": 0.15,
        },
    }


def _progress_dashboard(state: dict[str, Any]) -> dict[str, Any]:
    questions = state.get("interview_questions") or []
    answers = state.get("user_answers") or []
    plan = state.get("study_plan") or {}
    days = plan.get("days") or []
    completed_days = sum(1 for d in days if d.get("completed"))
    assessments = state.get("skill_assessments") or []
    research = state.get("research_results") or []
    interview_pct = (
        round(100 * len(answers) / len(questions), 1) if questions else 0.0
    )
    study_pct = (
        round(100 * completed_days / len(days), 1) if days else 0.0
    )
    research_pct = 100.0 if research else 0.0
    skill_total = len(assessments) or len(state.get("skills") or [])
    skill_pct = 100.0 if skill_total else 0.0
    overall = round(
        interview_pct * 0.35 + study_pct * 0.25 + research_pct * 0.15 + skill_pct * 0.25,
        1,
    )
    gaps = state.get("skill_gaps") or state.get("priority_skills") or []
    focus = (
        f"Improve {', '.join(gaps[:3])}."
        if gaps
        else "Start your preparation plan to unlock a focus area."
    )
    next_action = "Build your preparation plan."
    if state.get("interrupted"):
        next_action = "Review and approve your study plan."
    elif questions and len(answers) < len(questions):
        next_action = "Practice the next interview question."
    elif days and not state.get("final_report"):
        next_action = "Complete today's study session."
    elif state.get("final_report"):
        next_action = "Review your CareerPilot assessment report."

    return {
        "overall_pct": overall,
        "interview_completion_pct": interview_pct,
        "study_completion_pct": study_pct,
        "research_completion_pct": research_pct,
        "skill_coverage": {
            "assessed": skill_total,
            "total": skill_total,
            "pct": skill_pct,
        },
        "current_focus": focus,
        "next_action": next_action,
    }


def serialize_session(state: dict[str, Any]) -> dict[str, Any]:
    pending = state.get("pending_interrupt")
    if pending is not None and not isinstance(pending, dict):
        value = getattr(pending, "value", None)
        pending = value if isinstance(value, dict) else {"message": str(pending)}

    settings = get_settings()
    return {
        "session_id": state.get("session_id"),
        "workflow_status": state.get("workflow_status", "unknown"),
        "current_agent": state.get("current_agent"),
        "next_agent": state.get("next_agent"),
        "interrupted": bool(state.get("interrupted")),
        "pending_interrupt": pending,
        "target_role": state.get("target_role"),
        "user_goal": state.get("user_goal"),
        "experience_level": state.get("experience_level"),
        "available_days": state.get("available_days"),
        "hours_per_day": state.get("hours_per_day"),
        "skills": state.get("skills") or [],
        "priority_skills": state.get("priority_skills") or [],
        "skill_gaps": state.get("skill_gaps") or [],
        "skill_assessments": state.get("skill_assessments") or [],
        "research_results": state.get("research_results") or [],
        "study_plan": state.get("study_plan"),
        "plan_confirmed": bool(state.get("plan_confirmed")),
        "interview_questions": state.get("interview_questions") or [],
        "user_answers": state.get("user_answers") or [],
        "evaluation_results": state.get("evaluation_results") or [],
        "interview_performance": _interview_performance(state),
        "progress": _progress_dashboard(state),
        "agent_statuses": _derive_agent_statuses(state),
        "final_report": state.get("final_report"),
        "agent_messages": state.get("agent_messages") or [],
        "activity_log": state.get("activity_log") or [],
        "memory": state.get("memory") or {},
        "error": state.get("error"),
        "completed_agents": _completed_agents(state),
        "llm_provider": settings.llm_provider,
        "architecture": {
            "framework": "LangGraph",
            "state": "Typed shared CareerState",
            "routing": "Conditional graph edges",
            "persistence": "SQLite + MemorySaver checkpoints",
            "human_in_the_loop": "LangGraph interrupt",
            "llm": settings.llm_provider,
            "api": "FastAPI",
            "frontend": "React + TypeScript",
        },
    }


class CareerService:
    def analyze(
        self,
        *,
        user_goal: str,
        target_role: str,
        experience_level: str,
        known_skills: list[str] | None = None,
    ) -> dict[str, Any]:
        result = analyze_skill_gaps.invoke(
            {
                "target_role": target_role or user_goal,
                "experience_level": experience_level,
                "known_skills": known_skills or [],
            }
        )
        result["user_goal"] = user_goal
        return result

    def start(
        self,
        *,
        user_goal: str,
        target_role: str,
        experience_level: str,
        available_days: int,
        hours_per_day: float,
    ) -> dict[str, Any]:
        session_id = str(uuid.uuid4())
        state = initial_state(
            session_id=session_id,
            user_goal=user_goal,
            target_role=target_role,
            experience_level=experience_level,
            available_days=available_days,
            hours_per_day=hours_per_day,
        )
        store = get_store()
        store.create_session(
            {
                "session_id": session_id,
                "user_goal": user_goal,
                "target_role": target_role,
                "experience_level": experience_level,
                "available_days": available_days,
                "hours_per_day": hours_per_day,
            },
            dict(state),
        )

        with log_span(logger, "career_start", session_id=session_id):
            try:
                result = run_until_pause(session_id, state)
            except Exception as exc:  # noqa: BLE001
                logger.exception("Workflow failed to start")
                err_state = dict(state)
                err_state["error"] = str(exc)
                err_state["workflow_status"] = "error"
                store.save_state(session_id, err_state)
                raise

        result["session_id"] = session_id
        store.save_state(session_id, result)
        return serialize_session(result)

    def status(self, session_id: str) -> dict[str, Any]:
        snap = get_state_snapshot(session_id)
        store = get_store()
        if snap:
            snap["session_id"] = session_id
            store.save_state(session_id, snap)
            return serialize_session(snap)
        saved = store.get_state(session_id)
        if not saved:
            raise KeyError(session_id)
        return serialize_session(saved)

    def decide(self, session_id: str, decision: dict[str, Any]) -> dict[str, Any]:
        with log_span(
            logger, "human_decision", session_id=session_id, action=decision.get("action")
        ):
            result = resume_with_decision(session_id, decision)
        result["session_id"] = session_id
        get_store().save_state(session_id, result)
        return serialize_session(result)

    def add_answer(self, session_id: str, question_id: str, answer: str) -> dict[str, Any]:
        snap = get_state_snapshot(session_id) or get_store().get_state(session_id)
        if not snap:
            raise KeyError(session_id)

        questions = {q["id"]: q for q in (snap.get("interview_questions") or [])}
        q = questions.get(question_id)
        answers = list(snap.get("user_answers") or [])
        answers = [a for a in answers if a.get("question_id") != question_id]
        entry = {
            "question_id": question_id,
            "answer": answer,
            "question_prompt": (q or {}).get("prompt"),
        }
        answers.append(entry)

        mem = dict(snap.get("memory") or {})
        prev = list(mem.get("previous_answers") or [])
        prev.append({"question_id": question_id, "answer_preview": answer[:200]})
        mem["previous_answers"] = prev[-20:]

        from app.graph.workflow import career_graph

        config = {"configurable": {"thread_id": session_id}}
        career_graph.update_state(
            config,
            {
                "user_answers": answers,
                "memory": mem,
                "session_id": session_id,
            },
        )
        return self.status(session_id)

    def evaluate(self, session_id: str) -> dict[str, Any]:
        snap = get_state_snapshot(session_id)
        if not snap:
            raise KeyError(session_id)

        if snap.get("interrupted") and snap.get("pending_interrupt"):
            raise RuntimeError(
                "Session is waiting for a human decision before evaluation can continue."
            )

        from app.graph.workflow import career_graph

        config = {"configurable": {"thread_id": session_id}}
        career_graph.update_state(
            config,
            {
                "session_id": session_id,
                "workflow_status": "evaluating",
            },
        )
        result = run_until_pause(session_id, None)
        result["session_id"] = session_id
        get_store().save_state(session_id, result)
        return serialize_session(result)

    def request_report(self, session_id: str) -> dict[str, Any]:
        snap = get_state_snapshot(session_id)
        if not snap:
            raise KeyError(session_id)

        # If waiting on plan reconfirmation after evaluator-driven replan,
        # auto-approve so report generation can finish (portfolio UX).
        if snap.get("interrupted") and snap.get("pending_interrupt"):
            pending = snap.get("pending_interrupt") or {}
            if pending.get("type") == "plan_confirmation":
                self.decide(session_id, {"action": "approve"})
            else:
                raise RuntimeError(
                    "Session is waiting for a human decision before the report can be generated."
                )

        from app.graph.workflow import career_graph

        config = {"configurable": {"thread_id": session_id}}
        career_graph.update_state(
            config,
            {"ready_for_report": True, "session_id": session_id},
        )
        result = run_until_pause(session_id, None)
        result["session_id"] = session_id
        get_store().save_state(session_id, result)
        return serialize_session(result)

    def study_plan(self, session_id: str) -> dict[str, Any]:
        state = self.status(session_id)
        plan = state.get("study_plan")
        if not plan:
            raise ValueError("Study plan not available yet for this session.")
        return {
            "session_id": session_id,
            "plan_confirmed": state.get("plan_confirmed"),
            "study_plan": plan,
            "priority_skills": state.get("priority_skills"),
            "skill_gaps": state.get("skill_gaps"),
            "skill_assessments": state.get("skill_assessments"),
        }


career_service = CareerService()
