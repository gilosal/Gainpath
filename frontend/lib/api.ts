/**
 * api.ts — Typed fetch wrapper for the PaceForge FastAPI backend.
 *
 * Credentials are stored in localStorage (username + password) and sent
 * as HTTP Basic auth on every request. Single-user app — no token refresh needed.
 */

import type {
  UserProfile,
  TrainingPlan,
  TrainingPlanSummary,
  SessionLog,
  SetLog,
  BodyFeedback,
  DashboardSummary,
  WeeklyTrendPoint,
  ExerciseProgressPoint,
  CalendarWeek,
  AIUsageSummary,
  OfflineQueueItem,
  StreakSnapshot,
  Achievement,
  XPState,
  WeeklyChallenge,
  PersonalRecord,
  CoachingMessage,
  ChatMessage,
} from "./types";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// ── Auth helpers ──────────────────────────────────────────────────────────────

function getCredentials(): string {
  if (typeof window === "undefined") return "";
  const pass = localStorage.getItem("paceforge-password") ?? "";
  return btoa(`paceforge:${pass}`);
}

export function savePassword(password: string) {
  localStorage.setItem("paceforge-password", password);
}

// ── Core fetch ────────────────────────────────────────────────────────────────

async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${BASE_URL}${path}`;
  const res = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Basic ${getCredentials()}`,
      ...options.headers,
    },
  });

  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new ApiError(res.status, body || res.statusText);
  }

  if (res.status === 204) return undefined as unknown as T;
  return res.json() as Promise<T>;
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string
  ) {
    super(message);
    this.name = "ApiError";
  }
}

// ── Profile ───────────────────────────────────────────────────────────────────

export const profileApi = {
  get: () => apiFetch<UserProfile>("/profile"),
  update: (data: Partial<UserProfile>) =>
    apiFetch<UserProfile>("/profile", {
      method: "PUT",
      body: JSON.stringify(data),
    }),
};

// ── Plans ─────────────────────────────────────────────────────────────────────

export const plansApi = {
  list: () => apiFetch<TrainingPlanSummary[]>("/plans"),
  get: (id: string) => apiFetch<TrainingPlan>(`/plans/${id}`),
  generateRunning: () =>
    apiFetch<TrainingPlan>("/plans/generate/running", { method: "POST" }),
  generateLifting: () =>
    apiFetch<TrainingPlan>("/plans/generate/lifting", { method: "POST" }),
  generateMobility: () =>
    apiFetch<TrainingPlan>("/plans/generate/mobility", { method: "POST" }),
  recalculate: (id: string) =>
    apiFetch<TrainingPlan>(`/plans/${id}/recalculate`, { method: "POST" }),
  delete: (id: string) =>
    apiFetch<void>(`/plans/${id}`, { method: "DELETE" }),
};

// ── Sessions ──────────────────────────────────────────────────────────────────

