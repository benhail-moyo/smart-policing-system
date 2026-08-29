import { NextRequest, NextResponse } from "next/server";
import { backendApiUrl } from "@/lib/backend-api";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ patternId: string }> }
) {
  try {
    const { patternId } = await params;

    const token = request.headers.get("authorization")?.replace("Bearer ", "");
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };
    if (token) headers["Authorization"] = `Bearer ${token}`;

    const response = await fetch(`${backendApiUrl}/patterns/${patternId}/timeline`, {
      method: "GET",
      headers,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      return NextResponse.json(
        { error: error.error || "Failed to get pattern timeline" },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Pattern timeline API error:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
