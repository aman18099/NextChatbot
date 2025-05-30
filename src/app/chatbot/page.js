"use client";
import { useEffect, useState } from "react";
import { supabase } from "../../utils/supabaseClient";

export default function ChatbotPage() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(true);

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

  if (loading) return <div>Loading...</div>;
  if (!email) return <div>Please log in to use the chatbot.</div>;

  return <div>hi {email}</div>;
}
