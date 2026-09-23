import { useState } from "react";
import type { PendingInterrupt } from "../types/career";

type Props = {
  interrupt: PendingInterrupt;
  onDecide: (payload: {
    action: "approve" | "modify" | "restart" | "clarify";
    modifications?: string;
    target_role?: string;
    user_goal?: string;
  }) => Promise<void>;
  busy: boolean;
};

export function HumanGateModal({ interrupt, onDecide, busy }: Props) {
  const [mods, setMods] = useState("");
  const [role, setRole] = useState("");
  const isClarify = interrupt.type === "clarification";

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-[var(--color-ink)]/40 p-4 animate-fade-up">
      <div className="w-full max-w-lg rounded-2xl bg-[var(--color-paper)] p-6 shadow-xl border border-[var(--color-line)]">
        <p className="text-xs uppercase tracking-wider text-[var(--color-leaf)] mb-2">
          Human-in-the-loop
        </p>
        <h2 className="font-display text-2xl text-[var(--color-moss)] mb-2">
          {interrupt.title ||
            (isClarify ? "Need a clarification" : "Your personalized plan is ready for review.")}
        </h2>
        <p className="text-sm text-[var(--color-ink)]/90 mb-4">
          {interrupt.message || interrupt.question}
        </p>

        {!isClarify && (
          <div className="rounded-xl bg-white/80 p-3 mb-4 text-sm space-y-2">
            {!!interrupt.focus_areas?.length && (
              <div>
                <div className="text-xs uppercase tracking-wider text-[var(--color-slate)] mb-1">
                  Priority skills
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {(interrupt.focus_areas || interrupt.priority_skills || []).map(
                    (s) => (
                      <span
                        key={s}
                        className="text-xs px-2 py-0.5 rounded-md bg-[var(--color-mint)]/50 text-[var(--color-moss)]"
                      >
                        {s}
                      </span>
                    ),
                  )}
                </div>
              </div>
            )}
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div>
                <span className="text-[var(--color-slate)]">Duration</span>
                <div className="font-medium">
                  {interrupt.available_days ||
                    interrupt.study_plan_preview?.total_days ||
                    "—"}{" "}
                  days
                </div>
              </div>
              <div>
                <span className="text-[var(--color-slate)]">Daily commitment</span>
                <div className="font-medium">
                  {interrupt.hours_per_day ||
                    interrupt.study_plan_preview?.hours_per_day ||
                    "—"}{" "}
                  h/day
                </div>
              </div>
            </div>
            {!!interrupt.week_themes?.length && (
              <div>
                <div className="text-xs uppercase tracking-wider text-[var(--color-slate)] mb-1">
                  Main focus areas
                </div>
                <ul className="text-xs list-disc pl-4">
                  {interrupt.week_themes.map((t) => (
                    <li key={t}>{t}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {isClarify ? (
          <div className="space-y-3">
            <input
              value={role}
              onChange={(e) => setRole(e.target.value)}
              placeholder="Target role"
              className="w-full rounded-xl border border-[var(--color-line)] bg-white px-3 py-2 text-sm"
            />
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                disabled={busy || !role.trim()}
                onClick={() =>
                  void onDecide({ action: "clarify", target_role: role.trim() })
                }
                className="btn-primary"
              >
                Continue
              </button>
              <button
                type="button"
                disabled={busy}
                onClick={() => void onDecide({ action: "restart" })}
                className="btn-secondary"
              >
                Restart
              </button>
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            <textarea
              value={mods}
              onChange={(e) => setMods(e.target.value)}
              rows={2}
              placeholder="Optional modifications (e.g. more React, less databases)"
              className="w-full rounded-xl border border-[var(--color-line)] bg-white px-3 py-2 text-sm"
            />
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                disabled={busy}
                onClick={() => void onDecide({ action: "approve" })}
                className="btn-primary"
              >
                Approve Plan
              </button>
              <button
                type="button"
                disabled={busy || !mods.trim()}
                onClick={() =>
                  void onDecide({
                    action: "modify",
                    modifications: mods.trim(),
                  })
                }
                className="btn-secondary"
              >
                Modify Plan
              </button>
              <button
                type="button"
                disabled={busy}
                onClick={() => void onDecide({ action: "restart" })}
                className="btn-secondary"
              >
                Restart
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
