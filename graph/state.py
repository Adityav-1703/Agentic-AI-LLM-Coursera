"""Shared LangGraph state for CareerPilot workflows."""

from __future__ import annotations

import operator
from typing import Annotated, Any, Literal, TypedDict

from pydantic import BaseModel, Field


WorkflowStatus = Literal[
    "initialized",
    "planning",
    "awaiting_clarification",
    "analyzing",
    "researching",
    "awaiting_plan_confirmation",
    "planning_study",
    "interviewing",
    "evaluating",
    "reporting",
    "awaiting_answers",
    "completed",
    "error",
]

AgentName = Literal[
    "orchestrator",
    "career_analyst",
    "researcher",
    "study_planner",
    "interviewer",
    "evaluator",
    "report_agent",
    "human",
    "end",
]


class AgentMessage(BaseModel):
    agent: str
    role: str = "assistant"
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class SkillAssessment(BaseModel):
    name: str
    status: Literal["strong", "developing", "needs_improvement"] = "developing"
    priority: Literal["high", "medium", "low"] = "medium"
    subskills: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    why_gap: str | None = None


class SkillMap(BaseModel):
    target_role: str
    skills: list[str] = Field(default_factory=list)
    priority_skills: list[str] = Field(default_factory=list)
    skill_gaps: list[str] = Field(default_factory=list)
    skill_assessments: list[SkillAssessment] = Field(default_factory=list)
    needs_clarification: bool = False
    clarification_question: str | None = None
    notes: str = ""


class ResearchItem(BaseModel):
    title: str
    summary: str
    source: str
    source_type: Literal["web", "local_knowledge", "tool"] = "tool"
    url: str | None = None
    topics: list[str] = Field(default_factory=list)


class StudyDay(BaseModel):
    day: int
    week: int = 1
    focus: str
    topic: str = ""
    subtopics: list[str] = Field(default_factory=list)
    theory_hours: float = 0
    coding_hours: float = 0
    revision_hours: float = 0
    mock_interview_hours: float = 0
    tasks: list[str] = Field(default_factory=list)
    completed: bool = False


class StudyWeek(BaseModel):
    week: int
    theme: str
    focus_skills: list[str] = Field(default_factory=list)
    days: list[int] = Field(default_factory=list)


class StudyPlan(BaseModel):
    total_days: int
    hours_per_day: float
    days: list[StudyDay] = Field(default_factory=list)
    weeks: list[StudyWeek] = Field(default_factory=list)
    balance_notes: str = ""
    confirmed: bool = False


class InterviewQuestion(BaseModel):
    id: str
    category: Literal["technical", "behavioral", "coding"]
    difficulty: Literal["beginner", "intermediate", "advanced"]
    prompt: str
    expected_signals: list[str] = Field(default_factory=list)


class EvaluationResult(BaseModel):
    question_id: str
    score: float = Field(ge=0, le=10)
    criteria: dict[str, float] = Field(default_factory=dict)
    criteria_scores: dict[str, float] = Field(default_factory=dict)
    criteria_weights: dict[str, float] = Field(default_factory=dict)
    criteria_labels: dict[str, str] = Field(default_factory=dict)
    matched_signals: list[str] = Field(default_factory=list)
    missing_signals: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    feedback: str = ""
    study_next: list[str] = Field(default_factory=list)
    recommended_topics: list[str] = Field(default_factory=list)
    mapped_skill_gaps: list[str] = Field(default_factory=list)
    major_weaknesses: bool = False
    question_prompt: str | None = None
    category: str | None = None
    user_answer: str | None = None


class FinalReport(BaseModel):
    target_role: str
    skill_gaps: list[str] = Field(default_factory=list)
    recommended_resources: list[dict[str, Any]] = Field(default_factory=list)
    study_plan_summary: str = ""
    interview_summary: str = ""
    progress_summary: str = ""
    next_steps: list[str] = Field(default_factory=list)
    full_markdown: str = ""
    structured: dict[str, Any] = Field(default_factory=dict)


def _merge_messages(
    left: list[dict[str, Any]] | None,
    right: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    return (left or []) + (right or [])


class CareerState(TypedDict, total=False):
    """LangGraph shared state. Lists use reducers so nodes can append safely."""

    session_id: str
    user_goal: str
    target_role: str
    experience_level: str
    available_days: int
    hours_per_day: float

    skills: list[str]
    priority_skills: list[str]
    skill_gaps: list[str]
    skill_assessments: list[dict[str, Any]]
    needs_clarification: bool
    clarification_question: str | None

    research_results: list[dict[str, Any]]
    research_sufficient: bool

    study_plan: dict[str, Any] | None
    plan_confirmed: bool
    plan_modifications: str | None

    interview_questions: list[dict[str, Any]]
    user_answers: list[dict[str, Any]]
    evaluation_results: list[dict[str, Any]]
    major_weaknesses: bool
    replanning_count: int

    final_report: dict[str, Any] | None
    ready_for_report: bool

    agent_messages: Annotated[list[dict[str, Any]], _merge_messages]
    activity_log: Annotated[list[dict[str, Any]], operator.add]
    current_agent: str
    next_agent: str
    workflow_status: WorkflowStatus
    error: str | None
    memory: dict[str, Any]
