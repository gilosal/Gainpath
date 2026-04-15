"use client";

import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { sessionsApi } from "@/lib/api";
import { logSetWithFallback } from "@/lib/offline-queue";
import { BottomSheet } from "@/components/common/BottomSheet";
import { cn, rpeColor, rpeLabel } from "@/lib/utils";
import type { SessionLog } from "@/lib/types";
import { Minus, Plus, Check } from "lucide-react";

interface QuickLogSheetProps {
  session: SessionLog;
  open: boolean;
  onClose: () => void;
}

export function QuickLogSheet({ session, open, onClose }: QuickLogSheetProps) {
  const qc = useQueryClient();
  const [weight, setWeight] = useState(0);
  const [reps, setReps] = useState(10);
  const [rpe, setRpe] = useState(7);
  const [exerciseName, setExerciseName] = useState("");
  const [distance, setDistance] = useState(0);
  const [duration, setDuration] = useState(0);
  const [saved, setSaved] = useState(false);

  const isRunning = session.session_type === "running";
  const isMobility = session.session_type === "mobility";

  const save = async () => {
    const payload = isRunning
      ? { exercise_name: "Run", distance, duration: duration * 60, rpe }
      : isMobility
      ? { exercise_name: exerciseName || "Stretch", hold_duration: duration, rpe }
      : { exercise_name: exerciseName || "Exercise", weight, reps, rpe };

    await logSetWithFallback(session.id, payload, () =>
      sessionsApi.addSet(session.id, payload)
    );
    qc.invalidateQueries({ queryKey: ["sessions", "today"] });
    setSaved(true);
    setTimeout(() => {
      setSaved(false);
      onClose();
    }, 800);
  };

  return (
    <BottomSheet open={open} onClose={onClose} title="Quick Log" height="auto">
      <div className="space-y-5 pb-6">
        {/* Exercise name (lifting/mobility) */}
        {!isRunning && (
          <div>
            <label className="text-xs text-muted-foreground font-medium uppercase tracking-wider">
              Exercise
            </label>
            <input
              type="text"
              value={exerciseName}
              onChange={(e) => setExerciseName(e.target.value)}
              placeholder={isMobility ? "e.g. Pigeon Pose" : "e.g. Squat"}
              className="mt-1.5 w-full bg-secondary border border-border rounded-xl px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
          </div>
        )}

        {/* Running fields */}
        {isRunning && (
          <>
            <Stepper
              label="Distance (km)"
              value={distance}
              step={0.5}
              onDecrement={() => setDistance((d) => Math.max(0, +(d - 0.5).toFixed(1)))}
              onIncrement={() => setDistance((d) => +(d + 0.5).toFixed(1))}
              display={distance.toFixed(1)}
            />
            <Stepper
              label="Duration (min)"
              value={duration}
              step={1}
              onDecrement={() => setDuration((d) => Math.max(0, d - 1))}
              onIncrement={() => setDuration((d) => d + 1)}
            />
          </>
        )}

        {/* Lifting fields */}
        {!isRunning && !isMobility && (
          <>
            <Stepper
              label="Weight (kg)"
              value={weight}
              step={2.5}
              onDecrement={() => setWeight((w) => Math.max(0, +(w - 2.5).toFixed(1)))}
              onIncrement={() => setWeight((w) => +(w + 2.5).toFixed(1))}
              display={weight % 1 === 0 ? String(weight) : weight.toFixed(1)}
            />
            <Stepper
              label="Reps"
              value={reps}
              step={1}
              onDecrement={() => setReps((r) => Math.max(1, r - 1))}
              onIncrement={() => setReps((r) => r + 1)}
            />
          </>
        )}

        {/* Mobility duration */}
        {isMobility && (
          <Stepper
            label="Hold / Duration (sec)"
            value={duration}
            step={5}
            onDecrement={() => setDuration((d) => Math.max(0, d - 5))}
            onIncrement={() => setDuration((d) => d + 5)}
          />
        )}

        {/* RPE */}
        <div>
          <div className="flex justify-between mb-2">
            <label className="text-xs text-muted-foreground font-medium uppercase tracking-wider">
              RPE (Effort)
            </label>
            <span className={cn("text-sm font-bold", rpeColor(rpe))}>
              {rpe} — {rpeLabel(rpe)}
            </span>
          </div>
          <input
            type="range" min={1} max={10} value={rpe}
            onChange={(e) => setRpe(Number(e.target.value))}
            className="w-full accent-primary"
          />
          <div className="flex justify-between text-xs text-muted-foreground mt-1">
            <span>Easy</span><span>Max</span>
          </div>
        </div>

        <button
          onClick={save}
          className={cn(
            "w-full rounded-2xl py-4 text-base font-bold flex items-center justify-center gap-2",
            "touch-target active:scale-95 transition-all duration-200",
            saved
              ? "bg-green-600 text-white"
              : "bg-primary text-primary-foreground"
          )}
        >
          <Check size={20} strokeWidth={3} />
          {saved ? "Saved!" : "Save Set"}
        </button>
      </div>
    </BottomSheet>
  );
}

function Stepper({
  label, value, step, onDecrement, onIncrement, display,
}: {
  label: string;
  value: number;
  step: number;
  onDecrement: () => void;
  onIncrement: () => void;
  display?: string;
}) {
  return (
    <div>
      <label className="text-xs text-muted-foreground font-medium uppercase tracking-wider">
        {label}
      </label>
      <div className="flex items-center gap-3 mt-1.5">
        <button
          onClick={onDecrement}
          className="w-12 h-12 rounded-xl bg-secondary flex items-center justify-center touch-target active:scale-90 transition-transform flex-shrink-0"
        >
          <Minus size={18} />
        </button>
        <span className="flex-1 text-center text-3xl font-black text-foreground tabular-nums">
          {display ?? value}
        </span>
        <button
          onClick={onIncrement}
          className="w-12 h-12 rounded-xl bg-primary text-primary-foreground flex items-center justify-center touch-target active:scale-90 transition-transform flex-shrink-0"
        >
          <Plus size={18} />
        </button>
      </div>
    </div>
  );
}
