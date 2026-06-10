import { api, ChatThread } from "@/lib/api";
import { useEffect, useState } from "react";

interface ThreadSidebarProps {
  currentThreadId: string;
  onSwitchThread: (id: string) => void;
}

export default function ThreadSidebar({ currentThreadId, onSwitchThread }: ThreadSidebarProps) {
  const [threads, setThreads] = useState<ChatThread[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getThreads().then((list) => {
      setThreads(list);
      setLoading(false);
    });
  }, []);

  async function handleNew() {
    const thread = await api.createThread();
    setThreads((prev) => [thread, ...prev]);
    onSwitchThread(thread.id);
  }

  return (
    <aside className="w-64 shrink-0 bg-white border-r border-gray-200 flex flex-col h-screen">
      <div className="p-3 border-b border-gray-200">
        <button
          onClick={handleNew}
          className="w-full rounded-lg bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700 transition-colors"
        >
          + New Chat
        </button>
      </div>

      <nav className="flex-1 overflow-y-auto p-2 space-y-1">
        {loading && (
          <div className="text-xs text-gray-400 text-center py-4">Loading...</div>
        )}

        {!loading && threads.length === 0 && (
          <div className="text-xs text-gray-400 text-center py-4">No conversations yet</div>
        )}

        {threads.map((t) => (
          <button
            key={t.id}
            onClick={() => onSwitchThread(t.id)}
            className={`w-full text-left rounded-lg px-3 py-2 text-sm transition-colors ${
              t.id === currentThreadId
                ? "bg-blue-50 text-blue-700 font-medium"
                : "text-gray-700 hover:bg-gray-100"
            }`}
          >
            <span className="line-clamp-1">{t.title}</span>
          </button>
        ))}
      </nav>
    </aside>
  );
}
