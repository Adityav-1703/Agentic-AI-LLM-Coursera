"""Progress tracking and structured report assembly tools."""

from __future__ import annotations

from langchain_core.tools import tool


@tool
def track_progress(
    total_questions: int,
    answered_questions: int,
    evaluations: list[dict] | None = None,
    study_days_total: int = 0,
    study_days_completed: int = 0,
    research_count: int = 0,
    skill_assessed: int = 0,
    skill_total: int = 0,
) -> dict:
    """
    Compute preparation progress metrics from session data only.

    Args:
        total_questions: Interview questions generated.
        answered_questions: Answers submitted by the user.
        evaluations: Prior evaluation result dicts.
        study_days_total: Days in the study plan.
        study_days_completed: Days the user marked complete (if tracked).
        research_count: Research items collected.
        skill_assessed: Skills with non-pending status.
        skill_total: Total skills in assessment.
    """
    evaluations = evaluations or []
    scores = [float(e.get("score", 0)) for e in evaluations if "score" in e]
    avg_score = round(sum(scores) / len(scores), 2) if scores else None
    weak = []
    for e in evaluations:
        weak.extend(e.get("mapped_skill_gaps") or [])
        weak.extend(e.get("recommended_topics") or e.get("study_next") or [])

    interview_pct = (
        round(100 * answered_questions / total_questions, 1) if total_questions else 0.0
    )
    study_pct = (
        round(100 * study_days_completed / study_days_total, 1)
        if study_days_total
        else 0.0
    )
    research_pct = 100.0 if research_count > 0 else 0.0
    skill_pct = (
        round(100 * skill_assessed / skill_total, 1) if skill_total else 0.0
    )
    overall = round(
        (interview_pct * 0.35)
        + (study_pct * 0.25)
        + (research_pct * 0.15)
        + (skill_pct * 0.25),
        1,
    )

    return {
        "tool": "track_progress",
        "overall_pct": overall,
        "interview_completion_pct": interview_pct,
        "study_completion_pct": study_pct,
        "research_completion_pct": research_pct,
        "skill_coverage_pct": skill_pct,
        "skill_coverage": {"assessed": skill_assessed, "total": skill_total},
        "average_score": avg_score,
        "answered_questions": answered_questions,
        "total_questions": total_questions,
        "recurring_focus_areas": list(dict.fromkeys(weak))[:8],
        "notes": "Metrics derived only from provided session data.",
    }


@tool
def generate_final_report(
    target_role: str,
    skill_gaps: list[str],
    research_results: list[dict],
    study_plan: dict | None,
    interview_questions: list[dict],
    evaluation_results: list[dict],
    progress: dict | None = None,
    available_days: int = 30,
    hours_per_day: float = 2.0,
) -> dict:
    """
    Assemble a final career preparation report from agent outputs.
    """
    resources = []
    for item in research_results or []:
        resources.append(
            {
                "title": item.get("title"),
                "url": item.get("url"),
                "source": item.get("source"),
                "source_type": item.get("source_type"),
                "label": item.get("label"),
            }
        )

    plan = study_plan or {}
    days = plan.get("days") or []
    weeks = plan.get("weeks") or []
    plan_summary = (
        f"{plan.get('total_days', len(days))} day plan @ "
        f"{plan.get('hours_per_day', hours_per_day)} h/day covering "
        f"{', '.join(skill_gaps[:5]) or 'core skills'}."
    )

    avg = None
    by_cat: dict[str, list[float]] = {"technical": [], "behavioral": [], "coding": []}
    if evaluation_results:
        scores = [float(e.get("score", 0)) for e in evaluation_results]
        avg = round(sum(scores) / len(scores), 2)
        for e in evaluation_results:
            cat = (e.get("category") or "technical").lower()
            if cat in by_cat:
                by_cat[cat].append(float(e.get("score", 0)))

    cat_scores = {
        k: (round(sum(v) / len(v), 2) if v else None) for k, v in by_cat.items()
    }

    interview_summary = (
        f"{len(interview_questions)} questions generated; "
        f"{len(evaluation_results)} evaluated"
        + (f"; average score {avg}/10" if avg is not None else "")
        + "."
    )

    progress = progress or {}
    progress_summary = (
        f"Overall {progress.get('overall_pct', 0)}%; "
        f"interview {progress.get('interview_completion_pct', 0)}%; "
        f"study {progress.get('study_completion_pct', 0)}%."
    )

    week_summaries = []
    for w in weeks:
        week_summaries.append(
            {
                "week": w.get("week"),
                "theme": w.get("theme"),
                "focus_skills": w.get("focus_skills") or [],
            }
        )
    if not week_summaries and days:
        # Derive crude weeks if older plans lack weeks
        for i in range(0, len(days), 7):
            chunk = days[i : i + 7]
            focuses = list(dict.fromkeys(d.get("focus") for d in chunk if d.get("focus")))
            week_summaries.append(
                {
                    "week": (i // 7) + 1,
                    "theme": " · ".join(focuses[:3]) or f"Week {(i // 7) + 1}",
                    "focus_skills": focuses,
                }
            )

    next_steps = [
        "Complete today's study session from your plan.",
        "Retry your weakest interview question.",
        "Complete one coding practice problem.",
        "Take another short mock interview block.",
    ]
    if skill_gaps:
        next_steps.insert(0, f"Focus next block on: {', '.join(skill_gaps[:3])}.")

    structured = {
        "title": "CareerPilot Assessment",
        "target_role": target_role,
        "preparation_days": plan.get("total_days") or available_days,
        "hours_per_day": plan.get("hours_per_day") or hours_per_day,
        "current_readiness": {
            "interview_readiness": avg,
            "by_category": cat_scores,
        },
        "top_skill_gaps": skill_gaps[:5],
        "personalized_plan": week_summaries,
        "recommended_resources": resources,
        "next_steps": next_steps,
        "progress": progress,
    }

    gap_lines = [f"- {g}" for g in skill_gaps] if skill_gaps else ["- None recorded"]
    md_lines = [
        f"# CareerPilot Assessment — {target_role}",
        "",
        f"Preparation: {structured['preparation_days']} days · "
        f"{structured['hours_per_day']} h/day",
        "",
        "## Current readiness",
        f"Interview readiness: {avg if avg is not None else 'N/A'} / 10",
        "",
        "## Top skill gaps",
        *gap_lines,
        "",
        "## Personalized plan",
    ]
    for w in week_summaries:
        md_lines.append(f"- Week {w.get('week')}: {w.get('theme')}")
    md_lines += ["", "## Recommended resources"]
    for r in resources[:8]:
        url = f" ({r['url']})" if r.get("url") else ""
        label = ""
        if r.get("source_type") == "local_knowledge" or (
            r.get("label") and "LOCAL" in str(r.get("label"))
        ):
            label = " [Local fallback]"
        md_lines.append(f"- {r.get('title')} — {r.get('source')}{url}{label}")
    if not resources:
        md_lines.append("- No research items recorded")
    md_lines += ["", "## Next steps", *[f"- {s}" for s in next_steps]]

    return {
        "tool": "generate_final_report",
        "target_role": target_role,
        "skill_gaps": skill_gaps,
        "recommended_resources": resources,
        "study_plan_summary": plan_summary,
        "interview_summary": interview_summary,
        "progress_summary": progress_summary,
        "next_steps": next_steps,
        "full_markdown": "\n".join(md_lines),
        "structured": structured,
    }
