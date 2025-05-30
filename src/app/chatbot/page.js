"use client";

import { useEffect, useState } from "react";
import { supabase } from "../../utils/supabaseClient";

export default function ChatbotPage() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [response, setResponse] = useState("");
  const [sending, setSending] = useState(false);
  const [history, setHistory] = useState([]);

  useEffect(() => {
    const getUser = async () => {
      const { data: { user } } = await supabase.auth.getUser();
      if (user && user.email) {
        setEmail(user.email);
      }
      setLoading(false);
    };
    getUser();
  }, []);

  const handleSend = async (e) => {
    e.preventDefault();
    setSending(true);
    setResponse("");
    // Add user's message to history
    setHistory((prev) => [...prev, { sender: "user", text: query }]);
    // Replace with your backend endpoint
    const res = await fetch("http://localhost:8000/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query }),
    });
    const data = await res.json();
    setResponse(data.response);
    // Add bot's response to history
    setHistory((prev) => [...prev, { sender: "bot", text: data.response }]);
    setSending(false);
    setQuery("");
  };

  const handleLogout = async () => {
    await supabase.auth.signOut();
    window.location.href = "/login";
  };

  if (loading) return <div className="flex items-center justify-center min-h-screen">Loading...</div>;
  if (!email) return <div className="flex items-center justify-center min-h-screen">Please log in to use the chatbot.</div>;

  return (
    <div className="flex items-center justify-center min-h-screen bg-background relative">
      <button
        onClick={handleLogout}
        className="absolute top-6 right-6 px-4 py-2 bg-red-500 text-white rounded font-semibold hover:bg-red-600 transition-colors z-10"
      >
        Logout
      </button>
      <div className="w-full max-w-2xl bg-white dark:bg-black rounded-lg shadow-lg p-8 flex flex-col gap-6 border border-gray-200 dark:border-gray-800">
        <h1 className="text-2xl font-bold text-center mb-4">Chatbot</h1>
        <div className="text-lg font-semibold mb-2">hi {email} </div>

        <div className="flex flex-col gap-2 mt-4 max-h-96 overflow-y-auto">
          {history.length === 0 && (
            <div className="text-gray-400 text-center">Start the conversation!</div>
          )}
          {history.map((msg, idx) => (
            <div
              key={idx}
              className={
                msg.sender === "user"
                  ? "self-end bg-blue-500 text-white px-4 py-2 rounded-lg max-w-xs ml-auto"
                  : "self-start bg-gray-200 dark:bg-gray-800 text-gray-900 dark:text-gray-100 px-4 py-2 rounded-lg max-w-xs"
              }
            >
              {msg.text}
            </div>
          ))}
        </div>
        {/* End chat history */}
        {response && (
          <div className="mt-4 p-4 bg-gray-100 dark:bg-gray-900 rounded text-gray-800 dark:text-gray-100 border border-gray-200 dark:border-gray-700">
            <span className="font-bold">Bot:</span> {response}
          </div>
        )}

        <form onSubmit={handleSend} className="flex gap-2">
          <input
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="Ask something..."
            className="flex-1 px-4 py-2 border rounded focus:outline-none focus:ring focus:border-blue-400 bg-gray-50 dark:bg-gray-900"
            required
          />
          <button
            type="submit"
            disabled={sending}
            className="px-6 py-2 bg-foreground text-background rounded font-semibold hover:bg-gray-800 dark:hover:bg-gray-200 dark:hover:text-black transition-colors"
          >
            {sending ? "Sending..." : "Send"}
          </button>
        </form>
        {/* Chat history */}
        
      </div>
    </div>
  );
}
