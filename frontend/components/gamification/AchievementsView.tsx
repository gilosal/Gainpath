"use client";

import { useQuery } from "@tanstack/react-query";
import { Trophy } from "lucide-react";
import { gamificationApi } from "@/lib/api";
import { AchievementGrid } from "./AchievementGrid";
import { XPBar } from "./XPBar";
import { StreakBadge } from "./StreakBadge";

export function AchievementsView() {
  const { data: achievements } = useQuery({
    queryKey: ["achievements"],
    queryFn: gamificationApi.achievements,
  });

  const earnedCount = achievements?.filter((a) => a.earned).length ?? 0;
  const totalCount = achievements?.length ?? 0;

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="sticky top-0 z-10 bg-background/95 backdrop-blur border-b border-border px-4 pt-4 pb-3">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-foreground">Achievements</h1>
          <StreakBadge size="md" />
        </div>
        <p className="text-sm text-muted-foreground mt-0.5">
          {earnedCount} of {totalCount} unlocked
        </p>
        <div className="mt-2">
          <XPBar compact />
        </div>
      </div>

      {/* Content */}
      <div className="px-4 py-4">
        {totalCount === 0 ? (
          <div className="flex flex-col items-center py-16 text-center">
            <div className="p-4 bg-muted rounded-2xl mb-3">
              <Trophy size={28} className="text-muted-foreground" />
            </div>
            <p className="text-sm text-muted-foreground">Complete workouts to earn achievements!</p>
          </div>
        ) : (
          <AchievementGrid />
        )}
      </div>
    </div>
  );
}
