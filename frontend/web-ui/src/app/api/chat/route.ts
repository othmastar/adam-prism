import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { messages, model, temperature, top_p, top_k, stream, ollamaUrl, systemPrompt } = body;

    const baseUrl = ollamaUrl || "http://localhost:11434";
    
    const formattedMessages = [];
    
    if (systemPrompt) {
      formattedMessages.push({
        role: "system",
        content: systemPrompt,
      });
    }
    
    for (const msg of messages) {
      formattedMessages.push({
        role: msg.role,
        content: msg.content,
      });
    }

    if (stream) {
      const response = await fetch(`${baseUrl}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model: model || "gemma4:e4b",
          messages: formattedMessages,
          stream: true,
          options: {
            temperature: temperature ?? 0.7,
            top_p: top_p ?? 0.9,
            top_k: top_k ?? 40,
          },
        }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        return NextResponse.json(
          { error: `Ollama error: ${response.status} - ${errorText}` },
          { status: response.status }
        );
      }

      // Forward the stream
      return new Response(response.body, {
        headers: {
          "Content-Type": "text/event-stream",
          "Cache-Control": "no-cache",
          Connection: "keep-alive",
        },
      });
    } else {
      const response = await fetch(`${baseUrl}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model: model || "gemma4:e4b",
          messages: formattedMessages,
          stream: false,
          options: {
            temperature: temperature ?? 0.7,
            top_p: top_p ?? 0.9,
            top_k: top_k ?? 40,
          },
        }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        return NextResponse.json(
          { error: `Ollama error: ${response.status} - ${errorText}` },
          { status: response.status }
        );
      }

      const data = await response.json();
      return NextResponse.json(data);
    }
  } catch (error) {
    console.error("Chat API error:", error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Internal server error" },
      { status: 500 }
    );
  }
}
