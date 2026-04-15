"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { dashboardApi } from "@/lib/api";
import { weekStart, addDays, toISODate, formatDate, formatDayShort, isToday, cn, sessionTypeDot } from "@/lib/utils";
import { SessionSkeletonCard } from "@/components/common/SkeletonCard";
import { WeekSlider } from "./WeekSlider";
import { DayDetail } from "./DayDetail";
import type { CalendarDay } from "@/lib/types";
import { ChevronLeft, ChevronRight } from "lucide-react";

export function CalendarView() {
  const [weekOffset, setWeekOffset] = useState(0);
  const [selectedDate, setSelectedDate] = useState(toISODate(new Date()));

  const start = addDays(weekStart(), weekOffset * 7);
  const startISO = toISODate(start);

  const { data: week, isLoading } = useQuery({
    queryKey: ["calendar", startISO],
    queryFn: () => dashboardApi.calendar(startISO),
  });

  const selectedDay = week?.days.find((d) => d.date === selectedDate) ?? null;

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="sticky top-0 z-10 bg-background/95 backdrop-blur border-b border-border px-4 pt-4 pb-0">
        <div className="flex items-center justify-between mb-3">
          <button
            onClick={() => setWeekOffset((o) => o - 1)}
            className="touch-target text-muted-foreground"
            aria-label="Previous week"
          >
            <ChevronLeft size={20} />
          </button>
          <div className="text-center">
            <h1 className="text-base font-semibold text-foreground">
              {formatDate(startISO, { month: "long", year: "numeric" })}
            </h1>
            {weekOffset !== 0 && (
              <button
                onClick={() => { setWeekOffset(0); setSelectedDate(toISODate(new Date())); }}
                className="text-xs text-primary underline"
              >
                Back to this week
              </button>
            )}
          </div>
          <button
            onClick={() => setWeekOffset((o) => o + 1)}
            className="touch-target text-muted-foreground"
            aria-label="Next week"
          >
            <ChevronRight size={20} />
          </button>
        </div>

        {/* Day strip */}
        <div className="flex gap-1 pb-3">
          {week?.days.map((day) => (
            <DayChip
              key={day.date}
              day={day}
              isSelected={day.date === selectedDate}
              onSelect={() => setSelectedDate(day.date)}
            />
          )) ??
            Array.from({ length: 7 }, (_, i) => {
              const d = toISODate(addDays(start, i));
              return <DayChipSkeleton key={d} />;
            })}
        </div>
      </div>

      {/* Day detail */}
      <div className="px-4 py-4">
        {isLoading ? (
          <div className="space-y-3">
            <SessionSkeletonCard />
            <SessionSkeletonCard />
          </div>
        ) : selectedDay ? (
          <DayDetail day={selectedDay} />
        ) : (
          <p className="text-center text-muted-foreground text-sm py-8">
            No data for this day.
          </p>
        )}
      </div>
    </div>
  );
}

function DayChip({
  day,
  isSelected,
  onSelect,
}: {
  day: CalendarDay;
  isSelected: boolean;
  onSelect: () => void;
}) {
  const today = isToday(day.date);
  const hasSession = day.planned_sessions.length > 0;
  const allDone =
    hasSession &&
    day.logged_sessions.length >= day.planned_sessions.length &&
    day.logged_sessions.every((s) => s.status === "completed");

  return (
    <button
      onClick={onSelect}
      className={cn(
        "flex-1 flex flex-col items-center py-2 rounded-xl transition-all duration-150 touch-target",
        isSelected
          ? "bg-primary text-primary-foreground"
          : today
          ? "bg-primary/15 text-primary"
          : "text-muted-foreground active:bg-secondary"
      )}
    >
      <span className="text-[10px] font-medium uppercase">{formatDayShort(day.date).slice(0, 2)}</span>
      <span className={cn("text-sm font-bold mt-0.5", today && !isSelected && "text-primary")}>
        {new Date(day.date + "T12:00:00").getDate()}
      </span>
      {/* Session type dots */}
      <div className="flex gap-0.5 mt-1 h-1.5">
        {day.planned_sessions.slice(0, 3).map((s, i) => (
          <div
            key={i}
            className={cn(
              "w-1.5 h-1.5 rounded-full",
              isSelected ? "bg-primary-foreground/60" : sessionTypeDot(s.session_type)
            )}
          />
        ))}
        {allDone && !isSelected && (
          <div className="w-1.5 h-1.5 rounded-full bg-primary" />
        )}
      </div>
    </button>
  );
}

function DayChipSkeleton() {
  return (
    <div className="flex-1 flex flex-col items-center py-2 gap-1">
      <div className="skeleton w-5 h-2.5 rounded" />
      <div className="skeleton w-5 h-4 rounded" />
    </div>
  );
}

// WeekSlider is a horizontal swipeable version used on mobile (exported for use)
export { WeekSlider };
