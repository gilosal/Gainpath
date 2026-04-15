"use client";

import { BottomNav } from "./BottomNav";
import { cn } from "@/lib/utils";

interface AppShellProps {
  children: React.ReactNode;
  /** Hide the bottom nav for full-screen modes (e.g. active workout) */
  hideNav?: boolean;
  /** Extra classes for the main content area */
  className?: string;
}

/**
 * AppShell wraps all app pages with:
 * - Bottom navigation bar (mobile) / side nav placeholder (md+)
 * - Safe content area that clears the nav bar height
 */
export function AppShell({ children, hideNav = false, className }: AppShellProps) {
  return (
    <div className="flex flex-col min-h-screen bg-background">
      {/* Main scrollable content */}
      <main
        className={cn(
          "flex-1 overflow-y-auto",
          // Push content above the bottom nav on mobile
          !hideNav && "pb-[calc(4rem+env(safe-area-inset-bottom,0px))]",
          className
        )}
      >
        {children}
      </main>

      {!hideNav && <BottomNav />}
    </div>
  );
}
