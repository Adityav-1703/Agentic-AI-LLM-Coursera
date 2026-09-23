import { useState } from "react";
import type { ExperienceLevel, StartPayload } from "../types/career";

type Props = {
  onStart: (payload: StartPayload) => Promise<void>;
  busy: boolean;
};

export function GoalForm({ onStart, busy }: Props) {
  const [userGoal, setUserGoal] = useState(
    "I want to prepare for a Full Stack Developer interview.",
  );
  const [targetRole, setTargetRole] = useState("Full Stack Developer");
  const [level, setLevel] = useState<ExperienceLevel>("intermediate");
  const [days, setDays] = useState(30);
  const [hours, setHours] = useState(2);

  return (
    <form
      className="panel rounded-2xl p-5 sm:p-6 animate-fade-up"
      onSubmit={(e) => {
        e.preventDefault();
        void onStart({
          user_goal: userGoal,
          target_role: targetRole,
          experience_level: level,
          available_days: days,
          hours_per_day: hours,
        });
      }}
    >
      <h2 className="font-display text-2xl text-[var(--color-moss)] mb-1">
        Start preparation
      </h2>
      <p className="text-sm text-[var(--color-slate)] mb-5">
        Tell us your target role and schedule. CareerPilot builds a personalized
        learning and interview strategy.
      </p>

      <label className="block text-xs uppercase tracking-wider text-[var(--color-slate)] mb-1">
        Career goal
      </label>
      <textarea
        required
        minLength={8}
        value={userGoal}
        onChange={(e) => setUserGoal(e.target.value)}
        rows={2}
        placeholder="I want to prepare for a Full Stack Developer interview."
        className="w-full mb-3 rounded-xl border border-[var(--color-line)] bg-white/90 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-[var(--color-mint)]"
      />

      <div className="grid sm:grid-cols-2 gap-3">
        <div>
          <label className="block text-xs uppercase tracking-wider text-[var(--color-slate)] mb-1">
            Target role
          </label>
          <input
            required
            value={targetRole}
            onChange={(e) => setTargetRole(e.target.value)}
            placeholder="Full Stack Developer"
            className="w-full rounded-xl border border-[var(--color-line)] bg-white/90 px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label className="block text-xs uppercase tracking-wider text-[var(--color-slate)] mb-1">
            Experience level
          </label>
          <select
            value={level}
            onChange={(e) => setLevel(e.target.value as ExperienceLevel)}
            className="w-full rounded-xl border border-[var(--color-line)] bg-white/90 px-3 py-2 text-sm"
          >
            <option value="beginner">Beginner</option>
            <option value="intermediate">Intermediate</option>
            <option value="advanced">Advanced</option>
          </select>
        </div>
        <div>
          <label className="block text-xs uppercase tracking-wider text-[var(--color-slate)] mb-1">
            Preparation duration
          </label>
          <div className="flex items-center gap-2">
            <input
              type="number"
              min={1}
              max={180}
              value={days}
              onChange={(e) => setDays(Number(e.target.value))}
              className="w-full rounded-xl border border-[var(--color-line)] bg-white/90 px-3 py-2 text-sm"
            />
            <span className="text-sm text-[var(--color-slate)] shrink-0">days</span>
          </div>
        </div>
        <div>
          <label className="block text-xs uppercase tracking-wider text-[var(--color-slate)] mb-1">
            Daily availability
          </label>
          <div className="flex items-center gap-2">
            <input
              type="number"
              min={0.5}
              max={16}
              step={0.5}
              value={hours}
              onChange={(e) => setHours(Number(e.target.value))}
              className="w-full rounded-xl border border-[var(--color-line)] bg-white/90 px-3 py-2 text-sm"
            />
            <span className="text-sm text-[var(--color-slate)] shrink-0">hours/day</span>
          </div>
        </div>
      </div>

      <button type="submit" disabled={busy} className="btn-primary mt-5 w-full sm:w-auto">
        {busy ? "Building your plan…" : "Build My Preparation Plan"}
      </button>
    </form>
  );
}
