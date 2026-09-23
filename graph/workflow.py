"""LangGraph workflow with conditional orchestration."""

from __future__ import annotations

from typing import Any, Literal

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command

from app.agents.career_analyst import career_analyst_node
from app.agents.evaluator import evaluator_node
from app.agents.human_gate import human_gate_node
from app.agents.interviewer import interviewer_node
from app.agents.orchestrator import orchestrator_node
from app.agents.report_agent import report_agent_node
from app.agents.researcher import researcher_node
from app.agents.study_planner import study_planner_node
from app.core.logging import get_logger
from app.graph.state import CareerState

logger = get_logger(__name__)

AgentRoute = Literal[
    "career_analyst",
    "researcher",
    "study_planner",
    "interviewer",
    "evaluator",
    "report_agent",
    "human",
    "end",
]


def route_from_orchestrator(
    state: CareerState,
) -> AgentRoute:
    nxt = state.get("next_agent") or "end"
    mapping: dict[str, AgentRoute] = {
        "career_analyst": "career_analyst",
        "researcher": "researcher",
        "study_planner": "study_planner",
        "interviewer": "interviewer",
        "evaluator": "evaluator",
        "report_agent": "report_agent",
        "human": "human",
        "end": "end",
    }
    return mapping.get(nxt, "end")


def after_specialist(state: CareerState) -> Literal["orchestrator"]:
    """Specialists return control to the orchestrator for the next decision."""
    return "orchestrator"


def build_workflow(checkpointer: MemorySaver | None = None):
    graph = StateGraph(CareerState)

    graph.add_node("orchestrator", orchestrator_node)
    graph.add_node("career_analyst", career_analyst_node)
    graph.add_node("researcher", researcher_node)
    graph.add_node("study_planner", study_planner_node)
    graph.add_node("interviewer", interviewer_node)
    graph.add_node("evaluator", evaluator_node)
    graph.add_node("report_agent", report_agent_node)
    graph.add_node("human", human_gate_node)

    graph.add_edge(START, "orchestrator")

    graph.add_conditional_edges(
        "orchestrator",
        route_from_orchestrator,
        {
            "career_analyst": "career_analyst",
            "researcher": "researcher",
            "study_planner": "study_planner",
            "interviewer": "interviewer",
            "evaluator": "evaluator",
            "report_agent": "report_agent",
            "human": "human",
            "end": END,
        },
    )

    for node in (
        "career_analyst",
        "researcher",
        "study_planner",
        "interviewer",
        "evaluator",
    ):
        graph.add_conditional_edges(node, after_specialist, {"orchestrator": "orchestrator"})

    # Human gate returns to orchestrator (or restart path still goes through orchestrator)
    graph.add_edge("human", "orchestrator")
    # Report completes the workflow
    graph.add_edge("report_agent", END)

    memory = checkpointer or MemorySaver()
    return graph.compile(checkpointer=memory)


# Process-wide compiled graph + checkpointer for API sessions
_checkpointer = MemorySaver()
career_graph = build_workflow(_checkpointer)


def initial_state(
    *,
    session_id: str,
    user_goal: str,
    target_role: str,
    experience_level: str,
    available_days: int,
    hours_per_day: float,
) -> CareerState:
    return {
        "session_id": session_id,
        "user_goal": user_goal,
        "target_role": target_role,
        "experience_level": experience_level,
        "available_days": available_days,
        "hours_per_day": hours_per_day,
        "skills": [],
        "priority_skills": [],
        "skill_gaps": [],
        "skill_assessments": [],
        "needs_clarification": False,
        "clarification_question": None,
        "research_results": [],
        "research_sufficient": False,
        "study_plan": None,
        "plan_confirmed": False,
        "plan_modifications": None,
        "interview_questions": [],
        "user_answers": [],
        "evaluation_results": [],
        "major_weaknesses": False,
        "replanning_count": 0,
        "final_report": None,
        "ready_for_report": False,
        "agent_messages": [],
        "activity_log": [],
        "current_agent": "orchestrator",
        "next_agent": "career_analyst",
        "workflow_status": "initialized",
        "error": None,
        "memory": {
            "target_role": target_role,
            "previous_answers": [],
            "identified_weaknesses": [],
            "previous_question_ids": [],
            "previous_evaluation_results": [],
        },
    }


def run_until_pause(session_id: str, state: CareerState | None = None) -> dict[str, Any]:
    """Invoke/resume graph until END or a human interrupt."""
    config = {"configurable": {"thread_id": session_id}}
    if state is not None:
        result = career_graph.invoke(state, config=config)
    else:
        # Continue from checkpoint by re-entering the orchestrator.
        result = career_graph.invoke(Command(goto="orchestrator"), config=config)
    return _augment_with_interrupt(session_id, result)


def resume_with_decision(session_id: str, decision: dict[str, Any]) -> dict[str, Any]:
    config = {"configurable": {"thread_id": session_id}}
    result = career_graph.invoke(Command(resume=decision), config=config)
    return _augment_with_interrupt(session_id, result)


def _interrupt_payload(raw: Any) -> dict[str, Any] | None:
    """Normalize LangGraph interrupt objects into plain JSON-serializable dicts."""
    if raw is None:
        return None
    if isinstance(raw, dict):
        return raw
    value = getattr(raw, "value", None)
    if isinstance(value, dict):
        return value
    if value is not None:
        return {"value": str(value)}
    # Fallback: string form (never return Interrupt instance)
    return {"message": str(raw)}


def get_state_snapshot(session_id: str) -> dict[str, Any] | None:
    config = {"configurable": {"thread_id": session_id}}
    snap = career_graph.get_state(config)
    if not snap or snap.values is None:
        return None
    data = dict(snap.values)
    data["interrupted"] = bool(snap.next)
    data["next_nodes"] = list(snap.next or [])
    tasks = getattr(snap, "tasks", None) or []
    interrupts: list[Any] = []
    for task in tasks:
        for intr in getattr(task, "interrupts", None) or []:
            interrupts.append(_interrupt_payload(intr))
    # Also check snap.interrupts if present (langgraph versions vary)
    for intr in getattr(snap, "interrupts", None) or []:
        interrupts.append(_interrupt_payload(intr))
    data["pending_interrupt"] = next((i for i in interrupts if i), None)
    return data


def _json_safe(obj: Any) -> Any:
    """Recursively coerce state into JSON-serializable structures."""
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return {str(k): _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_safe(v) for v in obj]
    # LangGraph Interrupt / other objects
    if type(obj).__name__ == "Interrupt" or hasattr(obj, "value"):
        payload = _interrupt_payload(obj)
        return payload
    return str(obj)


def _augment_with_interrupt(session_id: str, result: dict[str, Any]) -> dict[str, Any]:
    snap = get_state_snapshot(session_id)
    out = _json_safe(dict(result or {}))
    if snap:
        out["interrupted"] = snap.get("interrupted", False)
        out["pending_interrupt"] = snap.get("pending_interrupt")
        out["next_nodes"] = snap.get("next_nodes")
        for k, v in snap.items():
            if k not in ("interrupted", "pending_interrupt", "next_nodes"):
                out.setdefault(k, _json_safe(v))
    else:
        out["interrupted"] = False
        out["pending_interrupt"] = None
    return out
