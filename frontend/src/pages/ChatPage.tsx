import { DefaultChatTransport, UIMessage } from "ai";
import { useChat } from "@ai-sdk/react";
import { useAuth } from "@/hooks/useAuth";
import { env } from "@/lib/env";
import { supabase } from "@/lib/supabase";
import { FormEvent, memo, useCallback, useEffect, useMemo, useRef, useState } from "react";
import Markdown from "@/components/Markdown";
import Chart from "@/components/Chart";
import ThreadSidebar from "@/components/ThreadSidebar";

const THREAD_KEY = "doc-copilot-thread";

function getStoredThreadId(): string | null {
  return localStorage.getItem(THREAD_KEY);
}

function storeThreadId(id: string) {
  localStorage.setItem(THREAD_KEY, id);
}

async function loadMessages(threadId: string): Promise<UIMessage[]> {
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;
  if (!token) return [];
  const res = await fetch(`${env.apiBaseUrl}/api/threads/${threadId}/messages`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) return [];
  const msgs = await res.json();
  return msgs.map((m: { id: string; role: string; content: string }) => ({
    id: m.id,
    role: m.role,
    parts: [{ type: "text" as const, text: m.content }],
  }));
}

function ThinkingDots() {
  return (
    <div className="flex items-center gap-1 px-2 py-2">
      {[0, 1, 2].map((i) => (
        <span key={i} className="thinking-dot w-2 h-2 bg-gray-400 rounded-full" />
      ))}
    </div>
  );
}

function Cursor() {
  return <span className="inline-block w-[2px] h-[1em] bg-gray-600 align-middle ml-0.5 animate-blink" />;
}

interface MessageItemProps {
  msg: { id: string; role: string; parts: Array<{ type: string; [key: string]: unknown }> };
  isUser: boolean;
  isCurrentAssistant: boolean;
  assistantStreaming: boolean;
}

