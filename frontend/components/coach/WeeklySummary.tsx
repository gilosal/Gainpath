"use client";

import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { BarChart2, CheckCircle2, ChevronRight } from "lucide-react";
import { coachingApi } from "@/lib/api";
import { cn } from "@/lib/utils";

export function WeeklySummary() {
  const { data: message, isLoading } = useQuery({
    queryKey: ["coaching", "weekly_summary"],
    queryFn: () => coachingApi.latestMessage("weekly_summary"),
    staleTime: 10 * 60_000,
  });

  if (isLoading) {
    return <div className="rounded-xl bg-muted h-32 animate-pulse" />;
  }

  if (!message) {
    return (
      <div className="rounded-xl border border-dashed border-border p-8 text-center">
        <BarChart2 size={28} className="text-muted-foreground mx-auto mb-2" />
        <p className="text-sm font-medium text-foreground mb-1">No weekly summary yet</p>
        <p className="text-xs text-muted-foreground">
          Generated automatically each Sunday evening.
        </p>
      </div>
    );
  }

  // Parse content — format: **Headline**\n\n• Point\n• Point\n\nEncouragement\n**Next week focus:** ...
  const lines = message.content.split("\n").filter(Boolean);
  const headline = lines[0]?.replace(/\*\*/g, "") ?? "This Week";
  const bullets = lines.filter((l) => l.startsWith("•")).map((l) => l.replace("• ", ""));
  const nonBullets = lines.filter((l) => !l.startsWith("•") && l !== lines[0]);
  const encouragement = nonBullets.find((l) => !l.startsWith("**"))?.replace(/\*\*/g, "") ?? "";
  const focus = nonBullets.find((l) => l.startsWith("**Next week"))?.replace(/\*\*Next week focus:\*\* /, "");

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-xl border border-border bg-card p-5 space-y-3"
    >
      <div className="flex items-center gap-2">
        <div className="p-1.5 bg-primary/10 rounded-lg">
          <BarChart2 size={14} className="text-primary" />
        </div>
        <h3 className="font-bold text-foreground">{headline}</h3>
      </div>

      {bullets.length > 0 && (
        <div className="space-y-1.5">
          {bullets.map((b, i) => (
            <div key={i} className="flex items-start gap-2">
              <CheckCircle2 size={13} className="text-primary mt-0.5 flex-shrink-0" />
              <p className="text-sm text-foreground">{b}</p>
            </div>
          ))}
        </div>
      )}

      {encouragement && (
        <p className="text-sm text-muted-foreground italic">{encouragement}</p>
      )}

      {focus && (
        <div className="flex items-center gap-2 pt-1 border-t border-border">
          <ChevronRight size={13} className="text-primary flex-shrink-0" />
          <p className="text-sm text-foreground">
            <span className="font-medium">Next week: </span>
            {focus}
          </p>
        </div>
      )}
    </motion.div>
  );
}
