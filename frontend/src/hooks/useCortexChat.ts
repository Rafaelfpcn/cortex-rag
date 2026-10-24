"use client";

import { useState, useCallback } from "react";
import { ChatMessage, Citation } from "@/types";

export function useCortexChat(token: string | null) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);

  const sendMessage = useCallback(
    async (query: string) => {
      if (!query.trim() || isStreaming) return;

      const userMsg: ChatMessage = {
        id: crypto.randomUUID(),
        sender: "user",
        text: query,
      };

      const assistantId = crypto.randomUUID();
      const initialAssistantMsg: ChatMessage = {
        id: assistantId,
        sender: "assistant",
        text: "",
        isStreaming: true,
        citations: [],
      };

      setMessages((prev) => [...prev, userMsg, initialAssistantMsg]);
      setIsStreaming(true);

      try {
        const response = await fetch("/api/v1/chat/stream", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ query, stream: true }),
        });

        if (!response.ok) {
          const err = await response.json();
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? {
                    ...m,
                    text: `Erro: ${err.detail || "Falha na requisição"}`,
                    isStreaming: false,
                  }
                : m
            )
          );
          setIsStreaming(false);
          return;
        }

        const reader = response.body?.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        if (!reader) return;

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n\n");
          buffer = lines.pop() ?? "";

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              const data = JSON.parse(line.substring(6));

              if (data.type === "cache_hit") {
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantId
                      ? {
                          ...m,
                          cacheHit: true,
                          latencyMs: data.latency_ms,
                        }
                      : m
                  )
                );
              } else if (data.type === "citations") {
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantId
                      ? { ...m, citations: data.citations as Citation[] }
                      : m
                  )
                );
              } else if (data.type === "delta") {
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantId
                      ? { ...m, text: m.text + data.delta }
                      : m
                  )
                );
              } else if (data.type === "done") {
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantId
                      ? {
                          ...m,
                          isStreaming: false,
                          latencyMs: m.latencyMs ?? data.latency_ms,
                        }
                      : m
                  )
                );
              }
            }
          }
        }
      } catch (err: any) {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId
              ? {
                  ...m,
                  text: `Erro de conexão: ${err.message}`,
                  isStreaming: false,
                }
              : m
          )
        );
      } finally {
        setIsStreaming(false);
      }
    },
    [token, isStreaming]
  );

  return { messages, isStreaming, sendMessage };
}
