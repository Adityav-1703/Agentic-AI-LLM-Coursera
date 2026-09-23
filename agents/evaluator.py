"""Evaluator agent — scores answers only against provided criteria/signals."""

from __future__ import annotations

import json
import re
from typing import Any

from app.agents.helpers import activity, llm, message, update_memory
from app.core.logging import get_logger, log_span
from app.graph.state import CareerState
from app.tools.skill_analysis import map_topic_to_skill

logger = get_logger(__name__)

CRITERIA_WEIGHTS = {
    "relevance": 0.30,
    "correctness_signals": 0.35,
    "structure": 0.20,
    "specificity": 0.15,
}

CRITERIA_LABELS = {
    "relevance": "Relevance",
    "correctness_signals": "Technical correctness",
    "structure": "Structure",
    "specificity": "Specificity",
}


def _find_question(state: CareerState, question_id: str) -> dict[str, Any] | None:
    for q in state.get("interview_questions") or []:
        if q.get("id") == question_id:
            return q
    return None


def _heuristic_score(answer: str, question: dict[str, Any]) -> dict[str, Any]:
    text = (answer or "").strip()
    raw_signals = [str(s) for s in (question.get("expected_signals") or []) if s]
    signals = [s.lower() for s in raw_signals]
    lower = text.lower()

    if not text:
        return {
            "score": 0.0,
            "criteria": {k: 0.0 for k in CRITERIA_WEIGHTS},
            "criteria_scores": {k: 0.0 for k in CRITERIA_WEIGHTS},
            "criteria_weights": dict(CRITERIA_WEIGHTS),
            "criteria_labels": dict(CRITERIA_LABELS),
            "matched_signals": [],
            "missing_signals": list(raw_signals),
            "strengths": [],
            "weaknesses": ["Empty answer"],
            "feedback": "No answer was provided. Evaluation is based only on the empty response.",
            "study_next": raw_signals[:3] or ["Review the topic fundamentals"],
            "recommended_topics": raw_signals[:3] or ["Review the topic fundamentals"],
            "major_weaknesses": True,
        }

    matched = [raw_signals[i] for i, s in enumerate(signals) if s and s in lower]
    missing = [raw_signals[i] for i, s in enumerate(signals) if s and s not in lower]
    hit = len(matched)
    signal_ratio = (hit / len(signals)) if signals else 0.0
    word_count = len(re.findall(r"\b\w+\b", text))

    relevance = 4.0 + min(6.0, word_count / 40 * 6)
    if signals and hit == 0 and word_count > 20:
        relevance = min(relevance, 5.0)

    correctness = 2.0 + signal_ratio * 8.0
    structure = 3.0
    if any(k in lower for k in ("first", "second", "because", "for example", "trade-off")):
        structure += 3.0
    if word_count > 80:
        structure += 2.0
    structure = min(10.0, structure)

    specificity = 3.0
    if re.search(r"\b\d+\b", text) or "example" in lower:
        specificity += 3.0
    if word_count > 60:
        specificity += 2.0
    specificity = min(10.0, specificity)

    criteria = {
        "relevance": round(min(10.0, relevance), 2),
        "correctness_signals": round(min(10.0, correctness), 2),
        "structure": round(structure, 2),
        "specificity": round(specificity, 2),
    }
    score = round(sum(criteria[k] * w for k, w in CRITERIA_WEIGHTS.items()), 2)

    strengths = []
    weaknesses = []
    if signal_ratio >= 0.5:
        strengths.append("Answer mentions several expected topic signals.")
    else:
        weaknesses.append("Few expected topic signals detected in the answer text.")
    if structure >= 7:
        strengths.append("Response shows some structure / reasoning markers.")
    else:
        weaknesses.append("Could be structured more clearly (e.g., steps, trade-offs).")
    if specificity < 6:
        weaknesses.append("Add concrete examples or specifics.")

    study_next = list(missing[:5])
    if not study_next and question.get("category"):
        study_next = [f"{question.get('category')} fundamentals"]

    return {
        "score": score,
        "criteria": criteria,
        "criteria_scores": dict(criteria),
        "criteria_weights": dict(CRITERIA_WEIGHTS),
        "criteria_labels": dict(CRITERIA_LABELS),
        "matched_signals": matched,
        "missing_signals": missing,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "feedback": (
            "Scored only from the provided answer against transparent criteria "
            f"(weights={CRITERIA_WEIGHTS}). Matched {hit}/{len(signals) or 0} expected signals."
        ),
        "study_next": study_next,
        "recommended_topics": study_next,
        "major_weaknesses": score < 5.0,
    }


