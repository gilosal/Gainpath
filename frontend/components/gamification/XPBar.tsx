"use client";

import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Zap } from "lucide-react";
import { gamificationApi } from "@/lib/api";
import { cn } from "@/lib/utils";

interface XPBarProps {
  className?: string;
  compact?: boolean;
}

export function XPBar({ className, compact = false }: XPBarProps) {
  const { data: xp } = useQuery({
    queryKey: ["xp"],
    queryFn: gamificationApi.xp,
    staleTime: 30_000,
  });

  if (!xp) return null;

  // XP needed for current level band
  const prevLevelXp = 100 * Math.pow(xp.level - 1, 2);
  const nextLevelXp = 100 * Math.pow(xp.level, 2);
  const bandXp = nextLevelXp - prevLevelXp;
  const progressXp = xp.total_xp - prevLevelXp;
  const pct = bandXp > 0 ? Math.min(100, (progressXp / bandXp) * 100) : 0;

  if (compact) {
    return (
      <div className={cn("flex items-center gap-2", className)}>
        <div className="flex items-center gap-1 text-xs text-yellow-400 font-medium">
          <Zap size={12} fill="currentColor" />
          <span>Lv.{xp.level}</span>
        </div>
        <div className="flex-1 h-1.5 bg-muted rounded-full overflow-hidden">
          <motion.div
            className="h-full bg-yellow-400 rounded-full"
            initial={{ width: 0 }}
            animate={{ width: `${pct}%` }}
            transition={{ duration: 0.6, ease: "easeOut" }}
          />
        </div>
      </div>
    );
  }

  return (
    <div className={cn("space-y-1.5", className)}>
      <div className="flex items-center justify-between text-xs">
        <div className="flex items-center gap-1.5 text-yellow-400 font-semibold">
          <Zap size={14} fill="currentColor" />
          <span>Level {xp.level}</span>
        </div>
        <span className="text-muted-foreground">
          {xp.xp_to_next_level} XP to next level
        </span>
      </div>
      <div className="h-2 bg-muted rounded-full overflow-hidden">
        <motion.div
          className="h-full bg-gradient-to-r from-yellow-500 to-yellow-300 rounded-full"
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.8, ease: "easeOut" }}
        />
      </div>
      <p className="text-xs text-muted-foreground text-right">{xp.total_xp.toLocaleString()} XP total</p>
    </div>
  );
}
