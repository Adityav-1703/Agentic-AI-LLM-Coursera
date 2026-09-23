"""LLM provider abstraction — OpenAI, Anthropic, or deterministic offline mode."""

from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from typing import Any

from app.core.config import Settings, get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class LLMClient(ABC):
    """Minimal chat completion interface used by agents."""

    provider_name: str

    @abstractmethod
    def complete(
        self,
        system: str,
        user: str,
        *,
        temperature: float = 0.2,
        json_mode: bool = False,
    ) -> str:
        raise NotImplementedError

    def complete_json(
        self,
        system: str,
        user: str,
        *,
        temperature: float = 0.2,
    ) -> dict[str, Any]:
        raw = self.complete(system, user, temperature=temperature, json_mode=True)
        return parse_json_response(raw)


class OfflineLLM(LLMClient):
    """
    Deterministic offline fallback.

    Does NOT pretend to call a remote model. Agents still call real tools;
    this client only synthesizes structured JSON from prompts when no API key
    is configured, so local demos remain runnable.
    """

    provider_name = "offline"

    def complete(
        self,
        system: str,
        user: str,
        *,
        temperature: float = 0.2,
        json_mode: bool = False,
    ) -> str:
        logger.warning(
            "OfflineLLM used — set LLM_PROVIDER and API key for live model responses"
        )
        # Prefer extracting an explicit JSON instruction block if present.
        blob = _extract_offline_hint(user) or _heuristic_payload(system, user)
        if json_mode or isinstance(blob, dict):
            return json.dumps(blob)
        return str(blob)

    def complete_json(
        self,
        system: str,
        user: str,
        *,
        temperature: float = 0.2,
    ) -> dict[str, Any]:
        raw = self.complete(system, user, temperature=temperature, json_mode=True)
        data = parse_json_response(raw)
        data.setdefault("_mode", "offline")
        return data


class OpenAILLM(LLMClient):
    provider_name = "openai"

    def __init__(self, api_key: str, model: str) -> None:
        from openai import OpenAI

        self._client = OpenAI(api_key=api_key)
        self._model = model

    def complete(
        self,
        system: str,
        user: str,
        *,
        temperature: float = 0.2,
        json_mode: bool = False,
    ) -> str:
        kwargs: dict[str, Any] = {
            "model": self._model,
            "temperature": temperature,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        resp = self._client.chat.completions.create(**kwargs)
        return resp.choices[0].message.content or ""


class AnthropicLLM(LLMClient):
    provider_name = "anthropic"

    def __init__(self, api_key: str, model: str) -> None:
        import anthropic

        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model

    def complete(
        self,
        system: str,
        user: str,
        *,
        temperature: float = 0.2,
        json_mode: bool = False,
    ) -> str:
        prompt = user
        if json_mode:
            prompt = (
                user
                + "\n\nRespond with a single valid JSON object only. No markdown."
            )
        resp = self._client.messages.create(
            model=self._model,
            max_tokens=4096,
            temperature=temperature,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        parts = [b.text for b in resp.content if hasattr(b, "text")]
        return "".join(parts)


def get_llm(settings: Settings | None = None) -> LLMClient:
    settings = settings or get_settings()
    provider = settings.llm_provider

    if provider == "openai":
        if not settings.openai_api_key.strip():
            logger.warning("OPENAI_API_KEY missing — falling back to OfflineLLM")
            return OfflineLLM()
        return OpenAILLM(settings.openai_api_key, settings.openai_model)

    if provider == "anthropic":
        if not settings.anthropic_api_key.strip():
            logger.warning("ANTHROPIC_API_KEY missing — falling back to OfflineLLM")
            return OfflineLLM()
        return AnthropicLLM(settings.anthropic_api_key, settings.anthropic_model)

    return OfflineLLM()


def parse_json_response(raw: str) -> dict[str, Any]:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
        return {"value": data}
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            return json.loads(match.group(0))
        raise ValueError(f"Model did not return valid JSON: {raw[:200]}") from None


def _extract_offline_hint(user: str) -> dict[str, Any] | None:
    marker = "OFFLINE_HINT_JSON:"
    if marker not in user:
        return None
    chunk = user.split(marker, 1)[1].strip()
    try:
        data = json.loads(chunk)
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        return None


def _heuristic_payload(system: str, user: str) -> dict[str, Any]:
    combined = f"{system}\n{user}".lower()
    if "skill" in combined and "map" in combined:
        return {
            "target_role": "Software Engineer",
            "skills": ["Problem Solving", "Communication", "Domain Fundamentals"],
            "priority_skills": ["Problem Solving"],
            "skill_gaps": ["System Design"],
            "needs_clarification": False,
            "clarification_question": None,
            "notes": "Offline heuristic skill map — configure an API key for richer analysis.",
        }
    if "research" in combined:
        return {
            "topics": ["Core concepts", "Interview patterns"],
            "resources": [],
            "notes": "Offline mode: use research tools for concrete sources.",
        }
    if "study plan" in combined or "schedule" in combined:
        return {
            "days": [],
            "notes": "Offline mode expects study-plan tool output.",
        }
    if "interview" in combined and "question" in combined:
        return {
            "technical": [],
            "behavioral": [],
            "coding": [],
            "notes": "Offline mode expects interview-question tool output.",
        }
    if "evaluat" in combined:
        return {
            "score": 0,
            "criteria": {},
            "strengths": [],
            "weaknesses": [],
            "feedback": "No answer provided.",
            "study_next": [],
            "major_weaknesses": False,
        }
    if "report" in combined:
        return {
            "summary": "Offline report placeholder.",
            "next_steps": ["Configure LLM_PROVIDER and API key for richer reports."],
        }
    if "orchestr" in combined or "route" in combined:
        return {
            "next_agent": "career_analyst",
            "reason": "Default offline routing to career analyst.",
            "workflow_complete": False,
        }
    return {"message": "offline_fallback", "echo": user[:240]}
