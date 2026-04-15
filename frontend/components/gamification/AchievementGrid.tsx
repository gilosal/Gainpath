"use client";

import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  Flame, Star, Trophy, Award, Medal, TrendingUp, Zap, MapPin, Dumbbell,
  Shuffle, Sunrise, Target, Footprints
} from "lucide-react";
import { gamificationApi } from "@/lib/api";
import { cn } from "@/lib/utils";
import type { Achievement } from "@/lib/types";

const ICON_MAP: Record<string, React.ElementType> = {
  Footprints,
  TrendingUp,
  Award,
  Trophy,
  Flame,
  Zap,
  Star,
  Medal,
  MapPin,
  Dumbbell,
  Shuffle,
  Sunrise,
  Target,
  ChartLine: TrendingUp,
};

function AchievementIcon({ name, size = 20 }: { name: string; size?: number }) {
  const Icon = ICON_MAP[name] ?? Star;
  return <Icon size={size} />;
}

interface AchievementGridProps {
  className?: string;
}

export function AchievementGrid({ className }: AchievementGridProps) {
  const { data: achievements, isLoading } = useQuery({
    queryKey: ["achievements"],
    queryFn: gamificationApi.achievements,
    staleTime: 60_000,
  });

  if (isLoading) {
    return (
      <div className={cn("grid grid-cols-3 gap-3", className)}>
        {Array.from({ length: 9 }).map((_, i) => (
          <div key={i} className="aspect-square rounded-xl bg-muted animate-pulse" />
        ))}
      </div>
    );
  }

  const earned = achievements?.filter((a) => a.earned) ?? [];
  const unearned = achievements?.filter((a) => !a.earned) ?? [];

  return (
    <div className={cn("space-y-4", className)}>
      {earned.length > 0 && (
        <div>
          <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">
            Earned ({earned.length})
          </p>
          <div className="grid grid-cols-3 gap-3">
            {earned.map((ach, i) => (
              <AchievementTile key={ach.id} achievement={ach} index={i} />
            ))}
          </div>
        </div>
      )}
      {unearned.length > 0 && (
        <div>
          <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">
            Locked ({unearned.length})
          </p>
          <div className="grid grid-cols-3 gap-3">
            {unearned.map((ach, i) => (
              <AchievementTile key={ach.id} achievement={ach} index={i} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function AchievementTile({ achievement, index }: { achievement: Achievement; index: number }) {
  const categoryColors: Record<string, string> = {
    streak: "from-orange-500/30 to-orange-600/20 border-orange-500/30 text-orange-400",
    volume: "from-blue-500/30 to-blue-600/20 border-blue-500/30 text-blue-400",
    consistency: "from-green-500/30 to-green-600/20 border-green-500/30 text-green-400",
    milestone: "from-yellow-500/30 to-yellow-600/20 border-yellow-500/30 text-yellow-400",
  };

  const colorClass = achievement.earned
    ? categoryColors[achievement.category] ?? "from-primary/20 to-primary/10 border-primary/30 text-primary"
    : "from-muted to-muted border-border text-muted-foreground/40";

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay: index * 0.03 }}
      className={cn(
        "flex flex-col items-center justify-center gap-1.5 p-3 rounded-xl border bg-gradient-to-b aspect-square",
        colorClass
      )}
      title={achievement.description}
    >
      <AchievementIcon name={achievement.icon_name} size={22} />
      <p className="text-[10px] font-medium text-center leading-tight line-clamp-2">
        {achievement.name}
      </p>
      {achievement.earned && (
        <span className="text-[9px] opacity-60">+{achievement.xp_reward} XP</span>
      )}
    </motion.div>
  );
}
