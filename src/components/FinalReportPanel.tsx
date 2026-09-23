type Props = {
  report?: Record<string, unknown> | null;
  onGenerate: () => Promise<void>;
  canGenerate: boolean;
  busy: boolean;
};

export function FinalReportPanel({
  report,
  onGenerate,
  canGenerate,
  busy,
}: Props) {
  const structured = (report?.structured || null) as Record<string, unknown> | null;
  const readiness = (structured?.current_readiness || {}) as {
    interview_readiness?: number | null;
  };
  const weeks = (structured?.personalized_plan || []) as Array<{
    week?: number;
    theme?: string;
  }>;
  const resources = (structured?.recommended_resources ||
    report?.recommended_resources ||
    []) as Array<Record<string, unknown>>;
  const gaps = (structured?.top_skill_gaps ||
    report?.skill_gaps ||
    []) as string[];
  const nextSteps = (structured?.next_steps ||
    report?.next_steps ||
    []) as string[];

  function exportMarkdown() {
    const md =
      typeof report?.full_markdown === "string" ? report.full_markdown : "";
    if (!md) return;
    const blob = new Blob([md], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "careerpilot-assessment.md";
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="panel rounded-2xl p-5 animate-fade-up">
      <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
        <h2 className="font-display text-xl text-[var(--color-moss)]">
          CareerPilot Assessment
        </h2>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            disabled={busy || !canGenerate}
            onClick={() => void onGenerate()}
            className="btn-primary text-sm py-1.5"
          >
            Generate final report
          </button>
          {report && (
            <button
              type="button"
              onClick={exportMarkdown}
              className="btn-secondary text-sm py-1.5"
            >
              Export Markdown
            </button>
          )}
        </div>
      </div>

      {!report ? (
        <p className="text-sm text-[var(--color-slate)]">
          The structured assessment consolidates skill gaps, resources, plan, and
          evaluations when you request it.
        </p>
      ) : (
        <div className="space-y-4 text-sm">
          <div className="grid sm:grid-cols-3 gap-3">
            <div className="rounded-xl bg-white/70 p-3">
              <div className="text-xs text-[var(--color-slate)]">Target role</div>
              <div className="font-medium">
                {String(structured?.target_role || report.target_role || "—")}
              </div>
            </div>
            <div className="rounded-xl bg-white/70 p-3">
              <div className="text-xs text-[var(--color-slate)]">Preparation time</div>
              <div className="font-medium">
                {String(structured?.preparation_days || "—")} days
              </div>
            </div>
            <div className="rounded-xl bg-white/70 p-3">
              <div className="text-xs text-[var(--color-slate)]">Daily commitment</div>
              <div className="font-medium">
                {String(structured?.hours_per_day || "—")} hours
              </div>
            </div>
          </div>

          <div className="rounded-xl bg-white/70 p-3">
            <div className="text-xs uppercase tracking-wider text-[var(--color-slate)] mb-1">
              Current readiness
            </div>
            <div className="text-lg font-display text-[var(--color-moss)]">
              Interview readiness:{" "}
              {readiness.interview_readiness != null
                ? `${readiness.interview_readiness} / 10`
                : "N/A"}
            </div>
          </div>

          <div>
            <div className="text-xs uppercase tracking-wider text-[var(--color-slate)] mb-1">
              Top skill gaps
            </div>
            <ol className="list-decimal pl-5 space-y-0.5">
              {gaps.map((g) => (
                <li key={g}>{g}</li>
              ))}
              {!gaps.length && <li>None recorded</li>}
            </ol>
          </div>

          <div>
            <div className="text-xs uppercase tracking-wider text-[var(--color-slate)] mb-1">
              Personalized plan
            </div>
            <ul className="space-y-1">
              {weeks.map((w) => (
                <li key={String(w.week)}>
                  Week {w.week}: {w.theme}
                </li>
              ))}
              {!weeks.length && (
                <li className="text-[var(--color-slate)]">
                  {String(report.study_plan_summary || "Plan summary unavailable")}
                </li>
              )}
            </ul>
          </div>

          <div>
            <div className="text-xs uppercase tracking-wider text-[var(--color-slate)] mb-1">
              Recommended resources
            </div>
            <ul className="space-y-2">
              {resources.map((r, i) => {
                const local =
                  r.source_type === "local_knowledge" ||
                  String(r.label || "").includes("LOCAL");
                return (
                  <li key={i} className="rounded-lg bg-white/70 px-3 py-2">
                    <div className="font-medium">{String(r.title || "Untitled")}</div>
                    <div className="text-xs text-[var(--color-slate)]">
                      {String(r.source || "")}
                      {local ? " · Local fallback" : ""}
                      {r.url ? (
                        <>
                          {" · "}
                          <a
                            className="text-[var(--color-leaf)] underline"
                            href={String(r.url)}
                            target="_blank"
                            rel="noreferrer"
                          >
                            Open
                          </a>
                        </>
                      ) : null}
                    </div>
                  </li>
                );
              })}
              {!resources.length && (
                <li className="text-[var(--color-slate)]">No research items recorded</li>
              )}
            </ul>
          </div>

          <div>
            <div className="text-xs uppercase tracking-wider text-[var(--color-slate)] mb-1">
              Next steps
            </div>
            <ol className="list-decimal pl-5 space-y-0.5">
              {nextSteps.map((s) => (
                <li key={s}>{s}</li>
              ))}
            </ol>
          </div>
        </div>
      )}
    </div>
  );
}
