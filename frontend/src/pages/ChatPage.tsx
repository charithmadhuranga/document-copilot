import { DefaultChatTransport } from "ai";
import { useChat } from "@ai-sdk/react";
import { useAuth } from "@/hooks/useAuth";
import { env } from "@/lib/env";
import { supabase } from "@/lib/supabase";
import { FormEvent, useRef } from "react";

export default function ChatPage() {
  const { user, signOut } = useAuth();
  const formRef = useRef<HTMLFormElement>(null);

  const { messages, status, error, sendMessage, stop } = useChat({
    transport: new DefaultChatTransport({
      api: `${env.apiBaseUrl}/api/chat/stream`,
      headers: async () => {
        const { data } = await supabase.auth.getSession();
        return { Authorization: `Bearer ${data.session?.access_token}` };
      },
    }),
  });

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    const input = form.get("input") as string;
    if (!input?.trim()) return;
    sendMessage({ text: input });
    e.currentTarget.reset();
  }

  return (
    <div className="flex flex-col h-screen">
      <header className="flex items-center justify-between border-b px-4 py-3">
        <h1 className="text-lg font-semibold">Document Copilot</h1>
        <div className="flex items-center gap-3">
          <span className="text-sm text-gray-500">{user?.email}</span>
          <button onClick={signOut} className="text-sm text-red-600 hover:underline">
            Sign out
          </button>
        </div>
      </header>

      <main className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <p className="text-center text-gray-400 mt-20">
            Ask a question about SEC filings
          </p>
        )}
        {messages.map((msg) => {
          const text = msg.parts?.map((p) => (p.type === "text" ? p.text : "")).join("") ?? "";
          return (
            <div key={msg.id} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
              <div
                className={`max-w-[70%] rounded-lg px-4 py-2 whitespace-pre-wrap ${
                  msg.role === "user"
                    ? "bg-blue-600 text-white"
                    : "bg-gray-100 text-gray-900"
                }`}
              >
                {text}
              </div>
            </div>
          );
        })}
        {error && (
          <div className="text-red-500 text-sm text-center">
            Error: {error.message}
          </div>
        )}
      </main>

      <footer className="border-t p-4">
        <form ref={formRef} onSubmit={handleSubmit} className="flex gap-2 max-w-3xl mx-auto">
          <input
            name="input"
            type="text"
            placeholder="Ask about SEC filings..."
            disabled={status === "streaming"}
            className="flex-1 rounded border px-3 py-2 disabled:opacity-50"
          />
          {status === "streaming" ? (
            <button
              type="button"
              onClick={stop}
              className="rounded bg-red-600 px-4 py-2 text-white font-medium hover:bg-red-700"
            >
              Stop
            </button>
          ) : (
            <button
              type="submit"
              className="rounded bg-blue-600 px-4 py-2 text-white font-medium hover:bg-blue-700"
            >
              Send
            </button>
          )}
        </form>
      </footer>
    </div>
  );
}
