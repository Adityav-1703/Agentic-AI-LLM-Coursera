import { useState } from "react";
import type { ActivityEvent } from "../types/career";

const AGENT_LABEL: Record<string, string> = {
  orchestrator: "Orchestrator",
  career_analyst: "Career Analyst",
  researcher: "Research Agent",
  study_planner: "Study Planner",
  interviewer: "Interview Agent",
  evaluator: "Evaluator",
  report_agent: "Report Agent",
  human: "Your approval",
};

type Props = { events: ActivityEvent[]; onOpenInspector?: () => void };

export function AgentActivity({ events, onOpenInspector }: Props) {
  const [technical, setTechnical] = useState(false);
  const latest = [...events].reverse().slice(0, 12);

  return (
    <div className="panel rounded-2xl p-5 h-full animate-fade-up">
      <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
        <h2 className="font-display text-xl text-[var(--color-moss)]">
          Activity
        </h2>
        <div className="flex gap-2">
          <button
            type="button"
            className="text-xs px-2.5 py-1 rounded-lg bg-white border border-[var(--color-line)]"
            onClick={() => setTechnical((v) => !v)}
          >
            {technical ? "User view" : "View technical execution"}
          </button>
          {onOpenInspector && (
            <button
              type="button"
              className="text-xs px-2.5 py-1 rounded-lg bg-[var(--color-moss)] text-white"
              onClick={onOpenInspector}
            >
              Agent Inspector
            </button>
          )}
        </div>
      </div>
      <ol className="space-y-3 max-h-80 overflow-auto pr-1">
        {latest.length === 0 && (
          <li className="text-sm text-[var(--color-slate)]">
            Activity appears after you start preparation.
          </li>
        )}
        {latest.map((e, i) => (
          <li
            key={`${e.timestamp}-${e.agent}-${i}`}
            className="border-l-2 border-[var(--color-mint)] pl-3"
          >
            {technical ? (
              <>
                <div className="text-xs uppercase tracking-wide text-[var(--color-leaf)]">
                  {e.agent} → {e.action}
                </div>
                <p className="text-sm mt-0.5">{e.detail || "—"}</p>
              </>
            ) : (
              <>
                <div className="text-xs uppercase tracking-wide text-[var(--color-leaf)]">
                  {AGENT_LABEL[e.agent] || e.agent}
                </div>
                <p className="text-sm mt-0.5">
                  {e.user_summary || e.detail || "Step completed."}
                </p>
              </>
            )}
          </li>
        ))}
      </ol>
    </div>
  );
}
