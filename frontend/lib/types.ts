// ── Shared TypeScript types mirroring the FastAPI schemas ───────────────────

export type SessionType = "running" | "lifting" | "mobility" | "rest";
export type PlanType = "running" | "lifting" | "mobility" | "unified";
export type SessionStatus = "planned" | "in_progress" | "completed" | "skipped";
export type SyncStatus = "pending" | "syncing" | "synced" | "failed";

// ── User Profile ──────────────────────────────────────────────────────────────
export interface UserProfile {
  id: string;
  created_at: string;
  updated_at: string;
  name: string;
  running_goal_race?: string;
  running_goal_date?: string;
  running_fitness_level?: string;
  running_weekly_mileage?: number;
  running_recent_race_time?: string;
  training_days_per_week: number;
  available_equipment: string;
  weight_training_goal: string;
  training_preferred_days: string[];
  mobility_goal: string;
  mobility_target_areas: string[];
  mobility_experience: string;
  mobility_session_length: number;
  available_days: string[];
  session_time_constraints: Record<string, number>;
  no_morning_days: string[];
  units_weight: "kg" | "lb";
  units_distance: "km" | "mi";
  dark_mode: boolean;
  preferred_ai_model?: string;
}

// ── Plans ─────────────────────────────────────────────────────────────────────
export interface PlannedSession {
  id: string;
  plan_week_id: string;
  day_of_week: string;
  session_date: string;
  session_type: SessionType;
  session_subtype?: string;
  title: string;
  description?: string;
  estimated_duration?: number;
  exercises: ExerciseBlock[] | RunBlock[] | MobilityMove[];
  is_stacked: boolean;
  order_in_stack: number;
}

export interface PlanWeek {
  id: string;
  plan_id: string;
  week_number: number;
  week_start_date: string;
  theme?: string;
  focus?: string;
  total_volume_target?: number;
  sessions: PlannedSession[];
}

export interface TrainingPlan {
  id: string;
  created_at: string;
  updated_at: string;
  plan_type: PlanType;
  goal?: string;
  start_date: string;
  end_date: string;
  status: "active" | "completed" | "archived";
  weeks_total: number;
  weeks: PlanWeek[];
}

export interface TrainingPlanSummary {
  id: string;
  plan_type: PlanType;
  goal?: string;
  start_date: string;
  end_date: string;
  status: string;
  weeks_total: number;
}

// ── Exercise types ────────────────────────────────────────────────────────────
export interface ExerciseBlock {
  exercise_name: string;
  sets: number;
  reps: string;
  rpe?: string;
  rest_seconds: number;
  tempo?: string;
  notes: string;
  superset_group?: string;
}

export interface RunBlock {
  distance_km?: number;
  pace_target?: string;
  effort_zone?: string;
  intervals?: IntervalSet[];
  notes: string;
}

export interface IntervalSet {
  reps: number;
  distance_m: number;
  target_pace: string;
  rest_seconds: number;
}

export interface MobilityMove {
  name: string;
  target_area: string;
  hold_duration_seconds?: number;
  reps?: number;
  sets?: number;
  body_side: string;
  instructions: string;
  beginner_modification?: string;
  props_needed: string[];
}

// ── Session Logs ──────────────────────────────────────────────────────────────
export interface SetLog {
  id: string;
  session_log_id: string;
  exercise_name: string;
  exercise_library_id?: string;
  set_number: number;
  set_type: "working" | "warmup" | "dropset" | "failure";
  weight?: number;
  reps?: number;
  rpe?: number;
  distance?: number;
  duration?: number;
  pace?: number;
  hold_duration?: number;
  body_side?: string;
  tightness_notes?: string;
  completed_at: string;
  is_offline: boolean;
}

export interface BodyFeedback {
  id: string;
  session_log_id: string;
  logged_at: string;
  body_area: string;
  feeling: "good" | "tight" | "sore" | "pain";
  severity?: number;
  notes?: string;
}

export interface SessionLog {
  id: string;
  planned_session_id?: string;
  session_date: string;
  session_type: SessionType;
  started_at?: string;
  completed_at?: string;
  status: SessionStatus;
  overall_rpe?: number;
  notes?: string;
  actual_distance?: number;
  actual_duration?: number;
  actual_pace?: number;
  total_tonnage?: number;
  completed_flow?: boolean;
  sets: SetLog[];
  body_feedback: BodyFeedback[];
}

// ── Dashboard ─────────────────────────────────────────────────────────────────
export interface DashboardSummary {
  today: string;
  week_start: string;
  running_km_this_week: number;
  lifting_tonnage_this_week: number;
  mobility_minutes_this_week: number;
  sessions_completed_this_week: number;
  sessions_planned_this_week: number;
  today_sessions_count: number;
}

export interface WeeklyTrendPoint {
  week: string;
  km?: number;
  tonnage?: number;
  sessions?: number;
  minutes?: number;
}

export interface ExerciseProgressPoint {
  date: string;
  weight: number;
  reps: number;
  estimated_1rm: number;
  rpe?: number;
}

// ── Calendar ──────────────────────────────────────────────────────────────────
export interface CalendarDay {
  date: string;
  day_of_week: string;
  planned_sessions: {
    id: string;
    session_type: SessionType;
    session_subtype?: string;
    title: string;
    estimated_duration?: number;
    is_stacked: boolean;
  }[];
  logged_sessions: {
    id: string;
    session_type: SessionType;
    status: SessionStatus;
    overall_rpe?: number;
  }[];
}

export interface CalendarWeek {
  start_date: string;
  end_date: string;
  days: CalendarDay[];
}

// ── AI Usage ──────────────────────────────────────────────────────────────────
export interface AIUsageSummary {
  total_requests: number;
  successful_requests: number;
  total_tokens: number;
  total_cost_usd: number;
  by_model: Record<string, { requests: number; tokens: number; cost_usd: number }>;
  by_feature: Record<string, { requests: number; tokens: number; cost_usd: number }>;
}

// ── Offline Queue ─────────────────────────────────────────────────────────────
export interface OfflineQueueItem {
  id: string;
  created_at: string;
  sync_status: SyncStatus;
  action_type: string;
  payload: Record<string, unknown>;
  session_log_id?: string;
  error_message?: string;
  retry_count: number;
  synced_at?: string;
}
