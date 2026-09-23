import { useEffect, useRef, useState } from "react";
import { api } from "./services/api";
import type { SessionState, StartPayload } from "./types/career";
import { GoalForm } from "./components/GoalForm";
import { WorkflowViz } from "./components/WorkflowViz";
import { AgentActivity } from "./components/AgentActivity";
import { SkillGapPanel } from "./components/SkillGapPanel";
import { StudyPlanPanel } from "./components/StudyPlanPanel";
import { InterviewPanel } from "./components/InterviewPanel";
import { HumanGateModal } from "./components/HumanGateModal";
import { ProgressPanel } from "./components/ProgressPanel";
import { FinalReportPanel } from "./components/FinalReportPanel";
import { AgentInspector } from "./components/AgentInspector";

export default function App() {
  const [session, setSession] = useState<SessionState | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [provider, setProvider] = useState<string>("…");
  const [inspectorOpen, setInspectorOpen] = useState(false);
  const skillsRef = useRef<HTMLDivElement>(null);
  const interviewRef = useRef<HTMLDivElement>(null);
  const planRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    void api
      .health()
      .then((h) => setProvider(h.llm_provider))
      .catch(() => setProvider("unreachable"));
  }, []);

  async function run<T>(fn: () => Promise<T>): Promise<T | undefined> {
    setBusy(true);
    setError(null);
    try {
      return await fn();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      return undefined;
    } finally {
      setBusy(false);
    }
  }

  async function handleStart(payload: StartPayload) {
    const data = await run(() => api.start(payload));
    if (data) setSession(data);
  }

  async function handleDecide(body: {
    action: "approve" | "modify" | "restart" | "clarify";
    modifications?: string;
    target_role?: string;
    user_goal?: string;
  }) {
    if (!session) return;
    const data = await run(() => api.decide(session.session_id, body));
    if (data) setSession(data);
  }

  async function handleAnswer(questionId: string, answer: string) {
    if (!session) return;
    const data = await run(() =>
      api.answer(session.session_id, questionId, answer),
    );
    if (data) setSession(data);
  }

  async function handleEvaluate() {
    if (!session) return;
    const data = await run(() => api.evaluate(session.session_id));
    if (data) setSession(data);
  }

  async function handleReport() {
    if (!session) return;
    const data = await run(() => api.report(session.session_id));
    if (data) setSession(data);
  }

  const engineLabel =
    provider === "offline"
      ? "Offline Demo Mode"
      : provider === "unreachable"
        ? "API unreachable"
        : provider;

  return (
    <div className="min-h-screen pb-16">
      <header className="relative overflow-hidden border-b border-[var(--color-line)]">
        <div className="relative max-w-6xl mx-auto px-4 py-10 sm:py-12">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h1 className="font-display text-4xl sm:text-5xl text-[var(--color-moss)] animate-fade-up tracking-tight">
                CareerPilot
              </h1>
              <p className="mt-2 text-lg text-[var(--color-ink)]/85 animate-fade-up">
                AI-powered career preparation
              </p>
              <p
                className="mt-2 max-w-xl text-[var(--color-slate)] animate-fade-up"
                style={{ animationDelay: "50ms" }}
              >
                Turn your target role into a personalized learning and interview
                strategy.
              </p>
              <p className="mt-3 inline-flex text-[11px] uppercase tracking-[0.14em] px-2.5 py-1 rounded-md bg-white/70 border border-[var(--color-line)] text-[var(--color-leaf)]">
                Powered by LangGraph · Multi-Agent AI · Human-in-the-Loop
              </p>
            </div>
            <div className="text-right text-xs text-[var(--color-slate)]">
              <div className="uppercase tracking-wider">AI Engine</div>
              <div className="font-medium text-[var(--color-moss)] text-sm mt-0.5">
                {engineLabel}
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-8 space-y-6">
        {error && (
          <div className="rounded-xl bg-[var(--color-coral)]/15 text-[var(--color-coral)] px-4 py-3 text-sm">
            {error}
          </div>
        )}

        <GoalForm onStart={handleStart} busy={busy} />

        {session && (
          <>
            <ProgressPanel
              progress={session.progress}
              onContinue={() => planRef.current?.scrollIntoView({ behavior: "smooth" })}
              onInterview={() =>
                interviewRef.current?.scrollIntoView({ behavior: "smooth" })
              }
              onSkills={() =>
                skillsRef.current?.scrollIntoView({ behavior: "smooth" })
              }
            />

            <div className="grid lg:grid-cols-2 gap-6">
              <WorkflowViz
                agents={session.agent_statuses || []}
                status={session.workflow_status}
              />
              <AgentActivity
                events={session.activity_log}
                onOpenInspector={() => setInspectorOpen(true)}
              />
            </div>

            <div ref={skillsRef} className="grid lg:grid-cols-2 gap-6">
              <SkillGapPanel
                assessments={session.skill_assessments || []}
                gaps={session.skill_gaps}
              />
              <div ref={planRef}>
                <StudyPlanPanel
                  plan={session.study_plan}
                  confirmed={session.plan_confirmed}
                />
              </div>
            </div>

            <div ref={interviewRef}>
              <InterviewPanel
                questions={session.interview_questions}
                evaluations={session.evaluation_results}
                performance={session.interview_performance}
                answers={session.user_answers}
                onAnswer={handleAnswer}
                onEvaluate={handleEvaluate}
                busy={busy}
              />
            </div>

            <FinalReportPanel
              report={session.final_report}
              onGenerate={handleReport}
              canGenerate={session.plan_confirmed}
              busy={busy}
            />

            {!!session.research_results?.length && (
              <p className="text-xs text-[var(--color-slate)]">
                Research items: {session.research_results.length}
                {session.research_results.some(
                  (r) =>
                    r.source_type === "local_knowledge" ||
                    String(r.label || "").includes("LOCAL"),
                )
                  ? " · includes clearly labelled local fallback resources"
                  : ""}
              </p>
            )}
          </>
        )}
      </main>

      {session?.interrupted && session.pending_interrupt && (
        <HumanGateModal
          interrupt={session.pending_interrupt}
          onDecide={handleDecide}
          busy={busy}
        />
      )}

      {session && (
        <AgentInspector
          open={inspectorOpen}
          onClose={() => setInspectorOpen(false)}
          session={session}
        />
      )}
    </div>
  );
}
