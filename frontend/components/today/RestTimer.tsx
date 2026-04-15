"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { cn, formatDuration } from "@/lib/utils";

interface RestTimerProps {
  seconds: number;
  onDone: () => void;
  onSkip: () => void;
}

export function RestTimer({ seconds, onDone, onSkip }: RestTimerProps) {
  const [remaining, setRemaining] = useState(seconds);
  const [addedTime, setAddedTime] = useState(0);
  const total = seconds + addedTime;
  const progress = remaining / total;

  useEffect(() => {
    if (remaining <= 0) {
      onDone();
      return;
    }
    const id = setInterval(() => setRemaining((r) => r - 1), 1000);
    return () => clearInterval(id);
  }, [remaining, onDone]);

  const circumference = 2 * Math.PI * 56;

  return (
    <motion.div
      className="absolute inset-0 z-20 bg-background/97 flex flex-col items-center justify-center gap-6"
      initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
    >
      <p className="text-sm font-medium text-muted-foreground uppercase tracking-widest">
        Rest
      </p>

      {/* Circular progress */}
      <div className="relative w-36 h-36 flex items-center justify-center">
        {/* Pulse ring */}
        <div className="absolute inset-0 rounded-full border-2 border-primary/20 ring-pulse" />

        <svg className="absolute inset-0 w-full h-full -rotate-90" viewBox="0 0 128 128">
          {/* Track */}
          <circle cx="64" cy="64" r="56" fill="none" stroke="hsl(var(--muted))" strokeWidth="6" />
          {/* Progress */}
          <circle
            cx="64" cy="64" r="56"
            fill="none"
            stroke="hsl(var(--primary))"
            strokeWidth="6"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={circumference * (1 - progress)}
            className="transition-all duration-1000 ease-linear"
          />
        </svg>

        <div className="relative text-center">
          <span className={cn("text-4xl font-black tabular-nums", remaining <= 5 && "text-red-400")}>
            {remaining}
          </span>
          <p className="text-xs text-muted-foreground">sec</p>
        </div>
      </div>

      {/* +30s / Skip */}
      <div className="flex gap-3">
        <button
          onClick={() => {
            setAddedTime((a) => a + 30);
            setRemaining((r) => r + 30);
          }}
          className="px-5 py-2.5 rounded-xl bg-secondary text-secondary-foreground text-sm font-medium touch-target active:scale-95 transition-transform"
        >
          +30s
        </button>
        <button
          onClick={onSkip}
          className="px-5 py-2.5 rounded-xl bg-primary text-primary-foreground text-sm font-semibold touch-target active:scale-95 transition-transform"
        >
          Skip Rest
        </button>
      </div>
    </motion.div>
  );
}
