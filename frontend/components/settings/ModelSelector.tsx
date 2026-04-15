"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import { ChevronDown, Check } from "lucide-react";

// Curated list of popular OpenRouter models
const MODELS = [
  { id: "",                                   label: "Default (from .env)",      provider: "System" },
  { id: "anthropic/claude-sonnet-4-5",        label: "Claude Sonnet 4.5",        provider: "Anthropic" },
  { id: "anthropic/claude-opus-4",            label: "Claude Opus 4",            provider: "Anthropic" },
  { id: "openai/gpt-4o",                      label: "GPT-4o",                   provider: "OpenAI" },
  { id: "openai/gpt-4o-mini",                 label: "GPT-4o Mini",              provider: "OpenAI" },
  { id: "google/gemini-2.5-pro",              label: "Gemini 2.5 Pro",           provider: "Google" },
  { id: "google/gemini-2.5-flash",            label: "Gemini 2.5 Flash",         provider: "Google" },
  { id: "meta-llama/llama-4-maverick",        label: "Llama 4 Maverick",         provider: "Meta" },
  { id: "mistralai/mistral-large",            label: "Mistral Large",            provider: "Mistral" },
  { id: "deepseek/deepseek-r1",               label: "DeepSeek R1",              provider: "DeepSeek" },
];

interface ModelSelectorProps {
  value: string;
  onChange: (model: string) => void;
}

export function ModelSelector({ value, onChange }: ModelSelectorProps) {
  const [open, setOpen] = useState(false);
  const selected = MODELS.find((m) => m.id === value) ?? MODELS[0];

  return (
    <div className="relative">
      <button
        onClick={() => setOpen((o) => !o)}
        className={cn(
          "w-full flex items-center justify-between px-4 py-3.5 rounded-xl border border-border bg-card",
          "touch-target active:scale-[0.98] transition-transform"
        )}
      >
        <div className="text-left">
          <p className="text-sm font-medium text-foreground">{selected.label}</p>
          <p className="text-xs text-muted-foreground">{selected.provider}</p>
        </div>
        <ChevronDown
          size={16}
          className={cn("text-muted-foreground transition-transform", open && "rotate-180")}
        />
      </button>

      {open && (
        <div className="absolute inset-x-0 top-full mt-1 z-20 bg-card border border-border rounded-xl shadow-2xl overflow-hidden max-h-72 overflow-y-auto">
          {MODELS.map((model) => (
            <button
              key={model.id}
              onClick={() => { onChange(model.id); setOpen(false); }}
              className={cn(
                "w-full flex items-center justify-between px-4 py-3 text-left",
                "hover:bg-secondary transition-colors touch-target",
                model.id === value && "bg-primary/10"
              )}
            >
              <div>
                <p className="text-sm font-medium text-foreground">{model.label}</p>
                <p className="text-xs text-muted-foreground">{model.provider}</p>
              </div>
              {model.id === value && (
                <Check size={15} className="text-primary flex-shrink-0" />
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
