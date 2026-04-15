"use client";

import { useRef } from "react";
import { motion, useMotionValue, animate } from "framer-motion";

interface WeekSliderProps {
  onSwipeLeft: () => void;
  onSwipeRight: () => void;
  children: React.ReactNode;
}

/**
 * Wraps children in a swipeable container.
 * Swipe left → next week, swipe right → previous week.
 */
export function WeekSlider({ onSwipeLeft, onSwipeRight, children }: WeekSliderProps) {
  const x = useMotionValue(0);
  const THRESHOLD = 60;

  const handleDragEnd = (_: unknown, info: { offset: { x: number } }) => {
    if (info.offset.x < -THRESHOLD) {
      onSwipeLeft();
    } else if (info.offset.x > THRESHOLD) {
      onSwipeRight();
    }
    animate(x, 0, { type: "spring", stiffness: 300, damping: 30 });
  };

  return (
    <motion.div
      style={{ x }}
      drag="x"
      dragConstraints={{ left: -100, right: 100 }}
      dragElastic={0.3}
      onDragEnd={handleDragEnd}
      className="touch-pan-x cursor-grab active:cursor-grabbing"
    >
      {children}
    </motion.div>
  );
}
