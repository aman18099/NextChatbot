"use client";

import { useRouter } from "next/navigation";
import { supabase } from "../../supabase/client";
import { useState, useRef, useEffect } from "react";
import {
  formatDate,
  formatDateTime,
} from "../../utils/date_formatter";

type Message = {
  role: "assistant" | "user";
  content: string;
  timestamp: string;
};

export default function DashboardPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const [input, setInput] = useState("");
  const [userId, setUserId] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement | null>(null);

  const router = useRouter();

  async function getToken() {
    const session = await supabase.auth.getSession();
    const token = session?.data?.session?.access_token;
    // console.log("Supabase token:", token);
    return token;
  }

  const fetchQueries = async () => {
    const token = await getToken();
    if (!token) {
      console.error("No token found, redirecting to login");
      router.push("/login");
      return;
    }

    try {
      const res = await fetch("/api/ask", {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        credentials: "include", // include Supabase auth cookies
      });

      if (!res.ok) {
        throw new Error("Failed to fetch queries");
      }

      const data = await res.json();
      const messages = data.queries.flatMap((q) => [
        {
          role: "user",
          content: q.question,
          timestamp: q.created_at,
        },
        {
          role: "assistant",
          content: q.answer,
          timestamp: q.created_at,
        },
      ]);
      console.log("Fetched messages:", messages);
      setMessages((prev) => [...prev, ...messages]);
    } catch (error) {
      console.error("Error fetching queries:", error);
    }
  };

  useEffect(() => {
    supabase.auth.getUser().then(({ data }) => {
      setUserId(data.user?.id ?? null);
    });
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    fetchQueries();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || !userId) return;
    const question = input.trim();
    setMessages((prev) => [
      ...prev,
      { role: "user", content: question, timestamp: new Date().toISOString() },
    ]);
    setInput("");
    setIsTyping(true);
    try {
      const token = await getToken();
      const res = await fetch("https://nextchatbot-6631.onrender.com/api/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json", 
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({ question, user_id: userId }),
      });
      const data = await res.json();
      setIsTyping(false);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.output || data.error || "No response",
          timestamp: new Date().toISOString(),
        },
      ]);
    } catch (error: any) {
      setIsTyping(false);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `⚠️ Error: ${error.message}`,
          timestamp: new Date().toISOString(),
        },
      ]);
    }
  };

  const handleLogout = async () => {
    await supabase.auth.signOut();
    router.push("/login");
  };

  return (
    <div className="flex h-screen text-white bg-gray-900">
      {/* Sidebar */}
      <div className="w-64 h-screen bg-gray-900 text-white flex flex-col justify-between p-4 shadow-lg">
        <div>
          <p className="text-gray-400 mb-4">
            Empowering your data queries with intelligent chat-driven insights.
          </p>
        </div>

        <button
          onClick={handleLogout}
          className="w-full mt-auto border border-red-600 hover:bg-red-900 py-2 px-4 rounded text-white font-semibold"
        >
          Logout
        </button>
      </div>

      {/* Chat Panel */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="px-4 py-3 bg-gray-800 border-b border-gray-700 text-lg font-semibold">
          NBC Assistant
        </div>

        {/* Chat Area */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((msg, idx) => {
            const currentDate = new Date(msg.timestamp);
            const prevDate =
              idx > 0 ? new Date(messages[idx - 1].timestamp) : null;
            const showDateSeparator =
              !prevDate ||
              currentDate.toDateString() !== prevDate.toDateString();

            return (
              <div key={idx}>
                {showDateSeparator && (
                  <div className="flex justify-center mb-4">
                    <span className="text-gray-400 text-xs px-3 py-1 rounded-full bg-gray-700">
                      {formatDate(currentDate)}
                    </span>
                  </div>
                )}

                <div
                  className={`flex flex-col ${
                    msg.role === "user" ? "items-end" : "items-start"
                  }`}
                >
                  <div
                    className={`max-w-lg px-4 py-3 rounded-lg text-sm ${
                      msg.role === "user"
                        ? "bg-indigo-600 text-white"
                        : "bg-gray-700 text-gray-100"
                    }`}
                  >
                    {msg.content}
                  </div>
                  {msg.timestamp && !isNaN(new Date(msg.timestamp).getTime()) ? (
                    <span className="text-xs text-gray-400">
                      {new Date(msg.timestamp).toLocaleString("en-IN", { 
                        timeZone: "Asia/Kolkata", 
                        hour: "2-digit", 
                        minute: "2-digit", 
                        hour12: true 
                      })}
                    </span>
                  ) : (
                    <span className="text-xs text-gray-400">Invalid Date</span>
                  )}
                </div>
              </div>
            );
          })}
          {isTyping && (
            <div className="flex justify-start">
              <div className="max-w-lg px-4 py-1 rounded-lg text-sm bg-gradient-to-r from-indigo-700 via-purple-700 to-pink-700 text-white flex items-center space-x-2">
                <span className="font-medium">Thinking</span>
                <span className="flex space-x-1">
                  <span className="dot text-pink-300 animate-bounce">.</span>
                  <span className="dot text-yellow-300 animate-bounce delay-200">
                    .
                  </span>
                  <span className="dot text-green-300 animate-bounce delay-400">
                    .
                  </span>
                </span>
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Chat Input */}
        <form
          onSubmit={handleSubmit}
          className="p-4 border-t border-gray-700 bg-gray-800"
        >
          <div className="flex">
            <input
              type="text"
              className="flex-1 bg-gray-700 text-white px-4 py-2 rounded-l-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
              placeholder="Send a message..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
            />
            <button
              type="submit"
              className="bg-indigo-600 hover:bg-indigo-700 px-6 py-2 rounded-r-md text-white"
              disabled={!input.trim() || !userId}
            >
              Send
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
