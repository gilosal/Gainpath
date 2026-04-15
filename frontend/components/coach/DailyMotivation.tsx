"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import { X, Sparkles } from "lucide-react";
import { coachingApi } from "@/lib/api";

interface DailyMotivationProps {
  className?: string;
}

export function DailyMotivation({ className }: DailyMotivationProps) {
  const qc = useQueryClient();
  const [dismissed, setDismissed] = useState(false);

  const { data: message } = useQuery({
    queryKey: ["coaching", "daily_motivation"],
    queryFn: () => coachingApi.latestMessage("daily_motivation"),
    staleTime: 5 * 60_000,
  });

  const dismissMutation = useMutation({
    mutationFn: (id: string) => coachingApi.dismissMessage(id),
    onSuccess: () => {
      setDismissed(true);
      qc.invalidateQueries({ queryKey: ["coaching"] });
    },
  });

  if (!message || dismissed) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: -8 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -8, height: 0 }}
        transition={{ duration: 0.3 }}
        className={className}
      >
        <div className="rounded-xl border border-primary/25 bg-primary/5 p-4">
          <div className="flex items-start gap-3">
            <div className="p-1.5 bg-primary/15 rounded-lg flex-shrink-0 mt-0.5">
              <Sparkles size={14} className="text-primary" />
            </div>
            <p className="flex-1 text-sm text-foreground leading-relaxed">{message.content}</p>
            <button
              onClick={() => dismissMutation.mutate(message.id)}
              className="text-muted-foreground hover:text-foreground flex-shrink-0 p-0.5"
            >
              <X size={14} />
            </button>
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
