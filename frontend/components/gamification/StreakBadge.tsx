"use client";

import { useQuery } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import { Flame } from "lucide-react";
import { gamificationApi } from "@/lib/api";
import { cn } from "@/lib/utils";

interface StreakBadgeProps {
  size?: "sm" | "md" | "lg";
  className?: string;
}

export function StreakBadge({ size = "md", className }: StreakBadgeProps) {
  const { data: streak } = useQuery({
    queryKey: ["streak"],
    queryFn: gamificationApi.streak,
    staleTime: 60_000,
  });

  const current = streak?.current_streak ?? 0;

  if (current === 0) return null;

  const sizeClasses = {
    sm: "text-xs gap-0.5 px-1.5 py-0.5",
    md: "text-sm gap-1 px-2 py-1",
    lg: "text-base gap-1.5 px-3 py-1.5",
  };
  const iconSize = { sm: 12, md: 14, lg: 18 }[size];

  const isHot = current >= 7;

  return (
    <AnimatePresence>
      <motion.div
        key={current}
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.8, opacity: 0 }}
        className={cn(
          "inline-flex items-center rounded-full font-semibold",
          sizeClasses[size],
          isHot
            ? "bg-orange-500/20 text-orange-400 border border-orange-500/30"
            : "bg-yellow-500/15 text-yellow-400 border border-yellow-500/25",
          className
        )}
      >
        <motion.div
          animate={isHot ? { rotate: [-5, 5, -5] } : {}}
          transition={{ repeat: Infinity, duration: 1.5 }}
        >
          <Flame size={iconSize} fill="currentColor" />
        </motion.div>
        <span>{current}</span>
      </motion.div>
    </AnimatePresence>
  );
}
