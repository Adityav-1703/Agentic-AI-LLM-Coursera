"""Pydantic request/response models for the CareerPilot API."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class CareerStartRequest(BaseModel):
    user_goal: str = Field(..., min_length=8, max_length=500)
    target_role: str = Field(..., min_length=2, max_length=120)
    experience_level: Literal["beginner", "intermediate", "advanced"] = "intermediate"
    available_days: int = Field(30, ge=1, le=180)
    hours_per_day: float = Field(2.0, gt=0, le=16)

    @field_validator("user_goal", "target_role")
    @classmethod
    def strip_text(cls, v: str) -> str:
        return v.strip()


class CareerAnalyzeRequest(BaseModel):
    user_goal: str = Field(..., min_length=8, max_length=500)
    target_role: str = Field(..., min_length=2, max_length=120)
    experience_level: Literal["beginner", "intermediate", "advanced"] = "intermediate"
    known_skills: list[str] = Field(default_factory=list)


class HumanDecisionRequest(BaseModel):
    action: Literal["approve", "modify", "restart", "clarify"]
    modifications: str | None = None
    target_role: str | None = None
    user_goal: str | None = None


class InterviewStartRequest(BaseModel):
    session_id: str


class InterviewAnswerRequest(BaseModel):
    session_id: str
    question_id: str
    answer: str = Field(..., min_length=1, max_length=8000)


class InterviewEvaluateRequest(BaseModel):
    session_id: str


class SessionStateResponse(BaseModel):
    session_id: str
    workflow_status: str
    current_agent: str | None = None
    next_agent: str | None = None
    interrupted: bool = False
    pending_interrupt: dict[str, Any] | None = None
    target_role: str | None = None
    user_goal: str | None = None
    experience_level: str | None = None
    available_days: int | None = None
    hours_per_day: float | None = None
    skills: list[str] = Field(default_factory=list)
    priority_skills: list[str] = Field(default_factory=list)
    skill_gaps: list[str] = Field(default_factory=list)
    skill_assessments: list[dict[str, Any]] = Field(default_factory=list)
    research_results: list[dict[str, Any]] = Field(default_factory=list)
    study_plan: dict[str, Any] | None = None
    plan_confirmed: bool = False
    interview_questions: list[dict[str, Any]] = Field(default_factory=list)
    user_answers: list[dict[str, Any]] = Field(default_factory=list)
    evaluation_results: list[dict[str, Any]] = Field(default_factory=list)
    interview_performance: dict[str, Any] = Field(default_factory=dict)
    progress: dict[str, Any] = Field(default_factory=dict)
    agent_statuses: list[dict[str, Any]] = Field(default_factory=list)
    final_report: dict[str, Any] | None = None
    agent_messages: list[dict[str, Any]] = Field(default_factory=list)
    activity_log: list[dict[str, Any]] = Field(default_factory=list)
    memory: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    completed_agents: list[str] = Field(default_factory=list)
    llm_provider: str | None = None
    architecture: dict[str, Any] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    status: str
    llm_provider: str
    llm_ready: bool
    web_research_enabled: bool


class ErrorResponse(BaseModel):
    detail: str
