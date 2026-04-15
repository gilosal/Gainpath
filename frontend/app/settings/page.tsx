import type { Metadata } from "next";
import { SettingsView } from "@/components/settings/SettingsView";
import { AppShell } from "@/components/layout/AppShell";

export const metadata: Metadata = { title: "Settings" };

export default function SettingsPage() {
  return (
    <AppShell>
      <SettingsView />
    </AppShell>
  );
}
