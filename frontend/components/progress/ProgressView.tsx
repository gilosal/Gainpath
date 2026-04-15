"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { dashboardApi, aiUsageApi } from "@/lib/api";
import { cn, formatDistance, formatDuration } from "@/lib/utils";
import { StatCardSkeleton } from "@/components/common/SkeletonCard";
import { VolumeChart } from "./VolumeChart";
import { AIUsagePanel } from "./AIUsagePanel";
import { Activity, Dumbbell, PersonStanding, Brain } from "lucide-react";

type Tab = "overview" | "running" | "lifting" | "ai";

export function ProgressView() {
  const [tab, setTab] = useState<Tab>("overview");

  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ["dashboard", "summary"],
    queryFn: dashboardApi.summary,
  });
  const { data: runTrends } = useQuery({
    queryKey: ["trends", "running"],
    queryFn: () => dashboardApi.runningTrends(12),
    enabled: tab === "overview" || tab === "running",
  });
  const { data: liftTrends } = useQuery({
    queryKey: ["trends", "lifting"],
    queryFn: () => dashboardApi.liftingTrends(12),
    enabled: tab === "overview" || tab === "lifting",
  });
  const { data: mobTrends } = useQuery({
    queryKey: ["trends", "mobility"],
    queryFn: () => dashboardApi.mobilityTrends(12),
    enabled: tab === "overview",
  });

  const TABS = [
    { id: "overview" as Tab, label: "Overview", Icon: Activity },
    { id: "running"  as Tab, label: "Running",  Icon: Activity },
    { id: "lifting"  as Tab, label: "Lifting",  Icon: Dumbbell },
    { id: "ai"       as Tab, label: "AI Cost",  Icon: Brain },
  ];

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="sticky top-0 z-10 bg-background/95 backdrop-blur border-b border-border px-4 pt-4 pb-0">
        <h1 className="text-2xl font-bold text-foreground mb-3">Progress</h1>
        {/* Tab strip */}
        <div className="flex gap-1 overflow-x-auto pb-3 scrollbar-none">
          {TABS.map(({ id, label, Icon }) => (
            <button
              key={id}
              onClick={() => setTab(id)}
              className={cn(
                "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium whitespace-nowrap transition-colors flex-shrink-0",
                tab === id
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground bg-secondary active:bg-accent"
              )}
            >
              <Icon size={13} />
              {label}
            </button>
          ))}
        </div>
      </div>

      <div className="px-4 py-4 space-y-4">
        {/* ── Overview ── */}
        {tab === "overview" && (
          <>
            {/* This-week stat cards */}
            <div className="grid grid-cols-2 gap-3">
              {summaryLoading ? (
                <>
                  <StatCardSkeleton /><StatCardSkeleton />
                  <StatCardSkeleton /><StatCardSkeleton />
                </>
              ) : summary ? (
                <>
                  <StatCard
                    label="Running"
                    value={`${summary.running_km_this_week} km`}
                    sub="this week"
                    color="text-run"
                  />
                  <StatCard
                    label="Lifting"
                    value={`${(summary.lifting_tonnage_this_week / 1000).toFixed(1)} t`}
                    sub="tonnage this week"
                    color="text-lift"
                  />
                  <StatCard
                    label="Mobility"
                    value={`${summary.mobility_minutes_this_week} min`}
                    sub="this week"
                    color="text-mobility"
                  />
                  <StatCard
                    label="Sessions"
                    value={`${summary.sessions_completed_this_week}/${summary.sessions_planned_this_week}`}
                    sub="completed"
                    color="text-primary"
                  />
                </>
              ) : null}
            </div>

            {runTrends && runTrends.length > 0 && (
              <VolumeChart
                title="Weekly Running"
                data={runTrends}
                dataKey="km"
                color="#22c55e"
                unit=" km"
              />
            )}
            {liftTrends && liftTrends.length > 0 && (
              <VolumeChart
                title="Weekly Tonnage"
                data={liftTrends}
                dataKey="tonnage"
                color="#3b82f6"
                unit=" kg"
              />
            )}
            {mobTrends && mobTrends.length > 0 && (
              <VolumeChart
                title="Mobility Minutes"
                data={mobTrends}
                dataKey="minutes"
                color="#a855f7"
                unit=" min"
              />
            )}
          </>
        )}

        {/* ── Running ── */}
        {tab === "running" && runTrends && (
          <VolumeChart
            title="Weekly Mileage"
            data={runTrends}
            dataKey="km"
            color="#22c55e"
            unit=" km"
            height={280}
          />
        )}

        {/* ── Lifting ── */}
        {tab === "lifting" && liftTrends && (
          <VolumeChart
            title="Weekly Tonnage"
            data={liftTrends}
            dataKey="tonnage"
            color="#3b82f6"
            unit=" kg"
            height={280}
          />
        )}

        {/* ── AI Cost ── */}
        {tab === "ai" && <AIUsagePanel />}
      </div>
    </div>
  );
}

function StatCard({
  label,
  value,
  sub,
  color,
}: {
  label: string;
  value: string;
  sub: string;
  color: string;
}) {
  return (
    <div className="rounded-xl border border-border bg-card p-4">
      <p className="text-xs text-muted-foreground font-medium">{label}</p>
      <p className={cn("text-2xl font-black mt-1 tabular-nums", color)}>{value}</p>
      <p className="text-xs text-muted-foreground mt-0.5">{sub}</p>
    </div>
  );
}
