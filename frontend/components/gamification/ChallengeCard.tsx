"use client";

import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Target, Zap } from "lucide-react";
import { gamificationApi } from "@/lib/api";
import { cn } from "@/lib/utils";
import type { WeeklyChallenge } from "@/lib/types";

interface ChallengeCardProps {
  className?: string;
}

export function ChallengeCard({ className }: ChallengeCardProps) {
  const { data: challenges } = useQuery({
    queryKey: ["challenges"],
    queryFn: gamificationApi.challenges,
    staleTime: 60_000,
  });

  const active = challenges?.find((c) => c.status === "active");
  if (!active) return null;

  return <ActiveChallengeCard challenge={active} className={className} />;
}

function ActiveChallengeCard({
  challenge,
  className,
}: {
  challenge: WeeklyChallenge;
  className?: string;
}) {
  const isComplete = challenge.progress_pct >= 100;

  return (
    <div
      className={cn(
        "rounded-xl border bg-card p-4",
        isComplete ? "border-primary/40" : "border-border",
        className
      )}
    >
      <div className="flex items-start gap-3">
        <div
          className={cn(
            "p-2 rounded-lg border flex-shrink-0",
            isComplete
              ? "bg-primary/10 border-primary/30 text-primary"
              : "bg-muted border-border text-muted-foreground"
          )}
        >
          <Target size={16} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
              Weekly Challenge
            </p>
            {isComplete && (
              <span className="text-xs font-semibold text-primary bg-primary/10 px-1.5 py-0.5 rounded-full">
                Complete!
              </span>
            )}
          </div>
          <h4 className="font-semibold text-foreground text-sm mt-0.5">{challenge.title}</h4>
          <p className="text-xs text-muted-foreground mt-0.5">{challenge.description}</p>

          {/* Progress bar */}
          <div className="mt-2 space-y-1">
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>{challenge.current_value.toFixed(challenge.target_value % 1 === 0 ? 0 : 1)}</span>
              <span>{challenge.target_value.toFixed(challenge.target_value % 1 === 0 ? 0 : 1)}</span>
            </div>
            <div className="h-1.5 bg-muted rounded-full overflow-hidden">
              <motion.div
                className={cn(
                  "h-full rounded-full",
                  isComplete ? "bg-primary" : "bg-blue-500"
                )}
                initial={{ width: 0 }}
                animate={{ width: `${challenge.progress_pct}%` }}
                transition={{ duration: 0.6, ease: "easeOut" }}
              />
            </div>
          </div>
        </div>

        <div className="flex items-center gap-1 text-xs font-semibold text-yellow-400 flex-shrink-0">
          <Zap size={12} fill="currentColor" />
          <span>+{challenge.xp_reward}</span>
        </div>
      </div>
    </div>
  );
}
