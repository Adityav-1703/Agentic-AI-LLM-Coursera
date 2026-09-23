import type { SessionState, StartPayload } from "../types/career";

const BASE = "/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    ...init,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || JSON.stringify(body);
    } catch {
      /* ignore */
    }
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return res.json() as Promise<T>;
}

export const api = {
  health: () =>
    request<{ status: string; llm_provider: string; llm_ready: boolean }>(
      "/health",
    ),
  start: (payload: StartPayload) =>
    request<SessionState>("/career/start", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  status: (sessionId: string) =>
    request<SessionState>(`/career/status/${sessionId}`),
  decide: (
    sessionId: string,
    body: {
      action: "approve" | "modify" | "restart" | "clarify";
      modifications?: string;
      target_role?: string;
      user_goal?: string;
    },
  ) =>
    request<SessionState>(`/career/decide/${sessionId}`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  answer: (sessionId: string, questionId: string, answer: string) =>
    request<SessionState>("/interview/answer", {
      method: "POST",
      body: JSON.stringify({
        session_id: sessionId,
        question_id: questionId,
        answer,
      }),
    }),
  evaluate: (sessionId: string) =>
    request<SessionState>("/interview/evaluate", {
      method: "POST",
      body: JSON.stringify({ session_id: sessionId }),
    }),
  report: (sessionId: string) =>
    request<SessionState>(`/career/report/${sessionId}`, { method: "POST" }),
  studyPlan: (sessionId: string) =>
    request<{ study_plan: unknown; plan_confirmed: boolean }>(
      `/study-plan/${sessionId}`,
    ),
};
