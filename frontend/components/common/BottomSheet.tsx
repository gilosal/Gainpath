"use client";

import { useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";

interface BottomSheetProps {
  open: boolean;
  onClose: () => void;
  title?: string;
  /** Sheet height — "auto" grows with content, "full" is ~90vh */
  height?: "auto" | "full" | "half";
  children: React.ReactNode;
}

const heightClass = {
  auto: "max-h-[85vh]",
  half: "h-[50vh]",
  full: "h-[90vh]",
};

export function BottomSheet({
  open,
  onClose,
  title,
  height = "auto",
  children,
}: BottomSheetProps) {
  // Close on Escape key
  useEffect(() => {
    if (!open) return;
    const handler = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [open, onClose]);

  // Prevent body scroll when sheet is open
  useEffect(() => {
    document.body.style.overflow = open ? "hidden" : "";
    return () => { document.body.style.overflow = ""; };
  }, [open]);

  return (
    <AnimatePresence>
      {open && (
        <>
          {/* Backdrop */}
          <motion.div
            key="backdrop"
            className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
          />

          {/* Sheet */}
          <motion.div
            key="sheet"
            className={cn(
              "fixed inset-x-0 bottom-0 z-50",
              "bg-card rounded-t-2xl shadow-2xl",
              "flex flex-col overflow-hidden",
              heightClass[height]
            )}
            initial={{ y: "100%" }}
            animate={{ y: 0 }}
            exit={{ y: "100%" }}
            transition={{ type: "spring", damping: 30, stiffness: 300 }}
          >
            {/* Drag handle */}
            <div className="flex justify-center pt-3 pb-1 flex-shrink-0">
              <div className="w-10 h-1 rounded-full bg-muted-foreground/30" />
            </div>

            {/* Header */}
            {title && (
              <div className="flex items-center justify-between px-5 pb-3 flex-shrink-0">
                <h2 className="text-base font-semibold text-foreground">{title}</h2>
                <button
                  onClick={onClose}
                  className="touch-target text-muted-foreground hover:text-foreground transition-colors"
                  aria-label="Close"
                >
                  <X size={20} />
                </button>
              </div>
            )}

            {/* Scrollable content */}
            <div
              className={cn(
                "flex-1 overflow-y-auto overscroll-contain px-5",
                "pb-safe"
              )}
            >
              {children}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
