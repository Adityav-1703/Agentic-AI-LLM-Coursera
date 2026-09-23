"""FastAPI routers for CareerPilot."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.core.config import get_settings
from app.models.schemas import (
    CareerAnalyzeRequest,
    CareerStartRequest,
    HealthResponse,
    HumanDecisionRequest,
    InterviewAnswerRequest,
    InterviewEvaluateRequest,
    InterviewStartRequest,
    SessionStateResponse,
)
from app.services.career_service import career_service

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        llm_provider=settings.llm_provider,
        llm_ready=settings.has_llm_credentials() or settings.llm_provider == "offline",
        web_research_enabled=settings.enable_web_research,
    )


@router.post("/career/analyze")
def analyze_career(body: CareerAnalyzeRequest):
    try:
        return career_service.analyze(
            user_goal=body.user_goal,
            target_role=body.target_role,
            experience_level=body.experience_level,
            known_skills=body.known_skills,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/career/start", response_model=SessionStateResponse)
def start_career(body: CareerStartRequest) -> SessionStateResponse:
    try:
        data = career_service.start(
            user_goal=body.user_goal,
            target_role=body.target_role,
            experience_level=body.experience_level,
            available_days=body.available_days,
            hours_per_day=body.hours_per_day,
        )
        return SessionStateResponse(**data)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/career/status/{session_id}", response_model=SessionStateResponse)
def career_status(session_id: str) -> SessionStateResponse:
    try:
        data = career_service.status(session_id)
        return SessionStateResponse(**data)
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found") from None
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/career/decide/{session_id}", response_model=SessionStateResponse)
def career_decide(session_id: str, body: HumanDecisionRequest) -> SessionStateResponse:
    try:
        data = career_service.decide(
            session_id,
            {
                "action": body.action,
                "modifications": body.modifications,
                "target_role": body.target_role,
                "user_goal": body.user_goal,
            },
        )
        return SessionStateResponse(**data)
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found") from None
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/study-plan/{session_id}")
def get_study_plan(session_id: str):
    try:
        return career_service.study_plan(session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found") from None
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/interview/start", response_model=SessionStateResponse)
def interview_start(body: InterviewStartRequest) -> SessionStateResponse:
    """Return current session with interview questions (generated during workflow)."""
    try:
        data = career_service.status(body.session_id)
        if not data.get("interview_questions"):
            raise HTTPException(
                status_code=409,
                detail="Interview questions are not ready. Approve the study plan first.",
            )
        return SessionStateResponse(**data)
    except HTTPException:
        raise
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found") from None
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/interview/answer", response_model=SessionStateResponse)
def interview_answer(body: InterviewAnswerRequest) -> SessionStateResponse:
    try:
        data = career_service.add_answer(
            body.session_id, body.question_id, body.answer
        )
        return SessionStateResponse(**data)
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found") from None
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/interview/evaluate", response_model=SessionStateResponse)
def interview_evaluate(body: InterviewEvaluateRequest) -> SessionStateResponse:
    try:
        data = career_service.evaluate(body.session_id)
        return SessionStateResponse(**data)
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found") from None
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/career/report/{session_id}", response_model=SessionStateResponse)
def generate_report(session_id: str) -> SessionStateResponse:
    try:
        data = career_service.request_report(session_id)
        return SessionStateResponse(**data)
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found") from None
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc
