"use client";

import { formatDate, sessionTypeColor, sessionTypeLabel, cn } from "@/lib/utils";
import type { CalendarDay } from "@/lib/types";
import { Clock, CheckCircle2 } from "lucide-react";

interface DayDetailProps {
  day: CalendarDay;
}

export function DayDetail({ day }: DayDetailProps) {
  const logMap = Object.fromEntries(
    day.logged_sessions.map((l) => [l.id, l])
  );

  if (day.planned_sessions.length === 0) {
    return (
      <div className="text-center py-10">
        <p className="text-2xl mb-2">🛋️</p>
        <p className="text-sm text-muted-foreground">Rest day — nothing planned</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
        {formatDate(day.date, { weekday: "long", month: "long", day: "numeric" })}
      </h2>

      {day.planned_sessions.map((session) => {
        const log = day.logged_sessions.find(
          (l) => l.status === "completed"
        );
        const isDone = !!log;

        return (
          <div
            key={session.id}
            className={cn(
              "rounded-xl border bg-card p-4 transition-opacity",
              isDone && "opacity-70"
            )}
          >
            <div className="flex items-start gap-3">
              <div
                className={cn(
                  "w-2 h-2 rounded-full mt-1.5 flex-shrink-0",
                  sessionTypeColor(session.session_type)
                    .split(" ")
                    .find((c) => c.startsWith("bg-")) ?? "bg-muted"
                )}
              />

              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <h3 className="font-semibold text-sm text-foreground">{session.title}</h3>
                  {isDone && (
                    <CheckCircle2 size={14} className="text-primary flex-shrink-0" />
                  )}
                </div>
                <div className="flex items-center gap-3 mt-1">
                  <span
                    className={cn(
                      "text-xs font-medium px-1.5 py-0.5 rounded border",
                      sessionTypeColor(session.session_type)
                    )}
                  >
                    {sessionTypeLabel(session.session_type)}
                  </span>
                  {session.estimated_duration && (
                    <span className="flex items-center gap-1 text-xs text-muted-foreground">
                      <Clock size={11} />
                      {session.estimated_duration} min
                    </span>
                  )}
                  {session.is_stacked && (
                    <span className="text-xs text-muted-foreground">Stacked</span>
                  )}
                </div>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
