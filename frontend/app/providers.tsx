"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState, useEffect } from "react";
import { offlineQueue } from "@/lib/offline-queue";

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000,
            gcTime: 5 * 60 * 1000,
            retry: 1,
            refetchOnWindowFocus: false,
          },
        },
      })
  );

  // Apply user's dark/light preference on mount
  useEffect(() => {
    const saved = localStorage.getItem("paceforge-theme");
    if (saved === "light") {
      document.documentElement.classList.remove("dark");
    } else {
      document.documentElement.classList.add("dark");
    }
  }, []);

  // Process offline queue when connection restores or SW signals
  useEffect(() => {
    const handleOnline = () => offlineQueue.sync();
    const handleSwSync = () => offlineQueue.sync();

    window.addEventListener("online", handleOnline);
    window.addEventListener("paceforge:sync-offline", handleSwSync);
    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("paceforge:sync-offline", handleSwSync);
    };
  }, []);

  return (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}
