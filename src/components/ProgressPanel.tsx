import type { ProgressDashboard } from "../types/career";

type Props = {
  progress?: ProgressDashboard;
  onContinue: () => void;
  onInterview: () => void;
  onSkills: () => void;
};

function Bar({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <div className="flex justify-between text-xs mb-1">
        <span className="text-[var(--color-slate)]">{label}</span>
        <span className="font-medium">{value}%</span>
      </div>
      <div className="progress-track">
        <div className="progress-fill" style={{ width: `${Math.min(100, value)}%` }} />
      </div>
    </div>
  );
}

export function ProgressPanel({
  progress,
  onContinue,
  onInterview,
  onSkills,
}: Props) {
  const p = progress || {
    overall_pct: 0,
    interview_completion_pct: 0,
    study_completion_pct: 0,
    research_completion_pct: 0,
    skill_coverage: { assessed: 0, total: 0, pct: 0 },
    current_focus: "Start preparation to unlock focus.",
    next_action: "Build your preparation plan.",
  };

  return (
    <div className="panel rounded-2xl p-5 animate-fade-up">
      <h2 className="font-display text-xl text-[var(--color-moss)] mb-4">
        Progress
      </h2>
      <div className="mb-4">
        <div className="text-3xl font-display text-[var(--color-moss)]">
          {p.overall_pct}%
        </div>
        <div className="text-xs uppercase tracking-wider text-[var(--color-slate)]">
          Overall preparation
        </div>
        <div className="progress-track mt-2">
          <div
            className="progress-fill"
            style={{ width: `${Math.min(100, p.overall_pct)}%` }}
          />
        </div>
      </div>
      <div className="space-y-3 mb-4">
        <Bar label="Interview completion" value={p.interview_completion_pct} />
        <Bar label="Study completion" value={p.study_completion_pct} />
        <Bar label="Research" value={p.research_completion_pct} />
        <Bar
          label={`Skill coverage (${p.skill_coverage.assessed}/${p.skill_coverage.total || "—"})`}
          value={p.skill_coverage.pct}
        />
      </div>
      <div className="rounded-xl bg-white/70 p-3 mb-3">
        <div className="text-xs uppercase tracking-wider text-[var(--color-slate)]">
          Current focus
        </div>
        <p className="text-sm mt-1">{p.current_focus}</p>
      </div>
      <div className="rounded-xl bg-[var(--color-sand)]/60 p-3 mb-4">
        <div className="text-xs uppercase tracking-wider text-[var(--color-slate)]">
          Next action
        </div>
        <p className="text-sm mt-1 font-medium">{p.next_action}</p>
      </div>
      <div className="flex flex-wrap gap-2">
        <button type="button" className="btn-primary text-sm py-1.5" onClick={onContinue}>
          Continue Preparation
        </button>
        <button type="button" className="btn-secondary text-sm py-1.5" onClick={onInterview}>
          Practice Interview
        </button>
        <button type="button" className="btn-secondary text-sm py-1.5" onClick={onSkills}>
          Review Skill Gaps
        </button>
      </div>
    </div>
  );
}