const MessageItem = memo(function MessageItem({ msg, isUser, isCurrentAssistant, assistantStreaming }: MessageItemProps) {
  const text = useMemo(
    () => msg.parts
      ?.filter((p) => p.type === "text")
      .map((p) => ("text" in p ? (p as unknown as { text: string }).text : ""))
      .join("") ?? "",
    [msg.parts],
  );
  const chartParts = useMemo(
    () => msg.parts?.filter((p) => p.type === "data-chart") ?? [],
    [msg.parts],
  );

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} animate-fade-in`}>
      <div className="max-w-[75%]">
        <div
          className={`rounded-2xl px-4 py-2.5 ${
            isUser
              ? "bg-blue-600 text-white"
              : "bg-white border border-gray-200 text-gray-900 shadow-sm"
          }`}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap">{text}</p>
          ) : (
            <>
              <Markdown content={text} />
              {chartParts.map((part, i) => {
                const dp = part as { type: string; data: any };
                return <Chart key={i} data={dp.data} />;
              })}
            </>
          )}
          {isCurrentAssistant && assistantStreaming && <Cursor />}
        </div>
      </div>
    </div>
  );
});

function ChatView({ threadId }: { threadId: string }) {
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const [initialMsgs, setInitialMsgs] = useState<UIMessage[] | undefined>(undefined);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const stored = getStoredThreadId();
    if (stored && stored === threadId) {
      loadMessages(threadId).then((msgs) => {
        setInitialMsgs(msgs);
        setLoading(false);
      });
    } else {
      setInitialMsgs([]);
      setLoading(false);
    }
  }, [threadId]);

  const { messages, status, error, sendMessage, stop } = useChat({
    id: threadId,
    messages: initialMsgs,
    transport: new DefaultChatTransport({
      api: `${env.apiBaseUrl}/api/chat/stream`,
      headers: async () => {
        const { data } = await supabase.auth.getSession();
        return { Authorization: `Bearer ${data.session?.access_token}` };
      },
    }),
  });

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  if (loading) {
    return (
      <div className="flex flex-1 items-center justify-center bg-gray-50">
        <div className="text-gray-400 text-sm">Loading...</div>
      </div>
    );
  }

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const input = inputRef.current;
    if (!input || !input.value.trim()) return;
    sendMessage({ text: input.value });
    input.value = "";
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.currentTarget.form?.requestSubmit();
    }
  }

  const isStreaming = status === "streaming";
  const lastAssistant = messages.filter((m) => m.role === "assistant").at(-1);
  const assistantStreaming = !!(isStreaming && lastAssistant?.parts?.some(
    (p) => p.type === "text" && "state" in p && p.state === "streaming"
  ));

  return (
    <div className="flex flex-col flex-1 bg-gray-50">
      <header className="flex items-center justify-between px-5 py-3 bg-white border-b border-gray-200 shrink-0">
        <h1 className="text-lg font-semibold text-gray-900">
          <span className="text-blue-600">Document</span> Copilot
        </h1>
        <div className="flex items-center gap-3">
          <span className="text-sm text-gray-500">{/* email could go here */}</span>
        </div>
      </header>

      <main className="flex-1 overflow-y-auto px-4 py-6">
        <div className="max-w-3xl mx-auto space-y-4">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center mt-32 text-center">
              <div className="w-16 h-16 rounded-2xl bg-blue-100 flex items-center justify-center mb-4">
                <svg className="w-8 h-8 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <h2 className="text-xl font-semibold text-gray-700 mb-2">
                Ask about SEC filings
              </h2>
              <p className="text-sm text-gray-400 max-w-md">
                Search across 25 corporate filings from Apple, Microsoft, NVIDIA, Amazon, and Google.
              </p>
            </div>
          )}

          {messages.map((msg) => {
            const isUser = msg.role === "user";
            const isCurrentAssistant = !isUser && msg.id === lastAssistant?.id;
            return (
              <MessageItem
                key={msg.id}
                msg={msg as MessageItemProps["msg"]}
                isUser={isUser}
                isCurrentAssistant={isCurrentAssistant}
                assistantStreaming={assistantStreaming}
              />
            );
          })}

          {isStreaming && !assistantStreaming && (
            <div className="flex justify-start animate-fade-in">
              <div className="bg-white border border-gray-200 rounded-2xl px-4 py-3 shadow-sm">
                <ThinkingDots />
              </div>
            </div>
          )}

          {error && (
            <div className="flex justify-center animate-fade-in">
              <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg px-4 py-2.5">
                {error.message}
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>
      </main>

      <footer className="border-t border-gray-200 bg-white px-4 py-3 shrink-0">
        <form onSubmit={handleSubmit} className="max-w-3xl mx-auto flex gap-2">
          <div className="flex-1 relative">
            <input
              ref={inputRef}
              name="input"
              type="text"
              placeholder="Ask about SEC filings..."
              disabled={isStreaming}
              onKeyDown={handleKeyDown}
              className="w-full rounded-xl border border-gray-300 bg-gray-50 px-4 py-3 pr-12 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed transition-shadow"
            />
          </div>
          {isStreaming ? (
            <button
              type="button"
              onClick={stop}
              className="rounded-xl bg-gray-900 px-4 py-3 text-white text-sm font-medium hover:bg-gray-800 transition-colors shrink-0 flex items-center gap-2"
            >
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                <rect x="6" y="6" width="12" height="12" rx="1" />
              </svg>
              Stop
            </button>
          ) : (
            <button
              type="submit"
              disabled={status === "submitted"}
              className="rounded-xl bg-blue-600 px-5 py-3 text-white text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shrink-0"
            >
              Send
            </button>
          )}
        </form>
      </footer>
    </div>
  );
}

export default function ChatPage() {
  const { signOut } = useAuth();

  const getInitialThread = useCallback(() => {
    const stored = getStoredThreadId();
    if (stored) return stored;
    const id = crypto.randomUUID();
    storeThreadId(id);
    return id;
  }, []);

  const [threadId, setThreadId] = useState(getInitialThread);

  function handleSwitchThread(newId: string) {
    storeThreadId(newId);
    setThreadId(newId);
  }

  return (
    <div className="flex h-screen">
      <ThreadSidebar currentThreadId={threadId} onSwitchThread={handleSwitchThread} />
      <ChatView key={threadId} threadId={threadId} />
      {/* Floating sign out */}
      <button
        onClick={signOut}
        className="fixed bottom-4 right-4 z-50 text-xs text-gray-400 hover:text-red-500 transition-colors bg-white/80 backdrop-blur rounded-lg px-2.5 py-1.5 border border-gray-200 shadow-sm"
      >
        Sign out
      </button>
    </div>
  );
}
