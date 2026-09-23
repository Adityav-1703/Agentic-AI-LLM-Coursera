import { useState } from "react";
import type {
  EvaluationResult,
  InterviewPerformance,
  InterviewQuestion,
} from "../types/career";

type Props = {
  questions: InterviewQuestion[];
  evaluations: EvaluationResult[];
  performance?: InterviewPerformance;
  answers: Array<{ question_id: string; answer: string }>;
  onAnswer: (questionId: string, answer: string) => Promise<void>;
  onEvaluate: () => Promise<void>;
  busy: boolean;
};

function Score({ value }: { value: number | null | undefined }) {
  if (value == null) return <span className="text-[var(--color-slate)]">N/A</span>;
  return <span>{value.toFixed(2)} / 10</span>;
}

export function InterviewPanel({
  questions,
  evaluations,
  performance,
  answers,
  onAnswer,
  onEvaluate,
  busy,
}: Props) {
  const [activeId, setActiveId] = useState(questions[0]?.id || "");
  const [answer, setAnswer] = useState("");
  const active = questions.find((q) => q.id === activeId) || questions[0];
  const evalMap = Object.fromEntries(evaluations.map((e) => [e.question_id, e]));
  const answerMap = Object.fromEntries(answers.map((a) => [a.question_id, a.answer]));
  const weights = performance?.criteria_weights || {
    relevance: 0.3,
    correctness_signals: 0.35,
    structure: 0.2,
    specificity: 0.15,
  };

  if (!questions.length) {
    return (
      <div className="panel rounded-2xl p-5">
        <h2 className="font-display text-xl text-[var(--color-moss)] mb-2">
          Interview practice
        </h2>
        <p className="text-sm text-[var(--color-slate)]">
          Questions appear after you approve the study plan.
        </p>
      </div>
    );
  }

  const activeEval = active ? evalMap[active.id] : undefined;
  const criteria = activeEval?.criteria_scores || activeEval?.criteria || {};
  const labels = activeEval?.criteria_labels || {
    relevance: "Relevance",
    correctness_signals: "Technical correctness",
    structure: "Structure",
    specificity: "Specificity",
  };

  return (
    <div className="panel rounded-2xl p-5 animate-fade-up space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="font-display text-xl text-[var(--color-moss)]">
          Interview practice
        </h2>
        <button
          type="button"
          disabled={busy}
          onClick={() => void onEvaluate()}
          className="btn-primary text-sm py-1.5"
        >
          Evaluate answers
        </button>
      </div>

      <div className="rounded-xl bg-white/70 p-3">
        <h3 className="text-xs uppercase tracking-wider text-[var(--color-slate)] mb-2">
          Interview performance
        </h3>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-sm">
          <div>
            <div className="text-[var(--color-slate)] text-xs">Overall</div>
            <div className="font-semibold">
              <Score value={performance?.overall} />
            </div>
          </div>
          <div>
            <div className="text-[var(--color-slate)] text-xs">Technical</div>
            <div className="font-semibold">
              <Score value={performance?.technical} />
            </div>
          </div>
          <div>
            <div className="text-[var(--color-slate)] text-xs">Behavioral</div>
            <div className="font-semibold">
              <Score value={performance?.behavioral} />
            </div>
          </div>
          <div>
            <div className="text-[var(--color-slate)] text-xs">Coding</div>
            <div className="font-semibold">
              <Score value={performance?.coding} />
            </div>
          </div>
        </div>
        {!!performance?.weakest_areas?.length && (
          <div className="mt-3">
            <div className="text-xs uppercase tracking-wider text-[var(--color-slate)] mb-1">
              Weakest areas
            </div>
            <div className="flex flex-wrap gap-1.5">
              {performance.weakest_areas.map((w) => (
                <span
                  key={w}
                  className="text-xs px-2 py-0.5 rounded-md bg-[var(--color-coral)]/12 text-[var(--color-coral)]"
                >
                  {w}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="flex flex-wrap gap-2">
        {questions.map((q) => (
          <button
            key={q.id}
            type="button"
            onClick={() => {
              setActiveId(q.id);
              setAnswer(answerMap[q.id] || "");
            }}
            className={[
              "text-xs px-2 py-1 rounded-md",
              active?.id === q.id
                ? "bg-[var(--color-moss)] text-white"
                : "bg-white/70",
            ].join(" ")}
          >
            {q.category}
            {evalMap[q.id] ? ` · ${evalMap[q.id].score}/10` : ""}
          </button>
        ))}
      </div>

      {active && (
        <>
          <p className="text-sm font-medium">{active.prompt}</p>
          <textarea
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            rows={4}
            placeholder="Write your answer…"
            className="w-full rounded-xl border border-[var(--color-line)] bg-white/90 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-[var(--color-mint)]"
          />
          <button
            type="button"
            disabled={busy || !answer.trim()}
            onClick={() => void onAnswer(active.id, answer.trim())}
            className="btn-primary text-sm py-1.5"
          >
            Save answer
          </button>

          {activeEval && (
            <div className="rounded-xl bg-[var(--color-sand)]/50 p-3 space-y-2 text-sm">
              <div className="font-medium">Score: {activeEval.score}/10</div>
              <div>
                <div className="text-xs uppercase tracking-wider text-[var(--color-slate)] mb-1">
                  Evaluation criteria
                </div>
                <ul className="space-y-1 text-xs">
                  {Object.keys(weights).map((k) => (
                    <li key={k} className="flex justify-between gap-2">
                      <span>
                        {labels[k] || k} — {Math.round((weights[k] || 0) * 100)}%
                      </span>
                      <span>{(criteria[k] ?? 0).toFixed(1)}/10</span>
                    </li>
                  ))}
                </ul>
              </div>
              {!!activeEval.strengths?.length && (
                <div>
                  <div className="text-xs font-semibold">What went well</div>
                  <ul className="list-disc pl-4 text-xs">
                    {activeEval.strengths.map((s) => (
                      <li key={s}>{s}</li>
                    ))}
                  </ul>
                </div>
              )}
              {!!(activeEval.missing_signals || activeEval.weaknesses)?.length && (
                <div>
                  <div className="text-xs font-semibold">What was missing</div>
                  <ul className="list-disc pl-4 text-xs">
                    {(activeEval.missing_signals?.length
                      ? activeEval.missing_signals
                      : activeEval.weaknesses
                    ).map((s) => (
                      <li key={s}>{s}</li>
                    ))}
                  </ul>
                </div>
              )}
              {!!(activeEval.recommended_topics || activeEval.study_next)?.length && (
                <div className="text-xs">
                  <span className="font-semibold">Study next: </span>
                  {(
                    activeEval.recommended_topics || activeEval.study_next
                  ).join(", ")}
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}
