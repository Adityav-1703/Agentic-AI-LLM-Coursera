import { useState } from "react";
import type { SkillAssessment } from "../types/career";

const STATUS_LABEL: Record<string, string> = {
  strong: "Strong",
  developing: "Developing",
  needs_improvement: "Needs Improvement",
};

type Props = { assessments: SkillAssessment[]; gaps: string[] };

export function SkillGapPanel({ assessments, gaps }: Props) {
  const [openWhy, setOpenWhy] = useState<string | null>(null);
  const list =
    assessments.length > 0
      ? assessments
      : gaps.map((g) => ({
          name: g,
          status: "developing" as const,
          priority: "medium" as const,
          subskills: [],
          evidence: [],
          why_gap: null,
        }));

  return (
    <div className="panel rounded-2xl p-5 animate-fade-up">
      <h2 className="font-display text-xl text-[var(--color-moss)] mb-1">
        Skill assessment
      </h2>
      <p className="text-sm text-[var(--color-slate)] mb-4">
        Skills → subskills → evidence → priority
      </p>
      {!list.length ? (
        <p className="text-sm text-[var(--color-slate)]">
          Your skill map appears after the Career Analyst runs.
        </p>
      ) : (
        <ul className="space-y-3 max-h-[28rem] overflow-auto">
          {list.map((a) => (
            <li key={a.name} className="rounded-xl bg-white/70 px-3 py-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className="font-medium">{a.name}</span>
                <div className="flex gap-2 text-[10px] uppercase tracking-wide">
                  <span className="px-2 py-0.5 rounded-md bg-[var(--color-sand)]">
                    {STATUS_LABEL[a.status] || a.status}
                  </span>
                  <span className="px-2 py-0.5 rounded-md bg-[var(--color-mint)]/50 text-[var(--color-moss)]">
                    {a.priority} priority
                  </span>
                </div>
              </div>
              {!!a.subskills?.length && (
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {a.subskills.map((s) => (
                    <span
                      key={s}
                      className="text-xs px-2 py-0.5 rounded-md bg-white border border-[var(--color-line)]"
                    >
                      {s}
                    </span>
                  ))}
                </div>
              )}
              {!!a.evidence?.length && (
                <p className="text-xs text-[var(--color-slate)] mt-2">
                  Evidence: {a.evidence.join(", ")}
                </p>
              )}
              {a.why_gap && a.status !== "strong" && (
                <button
                  type="button"
                  className="text-xs text-[var(--color-leaf)] mt-2 underline"
                  onClick={() =>
                    setOpenWhy((cur) => (cur === a.name ? null : a.name))
                  }
                >
                  Why is this a gap?
                </button>
              )}
              {openWhy === a.name && a.why_gap && (
                <p className="text-xs mt-1 text-[var(--color-ink)]/80 bg-[var(--color-sand)]/50 rounded-lg p-2">
                  {a.why_gap}
                </p>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
