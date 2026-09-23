import type { StudyPlan } from "../types/career";

type Props = { plan?: StudyPlan | null; confirmed: boolean };

export function StudyPlanPanel({ plan, confirmed }: Props) {
  if (!plan) {
    return (
      <div className="panel rounded-2xl p-5">
        <h2 className="font-display text-xl text-[var(--color-moss)] mb-2">
          Study plan
        </h2>
        <p className="text-sm text-[var(--color-slate)]">
          Your week-by-week plan appears after research completes.
        </p>
      </div>
    );
  }

  const weeks =
    plan.weeks && plan.weeks.length
      ? plan.weeks
      : Array.from(
          new Set(plan.days.map((d) => d.week || Math.ceil(d.day / 7))),
        ).map((w) => ({
          week: w,
          theme: `Week ${w}`,
          focus_skills: [],
          days: plan.days
            .filter((d) => (d.week || Math.ceil(d.day / 7)) === w)
            .map((d) => d.day),
        }));

  return (
    <div className="panel rounded-2xl p-5 animate-fade-up">
      <div className="flex flex-wrap items-baseline justify-between gap-2 mb-3">
        <h2 className="font-display text-xl text-[var(--color-moss)]">
          {plan.total_days}-Day Plan
        </h2>
        <span
          className={[
            "text-xs px-2 py-1 rounded-md",
            confirmed
              ? "bg-[var(--color-mint)] text-[var(--color-moss)]"
              : "bg-[var(--color-sand)] text-[var(--color-slate)]",
          ].join(" ")}
        >
          {confirmed ? "Confirmed" : "Awaiting confirmation"}
        </span>
      </div>
      <p className="text-sm text-[var(--color-slate)] mb-4">
        {plan.hours_per_day} h/day
        {plan.balance_notes ? ` — ${plan.balance_notes}` : ""}
      </p>
      <div className="space-y-4 max-h-[28rem] overflow-auto">
        {weeks.map((w) => {
          const days = plan.days.filter((d) =>
            w.days.includes(d.day),
          );
          return (
            <section key={w.week}>
              <h3 className="text-sm font-semibold text-[var(--color-moss)] mb-2">
                WEEK {w.week}
                <span className="font-normal text-[var(--color-slate)]">
                  {" "}
                  · {w.theme}
                </span>
              </h3>
              <ul className="space-y-2">
                {days.map((d) => (
                  <li key={d.day} className="rounded-xl bg-white/70 px-3 py-2.5">
                    <div className="font-medium text-sm">
                      Day {d.day} · {d.topic || d.focus}
                    </div>
                    <div className="text-xs text-[var(--color-slate)] mt-1">
                      Theory {d.theory_hours}h · Coding {d.coding_hours}h ·
                      Revision {d.revision_hours}h · Mock {d.mock_interview_hours}h
                    </div>
                    {!!d.subtopics?.length && (
                      <div className="mt-2 flex flex-wrap gap-1">
                        {d.subtopics.map((s) => (
                          <span
                            key={s}
                            className="text-[11px] px-1.5 py-0.5 rounded bg-[var(--color-sand)]/80"
                          >
                            {s}
                          </span>
                        ))}
                      </div>
                    )}
                    {!!d.tasks?.length && (
                      <ul className="mt-2 text-xs text-[var(--color-ink)]/80 list-disc pl-4 space-y-0.5">
                        {d.tasks.map((t) => (
                          <li key={t}>{t}</li>
                        ))}
                      </ul>
                    )}
                  </li>
                ))}
              </ul>
            </section>
          );
        })}
      </div>
    </div>
  );
}