def evaluator_node(state: CareerState) -> dict[str, Any]:
    with log_span(logger, "evaluator_node", session_id=state.get("session_id")):
        answers = list(state.get("user_answers") or [])
        existing = list(state.get("evaluation_results") or [])
        evaluated_ids = {e.get("question_id") for e in existing}

        pending = [a for a in answers if a.get("question_id") not in evaluated_ids]
        if not pending:
            return {
                "current_agent": "evaluator",
                "agent_messages": [
                    message("evaluator", "No new answers to evaluate.")
                ],
                "activity_log": [
                    activity(
                        "evaluator",
                        "skip",
                        "No pending answers",
                        user_summary="No new answers were ready to score.",
                    )
                ],
            }

        new_evals: list[dict] = []
        major = False
        role = state.get("target_role") or ""

        for ans in pending:
            qid = ans.get("question_id") or ""
            question = _find_question(state, qid) or {
                "id": qid,
                "prompt": ans.get("question_prompt") or "",
                "expected_signals": [],
                "category": "technical",
            }
            base = _heuristic_score(ans.get("answer") or "", question)
            base["question_id"] = qid
            base["question_prompt"] = question.get("prompt")
            base["category"] = question.get("category")
            base["user_answer"] = ans.get("answer") or ""

            try:
                client = llm()
                refined = client.complete_json(
                    system=(
                        "You evaluate interview answers. Use ONLY the answer text and "
                        "expected_signals/criteria provided. Do not invent user history. "
                        "Return JSON with score, criteria, strengths, weaknesses, feedback, "
                        "study_next, major_weaknesses. Keep study_next as short topic labels."
                    ),
                    user=(
                        f"Question: {question.get('prompt')}\n"
                        f"Expected signals: {question.get('expected_signals')}\n"
                        f"Answer: {ans.get('answer')}\n"
                        f"Heuristic draft: {json.dumps(base)}\n"
                        f"OFFLINE_HINT_JSON: {json.dumps(base)}"
                    ),
                )
                for key in (
                    "score",
                    "criteria",
                    "strengths",
                    "weaknesses",
                    "feedback",
                    "study_next",
                    "major_weaknesses",
                ):
                    if key in refined:
                        base[key] = refined[key]
                base["score"] = float(max(0.0, min(10.0, float(base["score"]))))
                if isinstance(base.get("criteria"), dict):
                    base["criteria_scores"] = dict(base["criteria"])
                if isinstance(base.get("study_next"), list):
                    base["recommended_topics"] = list(base["study_next"])
                base["question_id"] = qid
            except Exception as exc:  # noqa: BLE001
                logger.warning("Evaluator LLM refine skipped: %s", exc)

            # Map missing signals to catalog skills for planner feedback
            mapped_skills = []
            for topic in base.get("study_next") or []:
                mapped = map_topic_to_skill(str(topic), role)
                if mapped:
                    mapped_skills.append(mapped)
            base["mapped_skill_gaps"] = list(dict.fromkeys(mapped_skills))

            if base.get("major_weaknesses") or base["score"] < 5.0:
                major = True
            new_evals.append(base)

        all_evals = existing + new_evals
        weak_labels = []
        for e in all_evals:
            weak_labels.extend(e.get("mapped_skill_gaps") or [])
            for t in e.get("study_next") or []:
                if len(str(t)) <= 40 and not str(t).endswith("."):
                    weak_labels.append(str(t))

        mem = update_memory(
            state,
            previous_evaluation_results=all_evals[-10:],
            last_scores=[e.get("score") for e in new_evals],
            identified_weaknesses=list(dict.fromkeys(weak_labels))[:12],
        )

        # Refresh hierarchical assessments with interview evidence
        skill_assessments = state.get("skill_assessments") or []
        try:
            from app.tools.skill_analysis import build_skill_assessments

            rebuilt = build_skill_assessments(
                target_role=role or "Software Engineer",
                experience_level=state.get("experience_level") or "intermediate",
                known_skills=list((state.get("memory") or {}).get("known_skills") or []),
                evidence_topics=list(dict.fromkeys(weak_labels)),
            )
            skill_assessments = rebuilt.get("skill_assessments") or skill_assessments
            skill_gaps = rebuilt.get("skill_gaps") or state.get("skill_gaps")
        except Exception as exc:  # noqa: BLE001
            logger.warning("Skill assessment refresh skipped: %s", exc)
            skill_gaps = state.get("skill_gaps")

        avg = round(
            sum(float(e.get("score", 0)) for e in new_evals) / max(1, len(new_evals)),
            2,
        )
        summary = (
            f"Evaluated {len(new_evals)} answer(s). "
            f"Major weaknesses={'yes' if major else 'no'}."
        )
        user_summary = (
            f"Scored {len(new_evals)} answer(s) (avg {avg}/10)"
            + (
                f" and flagged {', '.join(list(dict.fromkeys(weak_labels))[:3])}."
                if weak_labels
                else "."
            )
        )

        return {
            "current_agent": "evaluator",
            "evaluation_results": all_evals,
            "major_weaknesses": major,
            "skill_assessments": skill_assessments,
            "skill_gaps": skill_gaps,
            "workflow_status": "evaluating",
            "memory": mem,
            "agent_messages": [message("evaluator", summary)],
            "activity_log": [
                activity(
                    "evaluator",
                    "evaluate",
                    summary,
                    count=len(new_evals),
                    user_summary=user_summary,
                )
            ],
        }
