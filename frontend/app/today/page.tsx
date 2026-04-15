import type { Metadata } from "next";
import { TodayView } from "@/components/today/TodayView";
import { AppShell } from "@/components/layout/AppShell";

export const metadata: Metadata = { title: "Today" };

export default function TodayPage() {
  return (
    <AppShell>
      <TodayView />
    </AppShell>
  );
}
