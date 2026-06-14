import { NextRequest, NextResponse } from "next/server";

export async function GET(req: NextRequest) {
  try {
    const url = new URL(req.url);
    const ollamaUrl = url.searchParams.get("ollamaUrl") || "http://localhost:11434";

    const response = await fetch(`${ollamaUrl}/api/tags`, {
      method: "GET",
      signal: AbortSignal.timeout(5000),
    });

    if (!response.ok) {
      return NextResponse.json({ models: [] }, { status: 200 });
    }

    const data = await response.json();
    const models = (data.models || []).map((m: { name: string; size?: number; modified_at?: string }) => ({
      name: m.name,
      size: m.size,
      modifiedAt: m.modified_at,
    }));

    return NextResponse.json({ models });
  } catch {
    return NextResponse.json({ models: [] }, { status: 200 });
  }
}
