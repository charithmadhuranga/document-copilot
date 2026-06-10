import { env } from "./env";
import { apiFetch } from "./http";

const BASE = env.apiBaseUrl;

export interface ChatThread {
  id: string;
  title: string;
  createdAt: string;
  updatedAt?: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  createdAt?: string;
}

export const api = {
  async getThreads(): Promise<ChatThread[]> {
    return apiFetch<ChatThread[]>(`${BASE}/api/threads`);
  },

  async createThread(title = "New Chat"): Promise<ChatThread> {
    return apiFetch<ChatThread>(`${BASE}/api/threads`, {
      method: "POST",
      body: JSON.stringify({ title }),
    });
  },

  async getMessages(threadId: string): Promise<ChatMessage[]> {
    return apiFetch<ChatMessage[]>(`${BASE}/api/threads/${threadId}/messages`);
  },
};
