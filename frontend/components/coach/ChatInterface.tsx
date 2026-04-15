"use client";

import { useState, useRef, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Bot } from "lucide-react";
import { coachingApi } from "@/lib/api";
import { cn } from "@/lib/utils";
import type { ChatMessage } from "@/lib/types";

export function ChatInterface() {
  const qc = useQueryClient();
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  const { data: history = [], isLoading } = useQuery({
    queryKey: ["coaching", "chat"],
    queryFn: coachingApi.chatHistory,
    staleTime: 0,
  });

  const sendMutation = useMutation({
    mutationFn: (message: string) => coachingApi.sendChat(message),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["coaching", "chat"] });
    },
  });

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [history]);

  function handleSend() {
    const msg = input.trim();
    if (!msg || sendMutation.isPending) return;
    setInput("");
    sendMutation.mutate(msg);
  }

  const isEmpty = history.length === 0 && !isLoading;

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
        {isEmpty && (
          <div className="flex flex-col items-center justify-center h-full text-center py-12">
            <div className="p-4 bg-primary/10 rounded-2xl mb-3">
              <Bot size={28} className="text-primary" />
            </div>
            <h3 className="font-semibold text-foreground mb-1">Your AI Coach</h3>
            <p className="text-sm text-muted-foreground max-w-xs">
              Ask me anything about your training, recovery, nutrition, or how to hit your goals.
            </p>
          </div>
        )}

        {history.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}

        {sendMutation.isPending && <TypingIndicator />}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="px-4 pb-4 pt-2 border-t border-border">
        <div className="flex items-end gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            placeholder="Ask your coach..."
            rows={1}
            className={cn(
              "flex-1 resize-none rounded-xl border border-border bg-muted px-3 py-2.5",
              "text-sm text-foreground placeholder:text-muted-foreground",
              "focus:outline-none focus:ring-1 focus:ring-primary",
              "max-h-32 overflow-y-auto"
            )}
            style={{ minHeight: "42px" }}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || sendMutation.isPending}
            className={cn(
              "p-2.5 rounded-xl transition-all",
              input.trim() && !sendMutation.isPending
                ? "bg-primary text-primary-foreground active:scale-95"
                : "bg-muted text-muted-foreground cursor-not-allowed"
            )}
          >
            <Send size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}

function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn("flex", isUser ? "justify-end" : "justify-start")}
    >
      {!isUser && (
        <div className="w-7 h-7 rounded-full bg-primary/15 border border-primary/25 flex items-center justify-center flex-shrink-0 mr-2 mt-0.5">
          <Bot size={13} className="text-primary" />
        </div>
      )}
      <div
        className={cn(
          "max-w-[80%] rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed",
          isUser
            ? "bg-primary text-primary-foreground rounded-br-sm"
            : "bg-muted text-foreground rounded-bl-sm"
        )}
      >
        {message.content}
      </div>
    </motion.div>
  );
}

function TypingIndicator() {
  return (
    <div className="flex justify-start">
      <div className="w-7 h-7 rounded-full bg-primary/15 border border-primary/25 flex items-center justify-center flex-shrink-0 mr-2">
        <Bot size={13} className="text-primary" />
      </div>
      <div className="bg-muted rounded-2xl rounded-bl-sm px-4 py-3 flex gap-1 items-center">
        {[0, 1, 2].map((i) => (
          <motion.div
            key={i}
            className="w-1.5 h-1.5 bg-muted-foreground rounded-full"
            animate={{ scale: [1, 1.4, 1], opacity: [0.4, 1, 0.4] }}
            transition={{ repeat: Infinity, duration: 1, delay: i * 0.2 }}
          />
        ))}
      </div>
    </div>
  );
}
