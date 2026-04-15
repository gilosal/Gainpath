"use client";

import { useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Medal, TrendingUp, X } from "lucide-react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { gamificationApi } from "@/lib/api";
import type { PersonalRecord } from "@/lib/types";

interface PRCelebrationProps {
  prs: PersonalRecord[];
  onClose: () => void;
}

function formatRecordType(type: string): string {
  const labels: Record<string, string> = {
    weight_1rm: "Estimated 1RM",
    max_weight: "Max Weight",
    max_reps: "Max Reps",
    longest_distance: "Longest Distance",
    fastest_pace: "Fastest Pace",
  };
  return labels[type] ?? type.replace(/_/g, " ");
}

function formatValue(pr: PersonalRecord): string {
  if (pr.record_type === "fastest_pace") {
    // Value is min/km — format as M:SS
    const mins = Math.floor(pr.value);
    const secs = Math.round((pr.value - mins) * 60);
    return `${mins}:${secs.toString().padStart(2, "0")}/km`;
  }
  if (pr.record_type === "longest_distance") {
    return `${pr.value.toFixed(2)} km`;
  }
  return `${pr.value.toFixed(1)} kg`;
}

export function PRCelebration({ prs, onClose }: PRCelebrationProps) {
  const qc = useQueryClient();
  const celebrateMutation = useMutation({
    mutationFn: (prId: string) => gamificationApi.celebratePr(prId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["prs"] }),
  });

  useEffect(() => {
    // Mark all as celebrated
    prs.forEach((pr) => {
      if (!pr.celebrated) {
        celebrateMutation.mutate(pr.id);
      }
    });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex items-end justify-center bg-black/70 backdrop-blur-sm p-4"
        onClick={onClose}
      >
        <motion.div
          initial={{ y: 100, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: 100, opacity: 0 }}
          transition={{ type: "spring", damping: 20, stiffness: 300 }}
          className="w-full max-w-sm bg-card border border-primary/40 rounded-2xl p-6 shadow-2xl"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center gap-2">
              <div className="p-2 bg-yellow-500/20 rounded-xl border border-yellow-500/30">
                <Medal size={20} className="text-yellow-400" />
              </div>
              <div>
                <h3 className="font-bold text-foreground">
                  {prs.length === 1 ? "New Personal Record!" : `${prs.length} New Records!`}
                </h3>
                <p className="text-xs text-muted-foreground">You crushed it 💪</p>
              </div>
            </div>
            <button onClick={onClose} className="text-muted-foreground hover:text-foreground p-1">
              <X size={18} />
            </button>
          </div>

          {/* PR list */}
          <div className="space-y-2 mb-4">
            {prs.map((pr) => (
              <motion.div
                key={pr.id}
                initial={{ x: -20, opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                className="flex items-center justify-between p-3 bg-muted/50 rounded-xl"
              >
                <div>
                  <p className="font-medium text-foreground text-sm">{pr.exercise_name}</p>
                  <p className="text-xs text-muted-foreground">{formatRecordType(pr.record_type)}</p>
                </div>
                <div className="text-right">
                  <div className="flex items-center gap-1 text-primary font-bold text-sm">
                    <TrendingUp size={13} />
                    <span>{formatValue(pr)}</span>
                  </div>
                  {pr.previous_value && (
                    <p className="text-xs text-muted-foreground line-through">
                      prev: {formatValue({ ...pr, value: pr.previous_value })}
                    </p>
                  )}
                </div>
              </motion.div>
            ))}
          </div>

          <button
            onClick={onClose}
            className="w-full bg-primary text-primary-foreground rounded-xl py-3 font-semibold text-sm transition-transform active:scale-95"
          >
            Awesome!
          </button>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
