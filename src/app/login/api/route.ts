import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  const { email, password } = await request.json() as { email: string; password: string };
  // Mock authentication logic
  if (email === "test@example.com" && password === "password123") {
    return NextResponse.json(
      { success: true, message: "Login successful" },
      { status: 200 }
    );
  } else {
    return NextResponse.json(
      { success: false, message: "Invalid credentials" },
      { status: 401 }
    );
  }
}
