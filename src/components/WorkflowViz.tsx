import type { AgentStatus } from "../types/career";

const STATUS_STYLE: Record<string, string> = {
  pending: "bg-white/70 text-[var(--color-slate)]",
  running: "bg-[var(--color-moss)] text-white shadow-md scale-[1.02]",
  completed: "bg-[var(--color-mint)]/55 text-[var(--color-moss)]",
  waiting_for_user: "bg-[var(--color-sand)] text-[var(--color-moss)]",
  needs_review: "bg-[var(--color-coral)]/15 text-[var(--color-coral)]",
  failed: "bg-red-100 text-red-700",
  skipped: "bg-white/40 text-[var(--color-slate)] opacity-70",
};

type Props = {
  agents: AgentStatus[];
  status: string;
};

export function WorkflowViz({ agents, status }: Props) {
  const flow = agents.filter((a) => a.id !== "human");
  return (
    <div className="panel rounded-2xl p-5 animate-fade-up">
      <div className="flex flex-wrap items-baseline justify-between gap-2 mb-4">
        <h2 className="font-display text-xl text-[var(--color-moss)]">
          Preparation workflow
        </h2>
        <span className="text-xs uppercase tracking-wider text-[var(--color-slate)]">
          {status.replaceAll("_", " ")}
        </span>
      </div>
      <div className="flex flex-col gap-2">
        {flow.map((agent, idx) => (
          <div key={agent.id} className="flex items-stretch gap-2">
            <div className="flex flex-col items-center w-4 shrink-0">
              <span
                className={[
                  "mt-3 h-2.5 w-2.5 rounded-full",
                  agent.status === "running"
                    ? "bg-[var(--color-coral)] animate-pulse-dot"
                    : agent.status === "completed"
                      ? "bg-[var(--color-leaf)]"
                      : "bg-[var(--color-mint)]",
                ].join(" ")}
              />
              {idx < flow.length - 1 && (
                <span className="flex-1 w-px bg-[var(--color-mint)] my-1" />
              )}
            </div>
            <div
              className={[
                "flex-1 rounded-xl px-3 py-2.5 transition-all",
                STATUS_STYLE[agent.status] || STATUS_STYLE.pending,
              ].join(" ")}
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className="font-medium text-sm">{agent.label}</span>
                <span className="text-[10px] uppercase tracking-wide opacity-80">
                  {agent.status.replaceAll("_", " ")}
                </span>
              </div>
              <p className="text-xs mt-0.5 opacity-80">{agent.task}</p>
              {agent.reason && (
                <p className="text-xs mt-1 opacity-70">{agent.reason}</p>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
