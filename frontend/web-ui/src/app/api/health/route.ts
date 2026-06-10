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
      return NextResponse.json(
        { connected: false, error: `Ollama returned ${response.status}` },
        { status: 200 }
      );
    }

    const data = await response.json();
    const models = (data.models || []).map((m: { name: string }) => m.name);

    return NextResponse.json({
      connected: true,
      models,
      modelCount: models.length,
    });
  } catch (error) {
    return NextResponse.json(
      {
        connected: false,
        error: error instanceof Error ? error.message : "Cannot reach Ollama",
        models: [],
        modelCount: 0,
      },
      { status: 200 }
    );
  }
}
