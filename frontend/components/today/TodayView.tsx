"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { sessionsApi, plansApi } from "@/lib/api";
import { todayISO, formatDate, sessionTypeColor, sessionTypeLabel, cn } from "@/lib/utils";
import { PlanGeneratingSkeleton, SessionSkeletonCard } from "@/components/common/SkeletonCard";
import { ActiveWorkout } from "./ActiveWorkout";
import { QuickLogSheet } from "./QuickLogSheet";
import type { SessionLog } from "@/lib/types";
import { Play, CheckCircle2, SkipForward, Plus, Dumbbell, PersonStanding, Timer } from "lucide-react";

const SESSION_ICONS: Record<string, React.ElementType> = {
  running: Timer,
  lifting: Dumbbell,
  mobility: PersonStanding,
};

export function TodayView() {
  const qc = useQueryClient();
  const [activeSession, setActiveSession] = useState<SessionLog | null>(null);
  const [logSheet, setLogSheet] = useState<SessionLog | null>(null);

  const { data: sessions, isLoading } = useQuery({
    queryKey: ["sessions", "today"],
    queryFn: sessionsApi.today,
    refetchOnMount: true,
  });

  const completeMutation = useMutation({
    mutationFn: ({ id, rpe }: { id: string; rpe: number }) =>
      sessionsApi.update(id, {
        status: "completed",
        overall_rpe: rpe,
        completed_at: new Date().toISOString(),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["sessions", "today"] }),
  });

  const skipMutation = useMutation({
    mutationFn: (id: string) => sessionsApi.update(id, { status: "skipped" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["sessions", "today"] }),
  });

  if (activeSession) {
    return (
      <ActiveWorkout
        session={activeSession}
        onClose={() => setActiveSession(null)}
        onComplete={(rpe) => {
          completeMutation.mutate({ id: activeSession.id, rpe });
          setActiveSession(null);
        }}
      />
    );
  }

  const today = todayISO();
  const completedCount = sessions?.filter((s) => s.status === "completed").length ?? 0;
  const totalCount = sessions?.length ?? 0;

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="sticky top-0 z-10 bg-background/95 backdrop-blur border-b border-border px-4 pt-4 pb-3">
        <p className="text-xs text-muted-foreground font-medium uppercase tracking-wider">
          {formatDate(today, { weekday: "long", month: "long", day: "numeric" })}
        </p>
        <div className="flex items-end justify-between mt-0.5">
          <h1 className="text-2xl font-bold text-foreground">Today</h1>
          {totalCount > 0 && (
            <span className="text-sm text-muted-foreground">
              {completedCount}/{totalCount} done
            </span>
          )}
        </div>
        {/* Progress bar */}
        {totalCount > 0 && (
          <div className="mt-2 h-1 bg-muted rounded-full overflow-hidden">
            <div
              className="h-full bg-primary rounded-full transition-all duration-500"
              style={{ width: `${(completedCount / totalCount) * 100}%` }}
            />
          </div>
        )}
      </div>

      {/* Content */}
      <div className="px-4 py-4 space-y-3">
        {isLoading ? (
          <>
            <SessionSkeletonCard />
            <SessionSkeletonCard />
          </>
        ) : sessions && sessions.length > 0 ? (
          sessions.map((session) => (
            <SessionCard
              key={session.id}
              session={session}
              onStart={() => setActiveSession(session)}
              onQuickLog={() => setLogSheet(session)}
              onSkip={() => skipMutation.mutate(session.id)}
            />
          ))
        ) : (
          <RestDayCard />
        )}
      </div>

      {/* Quick log sheet */}
      {logSheet && (
        <QuickLogSheet
          session={logSheet}
          open={!!logSheet}
          onClose={() => setLogSheet(null)}
        />
      )}
    </div>
  );
}

// ── Session Card ──────────────────────────────────────────────────────────────

function SessionCard({
  session,
  onStart,
  onQuickLog,
  onSkip,
}: {
  session: SessionLog;
  onStart: () => void;
  onQuickLog: () => void;
  onSkip: () => void;
}) {
  const Icon = SESSION_ICONS[session.session_type] ?? Dumbbell;
  const colorClass = sessionTypeColor(session.session_type);
  const isCompleted = session.status === "completed";
  const isSkipped = session.status === "skipped";

  return (
    <div
      className={cn(
        "rounded-xl border bg-card p-4 transition-all duration-200",
        isCompleted ? "border-primary/40 opacity-75" : "border-border",
        isSkipped && "opacity-50"
      )}
    >
      <div className="flex items-start gap-3">
        {/* Icon badge */}
        <div className={cn("p-2.5 rounded-lg flex-shrink-0 border", colorClass)}>
          <Icon size={18} />
        </div>

        {/* Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="font-semibold text-foreground text-sm leading-tight truncate">
              {/* We'd fetch the PlannedSession title — use session_type as fallback */}
              {sessionTypeLabel(session.session_type)} Session
            </h3>
            {isCompleted && <CheckCircle2 size={15} className="text-primary flex-shrink-0" />}
          </div>
          <p className="text-xs text-muted-foreground mt-0.5">
            {session.session_type === "running" && session.actual_distance
              ? `${session.actual_distance} km logged`
              : session.session_type === "lifting" && session.total_tonnage
              ? `${session.total_tonnage.toFixed(0)} kg total`
              : "Tap to start"}
          </p>
        </div>

        {/* Status badge */}
        {isCompleted && (
          <span className="text-xs font-medium text-primary bg-primary/10 px-2 py-0.5 rounded-full flex-shrink-0">
            Done
          </span>
        )}
        {isSkipped && (
          <span className="text-xs font-medium text-muted-foreground bg-muted px-2 py-0.5 rounded-full flex-shrink-0">
            Skipped
          </span>
        )}
      </div>

      {/* Actions — only show if not done/skipped */}
      {!isCompleted && !isSkipped && (
        <div className="flex gap-2 mt-3 pt-3 border-t border-border">
          <button
            onClick={onStart}
            className="flex-1 flex items-center justify-center gap-1.5 bg-primary text-primary-foreground rounded-lg py-2.5 text-sm font-semibold touch-target transition-transform active:scale-95"
          >
            <Play size={15} fill="currentColor" />
            Start
          </button>
          <button
            onClick={onQuickLog}
            className="flex items-center justify-center gap-1.5 bg-secondary text-secondary-foreground rounded-lg px-3 py-2.5 text-sm font-medium touch-target transition-transform active:scale-95"
          >
            <Plus size={15} />
            Log
          </button>
          <button
            onClick={onSkip}
            className="flex items-center justify-center text-muted-foreground rounded-lg px-3 py-2.5 touch-target transition-transform active:scale-95"
            aria-label="Skip session"
          >
            <SkipForward size={15} />
          </button>
        </div>
      )}
    </div>
  );
}

function RestDayCard() {
  return (
    <div className="rounded-xl border border-dashed border-border bg-card/50 p-8 text-center">
      <div className="text-4xl mb-3">🛋️</div>
      <h3 className="font-semibold text-foreground mb-1">Rest Day</h3>
      <p className="text-sm text-muted-foreground">
        No sessions scheduled. Recovery is part of training.
      </p>
    </div>
  );
}
