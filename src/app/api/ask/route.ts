import { NextResponse, NextRequest } from "next/server";
import { exec } from "child_process";
import {supabase} from "../../../supabase/client";
import { max } from "date-fns";

export async function POST(req: NextRequest) {
  const authHeader = req.headers.get("authorization");
  const token = authHeader?.replace("Bearer ", "");
  // const token = "eyJhbGciOiJIUzI1NiIsImtpZCI6Ii8xWTFLWHlGaXVUSUw4NjgiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL214a29ycGZqZmRhd2FmaWNhaWdvLnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiJlNzc3MjVkZi02NDY1LTQzYTAtOTZmMC1iMjVjYTUxNGFhOWIiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzQ4ODQ5MjIwLCJpYXQiOjE3NDg4NDU2MjAsImVtYWlsIjoieWFzaHIzMDM3QGdtYWlsLmNvbSIsInBob25lIjoiIiwiYXBwX21ldGFkYXRhIjp7InByb3ZpZGVyIjoiZW1haWwiLCJwcm92aWRlcnMiOlsiZW1haWwiXX0sInVzZXJfbWV0YWRhdGEiOnsiZW1haWxfdmVyaWZpZWQiOnRydWV9LCJyb2xlIjoiYXV0aGVudGljYXRlZCIsImFhbCI6ImFhbDEiLCJhbXIiOlt7Im1ldGhvZCI6InBhc3N3b3JkIiwidGltZXN0YW1wIjoxNzQ4Nzk2NTY3fV0sInNlc3Npb25faWQiOiI0YjZjNDFiNC1lZjJkLTQ2MDctODliMy1jYzVjNDc4MTZjNWQiLCJpc19hbm9ueW1vdXMiOmZhbHNlfQ.RkwVLPuCW31IXOlRVRUvdoF8HPAo0g6Rwb2r-NODhLo"

  const { data: { user }, error } = await supabase.auth.getUser(token);
    if (error || !user) {
    return NextResponse.json({ error: "Invalid token" }, { status: 401 });
  }
  const userId = user?.id;
  console.log("Authenticated user:", user);
  const body = await req.json();
  const text = body.question;
  // const text = "hello";
  // let text = "what would be the budget for the trip";
  const outputText = new Promise((resolve, reject) => {
    
    exec(
      `venv\\Scripts\\python.exe src/scripts/rag_process.py "${text}" "${userId}"`,
      { maxBuffer: 1024 * 1024 * 50 },
      (error, stdout, stderr) => {
        if (error) {
          console.error(`Error executing script: ${error.message}`);
          reject(error)
        }
        resolve(stdout);
      }
    );
  });

  const output = await outputText;
  console.log("Output from Python script:", output);
  return NextResponse.json({
    status: "success",
    message: "Python script executed successfully",
    output: output,
  });
}

export async function GET(req: NextRequest) {
  const authHeader = req.headers.get("authorization");
  const token = authHeader?.replace("Bearer ", "");
  // Get authenticated user
  const {
    data: { user },
    error: authError,
  } = await supabase.auth.getUser(token);

  if (authError || !user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const userId = user.id;

  const { data, error } = await supabase
    .from("queries")
    .select("*")
    .eq("user_id", userId)
    .order("created_at", { ascending: true });

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  return NextResponse.json({ queries: data });
}
