"use client";
import React, { useState, FormEvent } from "react";
import { supabase } from "../../supabase/client";
import { useRouter } from "next/navigation";

export default function Login() {
  const [email, setEmail] = useState<string>("");
  const [password, setPassword] = useState<string>("");
  const [error, setError] = useState<string>("");
  const [success, setSuccess] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);
  const router = useRouter();

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    setLoading(true);

    const { error: loginError } = await supabase.auth.signInWithPassword({
      email,
      password,
    });

    setLoading(false);

    if (loginError) {
      setError(loginError.message);
      return;
    }

    setSuccess("Login successful!");
    router.push("/chatbot");
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <form
        onSubmit={handleSubmit}
        className="bg-white dark:bg-black p-8 rounded shadow-md w-full max-w-sm flex flex-col gap-4 border border-gray-200 dark:border-gray-800"
      >
        <h2 className="text-2xl font-bold mb-4 text-center">Login</h2>
        <label className="flex flex-col gap-1">
          <span className="text-sm font-medium">Email</span>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="px-3 py-2 border rounded focus:outline-none focus:ring focus:border-blue-400 bg-gray-50 dark:bg-gray-900"
            required
          />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-sm font-medium">Password</span>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="px-3 py-2 border rounded focus:outline-none focus:ring focus:border-blue-400 bg-gray-50 dark:bg-gray-900"
            required
          />
        </label>
        <button
          type="submit"
          className="mt-4 bg-foreground text-background py-2 rounded font-semibold hover:bg-gray-800 dark:hover:bg-gray-200 dark:hover:text-black transition-colors"
          disabled={loading}
        >
          {loading ? "Logging in..." : "Log In"}
        </button>
        {error && <div className="text-red-500 text-sm">{error}</div>}
        {success && <div className="text-green-500 text-sm">{success}</div>}
      </form>
    </div>
  );
}
