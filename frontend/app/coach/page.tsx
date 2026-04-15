import type { Metadata } from "next";
import { AppShell } from "@/components/layout/AppShell";
import { CoachView } from "@/components/coach/CoachView";

export const metadata: Metadata = { title: "Coach" };

export default function CoachPage() {
  return (
    <AppShell>
      <CoachView />
    </AppShell>
  );
}
