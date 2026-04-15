import type { Metadata } from "next";
import { CalendarView } from "@/components/calendar/CalendarView";
import { AppShell } from "@/components/layout/AppShell";

export const metadata: Metadata = { title: "Calendar" };

export default function CalendarPage() {
  return (
    <AppShell>
      <CalendarView />
    </AppShell>
  );
}
