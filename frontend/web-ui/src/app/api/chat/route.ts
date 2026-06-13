import { NextRequest, NextResponse } from "next/server";

const VISION_MODELS = ["llava", "gemma3-vision", "bakllava", "moondream", "llama3.2-vision", "minicpm-v"];
const IMAGE_EXTS = [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"];

function hasImageRef(messages: any[]): boolean {
  for (const msg of messages) {
    const content = (msg.content || "").trim();
    // strip quotes around filenames
    const cleaned = content.replace(/^["'\s]+|["'\s]+$/g, "");
    if (IMAGE_EXTS.some(ext => cleaned.toLowerCase().endsWith(ext))) return true;
  }
  return false;
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { messages, model, temperature, top_p, top_k, stream, ollamaUrl, systemPrompt } = body;

    const modelName = model || "gemma4:e4b";
    const isVisionModel = VISION_MODELS.some(vm => modelName.toLowerCase().includes(vm));

    // Block image references if model doesn't support vision
    if (hasImageRef(messages) && !isVisionModel) {
      const warning = "⚠️ هذا الموديل النصي لا يدعم معالجة الصور. لاستخدام الصور، غيّر الموديل إلى multimodal مثل llava أو gemma3-vision.";
      if (stream) {
        const encoder = new TextEncoder();
        const chunks = [
          encoder.encode(`{"message":{"role":"assistant","content":""}}\n`),
          encoder.encode(`{"message":{"role":"assistant","content":"${warning}"}}\n`),
          encoder.encode(`{"done":true}\n`),
        ];
        const streamContent = new ReadableStream({
          start(controller) {
            chunks.forEach(c => controller.enqueue(c));
            controller.close();
          },
        });
        return new Response(streamContent, {
          headers: { "Content-Type": "text/event-stream", "Cache-Control": "no-cache" },
        });
      }
      return NextResponse.json({ message: { role: "assistant", content: warning }, done: true });
    }

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
