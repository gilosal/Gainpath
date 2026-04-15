import type { Metadata } from "next";
import { AppShell } from "@/components/layout/AppShell";
import { AchievementsView } from "@/components/gamification/AchievementsView";

export const metadata: Metadata = { title: "Achievements" };

export default function AchievementsPage() {
  return (
    <AppShell>
      <AchievementsView />
    </AppShell>
  );
}
