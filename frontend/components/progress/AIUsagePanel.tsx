"use client";

import { useQuery } from "@tanstack/react-query";
import { aiUsageApi } from "@/lib/api";
import { StatCardSkeleton } from "@/components/common/SkeletonCard";
import { cn } from "@/lib/utils";

export function AIUsagePanel() {
  const { data, isLoading } = useQuery({
    queryKey: ["ai-usage", "summary"],
    queryFn: () => aiUsageApi.summary(30),
  });

  if (isLoading) {
    return (
      <div className="grid grid-cols-2 gap-3">
        <StatCardSkeleton /><StatCardSkeleton />
        <StatCardSkeleton /><StatCardSkeleton />
      </div>
    );
  }
  if (!data) return null;

  return (
    <div className="space-y-4">
      {/* Summary cards */}
      <div className="grid grid-cols-2 gap-3">
        <div className="rounded-xl border border-border bg-card p-4">
          <p className="text-xs text-muted-foreground">Total Cost (30d)</p>
          <p className="text-2xl font-black text-foreground mt-1">
            ${data.total_cost_usd.toFixed(4)}
          </p>
        </div>
        <div className="rounded-xl border border-border bg-card p-4">
          <p className="text-xs text-muted-foreground">Requests</p>
          <p className="text-2xl font-black text-primary mt-1">{data.total_requests}</p>
          <p className="text-xs text-muted-foreground">{data.successful_requests} succeeded</p>
        </div>
        <div className="rounded-xl border border-border bg-card col-span-2 p-4">
          <p className="text-xs text-muted-foreground">Total Tokens</p>
          <p className="text-2xl font-black text-foreground mt-1">
            {(data.total_tokens / 1000).toFixed(1)}k
          </p>
        </div>
      </div>

      {/* By model */}
      {Object.keys(data.by_model).length > 0 && (
        <div className="rounded-xl border border-border bg-card p-4">
          <h3 className="text-sm font-semibold text-foreground mb-3">By Model</h3>
          <div className="space-y-2">
            {Object.entries(data.by_model).map(([model, stats]) => (
              <div key={model} className="flex items-center justify-between">
                <div className="min-w-0">
                  <p className="text-xs font-medium text-foreground truncate">{model}</p>
                  <p className="text-xs text-muted-foreground">{stats.requests} req · {(stats.tokens / 1000).toFixed(1)}k tok</p>
                </div>
                <span className="text-xs font-mono text-foreground flex-shrink-0 ml-2">
                  ${stats.cost_usd.toFixed(4)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* By feature */}
      {Object.keys(data.by_feature).length > 0 && (
        <div className="rounded-xl border border-border bg-card p-4">
          <h3 className="text-sm font-semibold text-foreground mb-3">By Feature</h3>
          <div className="space-y-2">
            {Object.entries(data.by_feature).map(([feature, stats]) => (
              <div key={feature} className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-medium text-foreground capitalize">
                    {feature.replace(/_/g, " ")}
                  </p>
                  <p className="text-xs text-muted-foreground">{stats.requests} requests</p>
                </div>
                <span className="text-xs font-mono text-foreground">${stats.cost_usd.toFixed(4)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