export const sessionsApi = {
  list: (params?: { session_date?: string; session_type?: string }) => {
    const q = new URLSearchParams(params as Record<string, string>).toString();
    return apiFetch<SessionLog[]>(`/sessions${q ? `?${q}` : ""}`);
  },
  today: () => apiFetch<SessionLog[]>("/sessions/today"),
  get: (id: string) => apiFetch<SessionLog>(`/sessions/${id}`),
  create: (data: { session_date: string; session_type: string; planned_session_id?: string }) =>
    apiFetch<SessionLog>("/sessions", { method: "POST", body: JSON.stringify(data) }),
  update: (id: string, data: Partial<SessionLog>) =>
    apiFetch<SessionLog>(`/sessions/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  delete: (id: string) =>
    apiFetch<void>(`/sessions/${id}`, { method: "DELETE" }),

  // Sets
  addSet: (sessionId: string, data: Partial<SetLog>) =>
    apiFetch<SetLog>(`/sessions/${sessionId}/sets`, {
      method: "POST",
      body: JSON.stringify(data),
    }),
  updateSet: (sessionId: string, setId: string, data: Partial<SetLog>) =>
    apiFetch<SetLog>(`/sessions/${sessionId}/sets/${setId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  deleteSet: (sessionId: string, setId: string) =>
    apiFetch<void>(`/sessions/${sessionId}/sets/${setId}`, { method: "DELETE" }),

  // Body feedback
  addFeedback: (sessionId: string, data: Partial<BodyFeedback>) =>
    apiFetch<BodyFeedback>(`/sessions/${sessionId}/feedback`, {
      method: "POST",
      body: JSON.stringify(data),
    }),
  listFeedback: (sessionId: string) =>
    apiFetch<BodyFeedback[]>(`/sessions/${sessionId}/feedback`),
};

// ── Dashboard ─────────────────────────────────────────────────────────────────

export const dashboardApi = {
  summary: () => apiFetch<DashboardSummary>("/dashboard/summary"),
  runningTrends: (weeks = 12) =>
    apiFetch<WeeklyTrendPoint[]>(`/dashboard/trends/running?weeks=${weeks}`),
  liftingTrends: (weeks = 12) =>
    apiFetch<WeeklyTrendPoint[]>(`/dashboard/trends/lifting?weeks=${weeks}`),
  mobilityTrends: (weeks = 12) =>
    apiFetch<WeeklyTrendPoint[]>(`/dashboard/trends/mobility?weeks=${weeks}`),
  exerciseProgression: (name: string) =>
    apiFetch<ExerciseProgressPoint[]>(
      `/dashboard/trends/exercise/${encodeURIComponent(name)}`
    ),
  calendar: (startDate: string) =>
    apiFetch<CalendarWeek>(`/dashboard/calendar?start_date=${startDate}`),
};

// ── AI Usage ──────────────────────────────────────────────────────────────────

export const aiUsageApi = {
  summary: (days = 30) =>
    apiFetch<AIUsageSummary>(`/ai-usage/summary?days=${days}`),
};

// ── Offline sync ──────────────────────────────────────────────────────────────

export const offlineApi = {
  enqueue: (item: { action_type: string; payload: Record<string, unknown>; session_log_id?: string }) =>
    apiFetch<OfflineQueueItem>("/offline/queue", {
      method: "POST",
      body: JSON.stringify(item),
    }),
  sync: () => apiFetch<{ synced: number; failed: number; total: number }>("/offline/sync", { method: "POST" }),
};

// ── Gamification ──────────────────────────────────────────────────────────────

export const gamificationApi = {
  streak: () => apiFetch<StreakSnapshot>("/gamification/streak"),
  freezeStreak: () => apiFetch<{ message: string }>("/gamification/streak/freeze", { method: "POST" }),
  achievements: () => apiFetch<Achievement[]>("/gamification/achievements"),
  xp: () => apiFetch<XPState>("/gamification/xp"),
  challenges: () => apiFetch<WeeklyChallenge[]>("/gamification/challenges"),
  prs: (exercise?: string) => {
    const q = exercise ? `?exercise=${encodeURIComponent(exercise)}` : "";
    return apiFetch<PersonalRecord[]>(`/gamification/prs${q}`);
  },
  uncelebratedPrs: () => apiFetch<PersonalRecord[]>("/gamification/prs/uncelebrated"),
  celebratePr: (prId: string) =>
    apiFetch<{ ok: boolean }>(`/gamification/prs/${prId}/celebrate`, { method: "PATCH" }),
};

// ── Coaching ──────────────────────────────────────────────────────────────────

export const coachingApi = {
  messages: (messageType?: string) => {
    const q = messageType ? `?message_type=${messageType}` : "";
    return apiFetch<CoachingMessage[]>(`/coaching/messages${q}`);
  },
  latestMessage: (messageType: string) =>
    apiFetch<CoachingMessage | null>(`/coaching/messages/latest?message_type=${messageType}`),
  dismissMessage: (id: string) =>
    apiFetch<void>(`/coaching/messages/${id}/dismiss`, { method: "POST" }),
  markDisplayed: (id: string) =>
    apiFetch<void>(`/coaching/messages/${id}/mark-displayed`, { method: "POST" }),
  generateDaily: () =>
    apiFetch<{ status: string }>("/coaching/generate/daily", { method: "POST" }),
  generateWeeklySummary: () =>
    apiFetch<{ status: string }>("/coaching/generate/weekly-summary", { method: "POST" }),
  triggerPostWorkout: (sessionId: string) =>
    apiFetch<{ status: string }>(`/coaching/generate/post-workout/${sessionId}`, { method: "POST" }),
  chatHistory: (limit = 50) =>
    apiFetch<ChatMessage[]>(`/coaching/chat?limit=${limit}`),
  sendChat: (message: string) =>
    apiFetch<{ user_message: ChatMessage; assistant_message: ChatMessage }>("/coaching/chat", {
      method: "POST",
      body: JSON.stringify({ message }),
    }),
};
