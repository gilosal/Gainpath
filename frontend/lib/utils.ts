import type { SessionType } from "./types";

// ── Date helpers ──────────────────────────────────────────────────────────────

export function toISODate(d: Date): string {
  return d.toISOString().split("T")[0];
}

export function todayISO(): string {
  return toISODate(new Date());
}

/** Monday of the week containing `date` */
export function weekStart(date: Date = new Date()): Date {
  const d = new Date(date);
  const day = d.getDay();
  const diff = day === 0 ? -6 : 1 - day; // ISO week starts Monday
  d.setDate(d.getDate() + diff);
  d.setHours(0, 0, 0, 0);
  return d;
}

export function addDays(date: Date, days: number): Date {
  const d = new Date(date);
  d.setDate(d.getDate() + days);
  return d;
}

export function formatDate(iso: string, opts?: Intl.DateTimeFormatOptions): string {
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    ...opts,
  });
}

export function formatDayShort(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", { weekday: "short" });
}

export function isToday(iso: string): boolean {
  return iso === todayISO();
}

// ── Duration ──────────────────────────────────────────────────────────────────

/** Formats seconds → "1h 23m" or "45m 30s" */
export function formatDuration(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  if (h > 0) return `${h}h ${m}m`;
  if (m > 0) return s > 0 ? `${m}m ${s}s` : `${m}m`;
  return `${s}s`;
}

/** Formats a pace float (min/km) → "5:30/km" */
export function formatPace(pace: number, unit: "km" | "mi" = "km"): string {
  const min = Math.floor(pace);
  const sec = Math.round((pace - min) * 60);
  return `${min}:${sec.toString().padStart(2, "0")}/${unit}`;
}

// ── Session type helpers ──────────────────────────────────────────────────────

export function sessionTypeColor(type: SessionType): string {
  switch (type) {
    case "running":  return "text-run bg-run/10 border-run/30";
    case "lifting":  return "text-lift bg-lift/10 border-lift/30";
    case "mobility": return "text-mobility bg-mobility/10 border-mobility/30";
    default:         return "text-muted-foreground bg-muted border-border";
  }
}

export function sessionTypeDot(type: SessionType): string {
  switch (type) {
    case "running":  return "bg-run";
    case "lifting":  return "bg-lift";
    case "mobility": return "bg-mobility";
    default:         return "bg-muted-foreground";
  }
}

export function sessionTypeLabel(type: SessionType): string {
  switch (type) {
    case "running":  return "Run";
    case "lifting":  return "Lift";
    case "mobility": return "Mobility";
    default:         return "Rest";
  }
}

// ── RPE ───────────────────────────────────────────────────────────────────────

export function rpeColor(rpe: number): string {
  if (rpe <= 5) return "text-green-400";
  if (rpe <= 7) return "text-yellow-400";
  if (rpe <= 8) return "text-orange-400";
  return "text-red-400";
}

export function rpeLabel(rpe: number): string {
  if (rpe <= 4) return "Easy";
  if (rpe <= 6) return "Moderate";
  if (rpe <= 7) return "Comfortably Hard";
  if (rpe <= 8) return "Hard";
  if (rpe <= 9) return "Very Hard";
  return "Max Effort";
}

// ── Number formatting ─────────────────────────────────────────────────────────

export function formatWeight(kg: number, unit: "kg" | "lb"): string {
  if (unit === "lb") return `${Math.round(kg * 2.20462)} lb`;
  return `${kg} kg`;
}

export function formatDistance(km: number, unit: "km" | "mi"): string {
  if (unit === "mi") return `${(km * 0.621371).toFixed(2)} mi`;
  return `${km.toFixed(2)} km`;
}

// ── cn (class name helper — minimal clsx replacement) ─────────────────────────

export function cn(...classes: (string | undefined | false | null)[]): string {
  return classes.filter(Boolean).join(" ");
}
