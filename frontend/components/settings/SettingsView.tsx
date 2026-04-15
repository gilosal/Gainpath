"use client";

import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { profileApi, plansApi, savePassword } from "@/lib/api";
import { cn } from "@/lib/utils";
import { ModelSelector } from "./ModelSelector";
import { PlanGeneratingSkeleton } from "@/components/common/SkeletonCard";
import { Moon, Sun, Scale, Ruler, RefreshCw } from "lucide-react";
import type { UserProfile } from "@/lib/types";

export function SettingsView() {
  const qc = useQueryClient();
  const { data: profile, isLoading } = useQuery({
    queryKey: ["profile"],
    queryFn: profileApi.get,
  });

  const updateMutation = useMutation({
    mutationFn: profileApi.update,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["profile"] }),
  });

  const [generating, setGenerating] = useState<string | null>(null);
  const [password, setPassword] = useState("");
  const [darkMode, setDarkMode] = useState(true);

  useEffect(() => {
    if (profile) setDarkMode(profile.dark_mode);
  }, [profile]);

  const toggleDark = (on: boolean) => {
    setDarkMode(on);
    document.documentElement.classList.toggle("dark", on);
    localStorage.setItem("paceforge-theme", on ? "dark" : "light");
    updateMutation.mutate({ dark_mode: on });
  };

  const generatePlan = async (type: "running" | "lifting" | "mobility") => {
    setGenerating(type);
    try {
      if (type === "running") await plansApi.generateRunning();
      else if (type === "lifting") await plansApi.generateLifting();
      else await plansApi.generateMobility();
      qc.invalidateQueries({ queryKey: ["plans"] });
    } finally {
      setGenerating(null);
    }
  };

  if (isLoading) {
    return (
      <div className="p-4">
        <PlanGeneratingSkeleton message="Loading settings…" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="sticky top-0 z-10 bg-background/95 backdrop-blur border-b border-border px-4 pt-4 pb-3">
        <h1 className="text-2xl font-bold text-foreground">Settings</h1>
      </div>

      <div className="px-4 py-4 space-y-6">

        {/* ── Appearance ── */}
        <Section title="Appearance">
          <ToggleRow
            label="Dark Mode"
            description="Better for gym use and early runs"
            icon={darkMode ? Moon : Sun}
            checked={darkMode}
            onChange={toggleDark}
          />
        </Section>

        {/* ── Units ── */}
        <Section title="Units">
          <SegmentRow
            label="Weight"
            icon={Scale}
            options={["kg", "lb"]}
            value={profile?.units_weight ?? "kg"}
            onChange={(v) => updateMutation.mutate({ units_weight: v as "kg" | "lb" })}
          />
          <SegmentRow
            label="Distance"
            icon={Ruler}
            options={["km", "mi"]}
            value={profile?.units_distance ?? "km"}
            onChange={(v) => updateMutation.mutate({ units_distance: v as "km" | "mi" })}
          />
        </Section>

        {/* ── AI Model ── */}
        <Section title="AI Model">
          {profile && (
            <ModelSelector
              value={profile.preferred_ai_model ?? ""}
              onChange={(model) => updateMutation.mutate({ preferred_ai_model: model })}
            />
          )}
        </Section>

        {/* ── Generate Plans ── */}
        <Section title="Generate Training Plans">
          <p className="text-xs text-muted-foreground mb-3">
            Generates a new AI plan using your current profile. Any active plan of the same type will be archived.
          </p>
          {generating ? (
            <PlanGeneratingSkeleton
              message={`Generating your ${generating} plan… this may take 15–30 seconds`}
            />
          ) : (
            <div className="space-y-2">
              {(["running", "lifting", "mobility"] as const).map((type) => (
                <button
                  key={type}
                  onClick={() => generatePlan(type)}
                  className={cn(
                    "w-full flex items-center justify-between px-4 py-3.5 rounded-xl border border-border bg-card",
                    "text-left touch-target active:scale-[0.98] transition-transform"
                  )}
                >
                  <span className="text-sm font-medium text-foreground capitalize">
                    Generate {type} plan
                  </span>
                  <RefreshCw size={16} className="text-muted-foreground" />
                </button>
              ))}
            </div>
          )}
        </Section>

        {/* ── Auth ── */}
        <Section title="App Password">
          <p className="text-xs text-muted-foreground mb-3">
            Stored locally for API auth. Must match APP_PASSWORD in your .env.
          </p>
          <div className="flex gap-2">
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter app password"
              className="flex-1 bg-secondary border border-border rounded-xl px-4 py-2.5 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
            <button
              onClick={() => { savePassword(password); setPassword(""); }}
              className="px-4 py-2.5 rounded-xl bg-primary text-primary-foreground text-sm font-medium touch-target active:scale-95 transition-transform"
            >
              Save
            </button>
          </div>
        </Section>

        {/* ── About ── */}
        <Section title="About">
          <div className="text-xs text-muted-foreground space-y-1">
            <p>PaceForge · Personal fitness training platform</p>
            <p>Self-hosted · Single user · AI powered by OpenRouter</p>
          </div>
        </Section>

        <div className="h-4" />
      </div>
    </div>
  );
}

// ── Small reusable setting components ─────────────────────────────────────────

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h2 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">
        {title}
      </h2>
      {children}
    </div>
  );
}

function ToggleRow({
  label, description, icon: Icon, checked, onChange,
}: {
  label: string;
  description?: string;
  icon: React.ElementType;
  checked: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <div className="flex items-center justify-between rounded-xl border border-border bg-card px-4 py-3.5">
      <div className="flex items-center gap-3">
        <Icon size={18} className="text-muted-foreground" />
        <div>
          <p className="text-sm font-medium text-foreground">{label}</p>
          {description && <p className="text-xs text-muted-foreground">{description}</p>}
        </div>
      </div>
      <button
        role="switch"
        aria-checked={checked}
        onClick={() => onChange(!checked)}
        className={cn(
          "w-11 h-6 rounded-full transition-colors duration-200 flex-shrink-0 relative",
          checked ? "bg-primary" : "bg-muted"
        )}
      >
        <span
          className={cn(
            "absolute top-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform duration-200",
            checked ? "translate-x-5" : "translate-x-0.5"
          )}
        />
      </button>
    </div>
  );
}

function SegmentRow({
  label, icon: Icon, options, value, onChange,
}: {
  label: string;
  icon: React.ElementType;
  options: string[];
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <div className="flex items-center justify-between rounded-xl border border-border bg-card px-4 py-3 mb-2">
      <div className="flex items-center gap-3">
        <Icon size={18} className="text-muted-foreground" />
        <p className="text-sm font-medium text-foreground">{label}</p>
      </div>
      <div className="flex gap-1 bg-muted rounded-lg p-0.5">
        {options.map((opt) => (
          <button
            key={opt}
            onClick={() => onChange(opt)}
            className={cn(
              "px-3 py-1 rounded-md text-xs font-semibold transition-colors",
              value === opt
                ? "bg-card text-foreground shadow-sm"
                : "text-muted-foreground"
            )}
          >
            {opt}
          </button>
        ))}
      </div>
    </div>
  );
}
