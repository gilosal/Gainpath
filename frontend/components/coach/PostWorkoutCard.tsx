"use client";

import { motion, AnimatePresence } from "framer-motion";
import { Star, X, Zap, Flame } from "lucide-react";
import type { CoachingMessage } from "@/lib/types";
import { cn } from "@/lib/utils";

interface PostWorkoutCardProps {
  message: CoachingMessage;
  xpEarned?: number;
  streakCount?: number;
  onDismiss: () => void;
  className?: string;
}

export function PostWorkoutCard({
  message,
  xpEarned,
  streakCount,
  onDismiss,
  className,
}: PostWorkoutCardProps) {
  // Content format: "**Headline** Body text. Next suggestion."
  // We render it as plain text with mild formatting
  const lines = message.content.split("\n").filter(Boolean);
  const headline = lines[0]?.replace(/\*\*/g, "") ?? "Well done!";
  const body = lines.slice(1).join(" ").replace(/\*\*/g, "");

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 10 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95 }}
        transition={{ type: "spring", damping: 18, stiffness: 280 }}
        className={cn(
          "rounded-xl border border-primary/30 bg-gradient-to-b from-primary/10 to-primary/5 p-4",
          className
        )}
      >
        <div className="flex items-start justify-between mb-2">
          <div className="flex items-center gap-2">
            <div className="p-1.5 bg-primary/20 rounded-lg">
              <Star size={14} className="text-primary fill-primary" />
            </div>
            <h4 className="font-bold text-foreground text-sm">{headline}</h4>
          </div>
          <button onClick={onDismiss} className="text-muted-foreground hover:text-foreground p-0.5">
            <X size={14} />
          </button>
        </div>

        {body && <p className="text-sm text-muted-foreground leading-relaxed mb-3">{body}</p>}

        {/* Stats row */}
        <div className="flex items-center gap-3">
          {xpEarned !== undefined && xpEarned > 0 && (
            <div className="flex items-center gap-1 text-xs font-semibold text-yellow-400">
              <Zap size={11} fill="currentColor" />
              <span>+{xpEarned} XP</span>
            </div>
          )}
          {streakCount !== undefined && streakCount > 0 && (
            <div className="flex items-center gap-1 text-xs font-semibold text-orange-400">
              <Flame size={11} fill="currentColor" />
              <span>{streakCount} day streak</span>
            </div>
          )}
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
