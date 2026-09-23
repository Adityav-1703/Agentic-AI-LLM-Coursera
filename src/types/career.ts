export type ExperienceLevel = "beginner" | "intermediate" | "advanced";

export type AgentStatusKind =
  | "pending"
  | "running"
  | "completed"
  | "waiting_for_user"
  | "needs_review"
  | "failed"
  | "skipped";

export interface SkillAssessment {
  name: string;
  status: "strong" | "developing" | "needs_improvement";
  priority: "high" | "medium" | "low";
  subskills: string[];
  evidence: string[];
  why_gap?: string | null;
}

export interface InterviewQuestion {
  id: string;
  category: "technical" | "behavioral" | "coding";
  difficulty: string;
  prompt: string;
  expected_signals?: string[];
}

export interface EvaluationResult {
  question_id: string;
  score: number;
  criteria: Record<string, number>;
  criteria_scores?: Record<string, number>;
  criteria_weights?: Record<string, number>;
  criteria_labels?: Record<string, string>;
  matched_signals?: string[];
  missing_signals?: string[];
  strengths: string[];
  weaknesses: string[];
  feedback: string;
  study_next: string[];
  recommended_topics?: string[];
  mapped_skill_gaps?: string[];
  major_weaknesses: boolean;
  question_prompt?: string;
  category?: string;
  user_answer?: string;
}

export interface StudyDay {
  day: number;
  week?: number;
  focus: string;
  topic?: string;
  subtopics?: string[];
  theory_hours: number;
  coding_hours: number;
  revision_hours: number;
  mock_interview_hours: number;
  tasks: string[];
  completed?: boolean;
}

export interface StudyWeek {
  week: number;
  theme: string;
  focus_skills: string[];
  days: number[];
}

export interface StudyPlan {
  total_days: number;
  hours_per_day: number;
  days: StudyDay[];
  weeks?: StudyWeek[];
  balance_notes?: string;
  confirmed?: boolean;
}

export interface ActivityEvent {
  timestamp?: string;
  agent: string;
  action: string;
  detail?: string;
  user_summary?: string;
}

export interface AgentStatus {
  id: string;
  label: string;
  status: AgentStatusKind;
  task: string;
  reason?: string | null;
}

export interface PendingInterrupt {
  type?: string;
  title?: string;
  message?: string;
  question?: string;
  priority_skills?: string[];
  focus_areas?: string[];
  available_days?: number;
  hours_per_day?: number;
  week_themes?: string[];
  options?: string[];
  study_plan_preview?: {
    total_days?: number;
    hours_per_day?: number;
    weeks?: StudyWeek[];
    first_three_days?: StudyDay[];
  };
}

export interface ProgressDashboard {
  overall_pct: number;
  interview_completion_pct: number;
  study_completion_pct: number;
  research_completion_pct: number;
  skill_coverage: { assessed: number; total: number; pct: number };
  current_focus: string;
  next_action: string;
}

export interface InterviewPerformance {
  overall: number | null;
  technical: number | null;
  behavioral: number | null;
  coding: number | null;
  weakest_areas: string[];
  criteria_weights: Record<string, number>;
}

export interface SessionState {
  session_id: string;
  workflow_status: string;
  current_agent?: string | null;
  next_agent?: string | null;
  interrupted: boolean;
  pending_interrupt?: PendingInterrupt | null;
  target_role?: string | null;
  user_goal?: string | null;
  experience_level?: string | null;
  available_days?: number | null;
  hours_per_day?: number | null;
  skills: string[];
  priority_skills: string[];
  skill_gaps: string[];
  skill_assessments: SkillAssessment[];
  research_results: Array<Record<string, unknown>>;
  study_plan?: StudyPlan | null;
  plan_confirmed: boolean;
  interview_questions: InterviewQuestion[];
  user_answers: Array<{ question_id: string; answer: string }>;
  evaluation_results: EvaluationResult[];
  interview_performance?: InterviewPerformance;
  progress?: ProgressDashboard;
  agent_statuses?: AgentStatus[];
  final_report?: Record<string, unknown> | null;
  agent_messages: Array<Record<string, unknown>>;
  activity_log: ActivityEvent[];
  memory: Record<string, unknown>;
  error?: string | null;
  completed_agents: string[];
  llm_provider?: string;
  architecture?: Record<string, string>;
}

export interface StartPayload {
  user_goal: string;
  target_role: string;
  experience_level: ExperienceLevel;
  available_days: number;
  hours_per_day: number;
}

export const AGENT_FLOW = [
  "orchestrator",
  "career_analyst",
  "researcher",
  "study_planner",
  "interviewer",
  "evaluator",
  "report_agent",
] as const;
