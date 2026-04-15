"use client";

import { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@radix-ui/react-tabs";
import { Sparkles, MessageCircle, BarChart2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { DailyMotivation } from "./DailyMotivation";
import { WeeklySummary } from "./WeeklySummary";
import { ChatInterface } from "./ChatInterface";
import { XPBar } from "@/components/gamification/XPBar";
import { StreakBadge } from "@/components/gamification/StreakBadge";

export function CoachView() {
  const [tab, setTab] = useState("today");

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Header */}
      <div className="sticky top-0 z-10 bg-background/95 backdrop-blur border-b border-border px-4 pt-4 pb-3">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-foreground">Coach</h1>
          <StreakBadge size="md" />
        </div>
        <div className="mt-2">
          <XPBar compact />
        </div>
      </div>

      {/* Tabs */}
      <Tabs value={tab} onValueChange={setTab} className="flex-1 flex flex-col">
        <TabsList className="flex border-b border-border bg-transparent px-4">
          {[
            { value: "today", label: "Today", icon: Sparkles },
            { value: "chat", label: "Chat", icon: MessageCircle },
            { value: "summary", label: "Summary", icon: BarChart2 },
          ].map(({ value, label, icon: Icon }) => (
            <TabsTrigger
              key={value}
              value={value}
              className={cn(
                "flex items-center gap-1.5 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors",
                "data-[state=active]:border-primary data-[state=active]:text-foreground",
                "data-[state=inactive]:border-transparent data-[state=inactive]:text-muted-foreground"
              )}
            >
              <Icon size={14} />
              {label}
            </TabsTrigger>
          ))}
        </TabsList>

        <TabsContent value="today" className="flex-1 px-4 py-4 space-y-4">
          <DailyMotivation />
          <NudgeMessages />
          <PostWorkoutMessages />
        </TabsContent>

        <TabsContent value="chat" className="flex-1 flex flex-col overflow-hidden" style={{ minHeight: "calc(100vh - 200px)" }}>
          <ChatInterface />
        </TabsContent>

        <TabsContent value="summary" className="flex-1 px-4 py-4">
          <WeeklySummary />
        </TabsContent>
      </Tabs>
    </div>
  );
}

function NudgeMessages() {
  const { useQuery } = require("@tanstack/react-query");
  const { useMutation, useQueryClient } = require("@tanstack/react-query");
  const { coachingApi } = require("@/lib/api");
  const qc = useQueryClient();

  const { data: messages } = useQuery({
    queryKey: ["coaching", "nudge"],
    queryFn: () => coachingApi.messages("nudge"),
    staleTime: 5 * 60_000,
  });

  const dismissMutation = useMutation({
    mutationFn: (id: string) => coachingApi.dismissMessage(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["coaching"] }),
  });

  if (!messages?.length) return null;

  return (
    <div className="space-y-2">
      {messages.slice(0, 2).map((msg: { id: string; content: string }) => (
        <div key={msg.id} className="rounded-xl border border-orange-500/25 bg-orange-500/5 p-4">
          <div className="flex items-start gap-3">
            <span className="text-base flex-shrink-0">⚡</span>
            <p className="flex-1 text-sm text-foreground">{msg.content}</p>
            <button
              onClick={() => dismissMutation.mutate(msg.id)}
              className="text-muted-foreground hover:text-foreground flex-shrink-0"
            >
              ✕
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}

function PostWorkoutMessages() {
  const { useQuery } = require("@tanstack/react-query");
  const { useMutation, useQueryClient } = require("@tanstack/react-query");
  const { coachingApi } = require("@/lib/api");
  const qc = useQueryClient();

  const { data: messages } = useQuery({
    queryKey: ["coaching", "post_workout_list"],
    queryFn: () => coachingApi.messages("post_workout"),
    staleTime: 5 * 60_000,
  });

  const dismissMutation = useMutation({
    mutationFn: (id: string) => coachingApi.dismissMessage(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["coaching"] }),
  });

  if (!messages?.length) return null;

  return (
    <div className="space-y-2">
      <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Recent Sessions</p>
      {messages.slice(0, 3).map((msg: { id: string; content: string }) => {
        const lines = msg.content.split("\n").filter(Boolean);
        const headline = lines[0]?.replace(/\*\*/g, "") ?? "Well done!";
        const body = lines.slice(1).join(" ").replace(/\*\*/g, "");
        return (
          <div key={msg.id} className="rounded-xl border border-border bg-card p-4">
            <div className="flex items-start justify-between mb-1">
              <p className="font-semibold text-sm text-foreground">{headline}</p>
              <button
                onClick={() => dismissMutation.mutate(msg.id)}
                className="text-muted-foreground hover:text-foreground ml-2 flex-shrink-0 text-xs"
              >
                ✕
              </button>
            </div>
            {body && <p className="text-sm text-muted-foreground">{body}</p>}
          </div>
        );
      })}
    </div>
  );
}
