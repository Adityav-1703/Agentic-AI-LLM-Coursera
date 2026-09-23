import type { AgentStatus, SessionState } from "../types/career";

type Props = {
  open: boolean;
  onClose: () => void;
  session: SessionState;
};

const STATUS_BADGE: Record<string, string> = {
  completed: "bg-[var(--color-mint)]/60 text-[var(--color-moss)]",
  running: "bg-[var(--color-moss)] text-white",
  waiting_for_user: "bg-[var(--color-sand)] text-[var(--color-moss)]",
  needs_review: "bg-[var(--color-coral)]/15 text-[var(--color-coral)]",
  pending: "bg-white text-[var(--color-slate)]",
  skipped: "bg-white/50 text-[var(--color-slate)]",
  failed: "bg-red-100 text-red-700",
};

export function AgentInspector({ open, onClose, session }: Props) {
  if (!open) return null;
  const agents: AgentStatus[] = session.agent_statuses || [];
  const arch = session.architecture || {};

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-[var(--color-ink)]/45 p-4">
      <div className="w-full max-w-2xl max-h-[90vh] overflow-auto rounded-2xl bg-[var(--color-paper)] p-6 shadow-xl border border-[var(--color-line)]">
        <div className="flex items-start justify-between gap-3 mb-4">
          <div>
            <p className="text-xs uppercase tracking-wider text-[var(--color-leaf)]">
              Portfolio technical view
            </p>
            <h2 className="font-display text-2xl text-[var(--color-moss)]">
              Agent Inspector
            </h2>
          </div>
          <button type="button" className="btn-secondary text-sm py-1.5" onClick={onClose}>
            Close
          </button>
        </div>

        <ol className="space-y-3 mb-6">
          {agents.map((a, idx) => (
            <li key={a.id}>
              <div className="rounded-xl bg-white/80 px-3 py-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="font-medium">{a.label}</span>
                  <span
                    className={[
                      "text-[10px] uppercase tracking-wide px-2 py-0.5 rounded-md",
                      STATUS_BADGE[a.status] || STATUS_BADGE.pending,
                    ].join(" ")}
                  >
                    {a.status.replaceAll("_", " ")}
                  </span>
                </div>
                <p className="text-sm text-[var(--color-slate)] mt-1">{a.task}</p>
                {a.reason && (
                  <p className="text-xs mt-1 text-[var(--color-ink)]/70">{a.reason}</p>
                )}
              </div>
              {idx < agents.length - 1 && (
                <div className="text-center text-[var(--color-mint)] text-lg my-1">↓</div>
              )}
            </li>
          ))}
        </ol>

        <div className="rounded-xl border border-[var(--color-line)] bg-white/70 p-4">
          <h3 className="font-display text-lg text-[var(--color-moss)] mb-3">
            Technical architecture
          </h3>
          <dl className="grid sm:grid-cols-2 gap-3 text-sm">
            {Object.entries({
              Framework: arch.framework || "LangGraph",
              State: arch.state || "Typed shared state",
              Routing: arch.routing || "Conditional graph edges",
              Persistence: arch.persistence || "SQLite / checkpointing",
              "Human-in-the-loop": arch.human_in_the_loop || "LangGraph interrupt",
              LLM: arch.llm || session.llm_provider || "offline",
              API: arch.api || "FastAPI",
              Frontend: arch.frontend || "React + TypeScript",
            }).map(([k, v]) => (
              <div key={k}>
                <dt className="text-xs uppercase tracking-wider text-[var(--color-slate)]">
                  {k}
                </dt>
                <dd className="font-medium">{v}</dd>
              </div>
            ))}
          </dl>
          <p className="text-xs text-[var(--color-slate)] mt-4">
            CrewAI, AutoGen, and BeeAI appear only as isolated demos under{" "}
            <code>framework_demos/</code> — production orchestration is LangGraph.
          </p>
        </div>
      </div>
    </div>
  );
}
