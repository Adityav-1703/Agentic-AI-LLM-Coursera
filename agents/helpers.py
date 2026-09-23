"""Shared helpers for agent nodes."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.graph.state import CareerState
from app.llm.provider import LLMClient, get_llm


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def activity(
    agent: str,
    action: str,
    detail: str = "",
    **extra: Any,
) -> dict[str, Any]:
    return {
        "timestamp": utc_now(),
        "agent": agent,
        "action": action,
        "detail": detail,
        **extra,
    }


def message(agent: str, content: str, **metadata: Any) -> dict[str, Any]:
    return {
        "agent": agent,
        "role": "assistant",
        "content": content,
        "metadata": metadata,
        "timestamp": utc_now(),
    }


def update_memory(state: CareerState, **fields: Any) -> dict[str, Any]:
    mem = dict(state.get("memory") or {})
    mem.update(fields)
    mem["updated_at"] = utc_now()
    return mem


def llm() -> LLMClient:
    return get_llm()
