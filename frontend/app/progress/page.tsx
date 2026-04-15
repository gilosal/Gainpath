import type { Metadata } from "next";
import { ProgressView } from "@/components/progress/ProgressView";
import { AppShell } from "@/components/layout/AppShell";

export const metadata: Metadata = { title: "Progress" };

export default function ProgressPage() {
  return (
    <AppShell>
      <ProgressView />
    </AppShell>
  );
}
