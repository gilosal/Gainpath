"use client";

import { useState, useCallback } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import { sessionsApi } from "@/lib/api";
import { logSetWithFallback } from "@/lib/offline-queue";
import { cn, rpeColor, rpeLabel } from "@/lib/utils";
import { RestTimer } from "./RestTimer";
import type { SessionLog, ExerciseBlock } from "@/lib/types";
import { X, Check, Minus, Plus } from "lucide-react";

interface ActiveWorkoutProps {
  session: SessionLog;
  onClose: () => void;
  onComplete: (rpe: number) => void;
}

interface SetState {
  weight: number;
  reps: number;
  logged: boolean;
}

export function ActiveWorkout({ session, onClose, onComplete }: ActiveWorkoutProps) {
  const qc = useQueryClient();

  // Parse exercises from planned session (passed via session.sets or exercises field)
  const exercises: ExerciseBlock[] = (session as unknown as { exercises?: ExerciseBlock[] }).exercises ?? [];
  const [exerciseIdx, setExerciseIdx] = useState(0);
  const [setIdx, setSetIdx] = useState(0);
  const [sets, setSets] = useState<SetState[][]>(
    exercises.map((ex) =>
      Array.from({ length: ex.sets }, () => ({ weight: 0, reps: 0, logged: false }))
    )
  );
  const [resting, setResting] = useState(false);
  const [restSeconds, setRestSeconds] = useState(90);
  const [showRPE, setShowRPE] = useState(false);
  const [sessionRPE, setSessionRPE] = useState(7);

  const currentExercise = exercises[exerciseIdx];
  const currentSet = sets[exerciseIdx]?.[setIdx];

  const updateField = useCallback(
    (field: "weight" | "reps", delta: number) => {
      setSets((prev) => {
        const next = prev.map((exSets) => [...exSets]);
        const s = { ...next[exerciseIdx][setIdx] };
        if (field === "weight") s.weight = Math.max(0, s.weight + delta);
        if (field === "reps") s.reps = Math.max(0, s.reps + delta);
        next[exerciseIdx][setIdx] = s;
        return next;
      });
    },
    [exerciseIdx, setIdx]
  );

  const logCurrentSet = useCallback(async () => {
    if (!currentExercise || !currentSet) return;
    const payload = {
      exercise_name: currentExercise.exercise_name,
      set_number: setIdx + 1,
      set_type: "working" as const,
      weight: currentSet.weight,
      reps: currentSet.reps,
    };
    await logSetWithFallback(session.id, payload, () =>
      sessionsApi.addSet(session.id, payload)
    );
    setSets((prev) => {
      const next = prev.map((exSets) => [...exSets]);
      next[exerciseIdx][setIdx] = { ...next[exerciseIdx][setIdx], logged: true };
      return next;
    });
    qc.invalidateQueries({ queryKey: ["sessions", session.id] });

    // Advance set or exercise, trigger rest timer
    const isLastSet = setIdx >= (currentExercise.sets - 1);
    const isLastExercise = exerciseIdx >= exercises.length - 1;

    if (isLastSet && isLastExercise) {
      setShowRPE(true);
    } else if (isLastSet) {
      setExerciseIdx((i) => i + 1);
      setSetIdx(0);
      setResting(true);
      setRestSeconds(currentExercise.rest_seconds ?? 90);
    } else {
      setSetIdx((i) => i + 1);
      setResting(true);
      setRestSeconds(currentExercise.rest_seconds ?? 90);
    }
  }, [currentExercise, currentSet, exerciseIdx, exercises.length, session.id, setIdx, qc]);

  if (exercises.length === 0) {
    return (
      <div className="fixed inset-0 z-50 bg-background flex flex-col items-center justify-center gap-4 p-6">
        <p className="text-muted-foreground text-center">No exercise data for this session.</p>
        <button onClick={onClose} className="text-primary underline">Go back</button>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-50 bg-background flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-4 pt-safe pt-4 pb-3 border-b border-border flex-shrink-0">
        <button
          onClick={onClose}
          className="touch-target text-muted-foreground"
          aria-label="Close workout"
        >
          <X size={22} />
        </button>
        <div className="text-center">
          <p className="text-xs text-muted-foreground font-medium">
            Exercise {exerciseIdx + 1}/{exercises.length}
          </p>
          <p className="text-sm font-semibold text-foreground">
            Set {setIdx + 1}/{currentExercise?.sets ?? 1}
          </p>
        </div>
        {/* Progress dots */}
        <div className="flex gap-1">
          {exercises.map((_, i) => (
            <div
              key={i}
              className={cn(
                "w-1.5 h-1.5 rounded-full transition-colors",
                i < exerciseIdx
                  ? "bg-primary"
                  : i === exerciseIdx
                  ? "bg-primary/60"
                  : "bg-muted"
              )}
            />
          ))}
        </div>
      </div>

      {/* Rest timer overlay */}
      <AnimatePresence>
        {resting && (
          <RestTimer
            seconds={restSeconds}
            onDone={() => setResting(false)}
            onSkip={() => setResting(false)}
          />
        )}
      </AnimatePresence>

      {/* RPE selector overlay */}
      <AnimatePresence>
        {showRPE && (
          <motion.div
            className="absolute inset-0 z-10 bg-background/95 flex flex-col items-center justify-center gap-6 p-6"
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
          >
            <h2 className="text-xl font-bold text-foreground">How was that session?</h2>
            <p className={cn("text-5xl font-black", rpeColor(sessionRPE))}>{sessionRPE}</p>
            <p className="text-sm text-muted-foreground">{rpeLabel(sessionRPE)}</p>
            <input
              type="range" min={1} max={10} value={sessionRPE}
              onChange={(e) => setSessionRPE(Number(e.target.value))}
              className="w-full accent-primary"
            />
            <div className="flex justify-between w-full text-xs text-muted-foreground px-1">
              <span>Very Easy</span><span>Max Effort</span>
            </div>
            <button
              onClick={() => onComplete(sessionRPE)}
              className="w-full bg-primary text-primary-foreground rounded-xl py-4 text-base font-bold touch-target active:scale-95 transition-transform"
            >
              Complete Session
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main exercise area */}
      <div className="flex-1 flex flex-col items-center justify-center px-6 gap-6">
        <AnimatePresence mode="wait">
          <motion.h2
            key={exerciseIdx}
            className="text-2xl font-bold text-center text-foreground leading-tight"
            initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }}
          >
            {currentExercise?.exercise_name}
          </motion.h2>
        </AnimatePresence>

        {currentExercise && (
          <p className="text-sm text-muted-foreground text-center">
            {currentExercise.sets} × {currentExercise.reps}
            {currentExercise.rpe && ` @ RPE ${currentExercise.rpe}`}
          </p>
        )}

        {/* Weight counter */}
        <div className="w-full space-y-4">
          <CounterRow
            label="Weight (kg)"
            value={currentSet?.weight ?? 0}
            step={2.5}
            onDecrement={() => updateField("weight", -2.5)}
            onIncrement={() => updateField("weight", 2.5)}
          />
          <CounterRow
            label="Reps"
            value={currentSet?.reps ?? 0}
            step={1}
            onDecrement={() => updateField("reps", -1)}
            onIncrement={() => updateField("reps", 1)}
          />
        </div>
      </div>

      {/* Log button */}
      <div className="px-4 pb-safe pb-6 flex-shrink-0">
        <button
          onClick={logCurrentSet}
          className="w-full bg-primary text-primary-foreground rounded-2xl py-5 text-lg font-bold flex items-center justify-center gap-2 touch-target active:scale-95 transition-transform shadow-lg"
        >
          <Check size={22} strokeWidth={3} />
          Log Set
        </button>
      </div>
    </div>
  );
}

function CounterRow({
  label, value, step, onDecrement, onIncrement,
}: {
  label: string;
  value: number;
  step: number;
  onDecrement: () => void;
  onIncrement: () => void;
}) {
  return (
    <div className="flex items-center justify-between bg-card rounded-xl border border-border p-4">
      <span className="text-sm text-muted-foreground w-28">{label}</span>
      <div className="flex items-center gap-4">
        <button
          onClick={onDecrement}
          className="w-11 h-11 rounded-xl bg-secondary flex items-center justify-center touch-target active:scale-90 transition-transform"
        >
          <Minus size={18} />
        </button>
        <span className="text-2xl font-bold text-foreground w-16 text-center tabular-nums">
          {value % 1 === 0 ? value : value.toFixed(1)}
        </span>
        <button
          onClick={onIncrement}
          className="w-11 h-11 rounded-xl bg-primary text-primary-foreground flex items-center justify-center touch-target active:scale-90 transition-transform"
        >
          <Plus size={18} />
        </button>
      </div>
    </div>
  );
}
