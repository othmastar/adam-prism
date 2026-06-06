import requests
import uuid
import json
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
OLLAMA_URL = "http://localhost:11434/api/embeddings"
EMBED_MODEL = "nomic-embed-text"
DIM = 768

client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

def embed(text):
    r = requests.post(OLLAMA_URL, json={"model": EMBED_MODEL, "prompt": text})
    r.raise_for_status()
    return r.json()["embedding"]

def ensure_collection(name):
    try:
        client.get_collection(name)
        print(f"  Collection '{name}' exists, will overwrite")
        client.delete_collection(name)
    except:
        print(f"  Collection '{name}' does not exist, creating")
    client.create_collection(name, vectors_config=VectorParams(size=DIM, distance=Distance.COSINE))

def populate(collection_name, docs):
    print(f"\n{'='*60}")
    print(f"Populating: {collection_name}")
    print(f"{'='*60}")
    ensure_collection(collection_name)
    points = []
    for i, doc in enumerate(docs):
        print(f"  [{i+1}/{len(docs)}] Embedding: {doc['text'][:70]}...")
        vec = embed(doc["text"])
        points.append(PointStruct(
            id=str(uuid.uuid4()),
            vector=vec,
            payload=doc
        ))
    client.upsert(collection_name, points=points)
    count = client.count(collection_name)
    print(f"  ✅ {count.count} points in '{collection_name}'")

def search_and_print(collection_name, query, top=3):
    vec = embed(query)
    results = client.query_points(collection_name, query=vec, limit=top).points
    print(f"\n--- Search '{collection_name}': '{query}' ---")
    for r in results:
        print(f"  score={r.score:.4f} | {r.payload['text'][:120]}...")

# ===== FRONTEND_SERVICES =====
frontend_docs = [
    {"text": "Adam Prism frontend uses Next.js 16 with App Router, leveraging React Server Components for performance. The project is structured under /frontend/ with src/app, src/components, src/store, src/lib, and src/hooks directories.", "category": "project-structure", "source": "architecture-doc"},
    {"text": "State management uses Zustand v5 with a single large store split into logical slices: chat, engine, monitor, pipeline, tools, knowledge, notebook, settings, and ui slices. Each slice has typed interfaces and actions.", "category": "state-management", "source": "architecture-doc"},
    {"text": "The Zustand store contains approximately 45 state properties and 40 actions across all slices. State is persisted to localStorage via zustand/middleware persist, with selective hydration for critical UI state like theme and sidebar visibility.", "category": "state-management", "source": "architecture-doc"},
    {"text": "UI components use shadcn/ui primitives (47 total) including Button, Dialog, DropdownMenu, Popover, Tooltip, Command, Sheet, Tabs, and more. All primitives are customized with Tailwind CSS v4 using CSS variables for theming.", "category": "components", "source": "architecture-doc"},
    {"text": "Tailwind CSS v4 is configured with a custom design system using CSS variables for colors (background, foreground, primary, secondary, muted, accent, destructive), border radius, and spacing. RTL support is enabled via the 'dir' attribute on html element.", "category": "styling", "source": "architecture-doc"},
    {"text": "14 custom Adam components exist: ChatInterface, ChatSidebar, ChatMessage, ChatInput, ChatControls, FloatingMonitor, IssueTerminal, ModelOrchestrator, TerminalModal, PipelineView, KnowledgeBase, NotebookEditor, ToolPanel, and SettingsPanel.", "category": "components", "source": "architecture-doc"},
    {"text": "ChatInterface is the main chat view with message list, streaming response display, tool call rendering, and action trace panel. It handles both FastAPI backend responses and fallback Ollama proxy responses.", "category": "chat", "source": "architecture-doc"},
    {"text": "ChatSidebar provides conversation history, model selection dropdown, system prompt editor, and quick action buttons. It collapses to icons on narrow screens and persists its state in the Zustand store.", "category": "chat", "source": "architecture-doc"},
    {"text": "FloatingMonitor is a draggable overlay showing real-time system metrics: CPU, GPU, memory usage, internet connectivity status, and active tool calls. It updates every 5 seconds via the engine health endpoint.", "category": "monitoring", "source": "architecture-doc"},
    {"text": "IssueTerminal and ModelOrchestrator are modal components that implement mutual exclusion: opening one closes the other. They have z-index hierarchy: modals at z-[80], ActionTrace at z-[70], FloatingMonitor at z-[50].", "category": "components", "source": "architecture-doc"},
    {"text": "The API client in lib/api.ts contains 25+ functions organized by domain: chat (sendMessage, streamMessage, getHistory), engine (getHealth, getStatus, heal), tools (list, execute, getResult), knowledge (search, add, delete), and settings (get, update).", "category": "api-client", "source": "architecture-doc"},
    {"text": "Two custom hooks are used: useChat (manages chat state, streaming, tool calls, and auto-scroll) and useEngineHealth (polls engine health every 5 seconds, updates FloatingMonitor, triggers auto-healing when subsystems fail).", "category": "hooks", "source": "architecture-doc"},
    {"text": "Four lib files support the frontend: lib/api.ts (API client), lib/utils.ts (Tailwind CSS merge utility with cn()), lib/constants.ts (model names, color themes, default settings), and lib/types.ts (TypeScript interfaces for store slices, API responses, and component props).", "category": "lib", "source": "architecture-doc"},
    {"text": "7 main views render under a shared layout: Chat (primary interface), Monitor (system metrics dashboard), Pipeline (agent pipeline visualization), Knowledge (vector search browser), Notebook (persistent notes editor), Tools (tool registry and permissions), and Settings (configuration panel).", "category": "views", "source": "architecture-doc"},
]
populate("frontend_services", frontend_docs)
search_and_print("frontend_services", "How is chat implemented in the frontend?")

# ===== BACKEND_SERVICES =====
backend_docs = [
    {"text": "The AdamPrismEngine in core/engine.py is the central processing unit comprising 1200 lines and a 9-step processing cycle: receive input, guard check, intent classification, context building, tool selection, execution, response generation, ethics check, and output guard.", "category": "engine-architecture", "source": "architecture-doc"},
    {"text": "The FastAPI server exposes 33 API endpoints organized into groups: engine (5 endpoints for health, status, heal, config, restart), chat (4 endpoints for send, stream, history, clear), tools (6 endpoints for list, execute, status, cancel, result, history), and knowledge (5 endpoints for search, add, delete, collections, stats).", "category": "api", "source": "architecture-doc"},
    {"text": "29 tools are registered in the tool system: browser (navigate, click, type, scroll, screenshot, extract), mouse (move, click, double-click, right-click, drag), keyboard (type, hotkey, press), clipboard (copy, paste, read), screen (capture, record, ocr), window (list, focus, resize, move, close), file (read, write, list, search), knowledge (query, add, delete), and notebook (read, write, append).", "category": "tools", "source": "architecture-doc"},
    {"text": "6 Qdrant collections support RAG: knowledge (project documentation and learned information), conversations (past chat sessions for context retrieval), patterns (repeated user behavior and solution patterns), reasoning (chain-of-thought traces for meta-learning), summaries (compressed conversation summaries), and connections (relationships between concepts and entities).", "category": "vector-database", "source": "architecture-doc"},
    {"text": "Security uses a 5-layer guard system: InputGuard (sanitizes and validates all incoming text, blocks injection attempts), OutputGuard (filters sensitive information from responses), ToolPermission (checks tool execution authorization against user role matrix), Ethics (validates responses against ethical guidelines and core values), and Coordinator (manages guard interaction and conflict resolution).", "category": "security", "source": "architecture-doc"},
    {"text": "MemorySystem provides three-tier memory: short-term (in-memory dictionary with LRU eviction for recent context), episodic (Qdrant-backed storage of conversation episodes with timestamps and emotional valence), and vector (semantic search across all Qdrant collections for relevant context retrieval).", "category": "memory", "source": "architecture-doc"},
    {"text": "The Notebook system uses file-based persistent storage with daily files under data/notebook/YYYY-MM-DD.md, connections.md for entity relationships, pending.md for action items, summaries.md for daily digests, and user_profile.md for persistent user preferences and identity.", "category": "notebook", "source": "architecture-doc"},
    {"text": "Auto-healing in the engine monitors all subsystems every 60 seconds via a watchdog thread. When a subsystem fails, it attempts re-initialization through stub objects that provide graceful degradation. The /api/engine/heal endpoint triggers healing across all 9 subsystems.", "category": "auto-healing", "source": "architecture-doc"},
    {"text": "Context building in the 9-step cycle retrieves relevant information from all 6 Qdrant collections based on the intent-classified user input. Results are ranked by cosine similarity and merged into a context window that includes conversation history, knowledge snippets, and pattern matches.", "category": "rag-pipeline", "source": "architecture-doc"},
    {"text": "The llama.cpp server running on port 8080 provides local inference with the merged Adam V8 GGUF model (Q8_0, 7.5GB) on RTX 3060 GPU. Inference achieves ~46 tokens/second generation and ~200 tokens/second prompt processing with Egyptian Arabic LoRA adapter support.", "category": "inference", "source": "architecture-doc"},
    {"text": "The engine processes tool calls through a JSON-based protocol: tools respond with JSON containing _tool field and params. Each tool has a lifecycle: queued, running, completed, or failed. Tool timeouts and retry policies are configurable per tool category.", "category": "tool-execution", "source": "architecture-doc"},
    {"text": "WebSocket connections provide real-time streaming for chat responses, tool execution progress, and system health updates. The backend supports SSE (Server-Sent Events) as a fallback when WebSockets are unavailable or behind proxies.", "category": "real-time", "source": "architecture-doc"},
    {"text": "The Ollama server on port 11434 runs the merged Adam V8 model and provides a fallback inference path. It is configured with CUDA GPU acceleration via OLLAMA_LLM_LIBRARY=cuda_v12 and LD_LIBRARY_PATH pointing to custom CUDA libraries.", "category": "inference", "source": "architecture-doc"},
]
populate("backend_services", backend_docs)
search_and_print("backend_services", "How does the engine processing cycle work?")

# ===== ARCHITECTURE_DOCS =====
arch_docs = [
    {"text": "Local-first architecture: all inference runs locally via Ollama with GGUF models on RTX 3060 GPU. No cloud APIs are required for core functionality. This ensures privacy, low latency, and offline capability for the Adam Prism system.", "category": "principle", "source": "architecture-doc"},
    {"text": "Module independence: every subsystem (engine, memory, tools, security, notebook, monitoring) works standalone with well-defined interfaces. Modules communicate through typed protocols and can be started, stopped, or replaced independently without affecting other modules.", "category": "principle", "source": "architecture-doc"},
    {"text": "Zero-trust security model: every input is sanitized, every output is filtered, every tool execution requires permission, and every response passes through ethics validation. No implicit trust is granted to any layer of the system regardless of origin.", "category": "principle", "source": "architecture-doc"},
    {"text": "Auto-healing architecture: a watchdog thread monitors 9 subsystems (engine, api, memory, tools, security, notebook, monitoring, pipeline, knowledge) every 60 seconds. Failed subsystems are re-initialized through stub objects that provide graceful degradation instead of hard failures.", "category": "pattern", "source": "architecture-doc"},
    {"text": "RAG pipeline design: context building in the engine includes automatic vector search across all 6 Qdrant collections. Results are ranked by cosine similarity score and merged into a unified context window. The pipeline supports hybrid search (vector + keyword) for improved retrieval.", "category": "pattern", "source": "architecture-doc"},
    {"text": "Active agent pattern: the system prompt is rewritten to encourage autonomous tool-using agent behavior. The agent actively searches for information, selects appropriate tools, and chains multiple tool calls to accomplish complex tasks without step-by-step human guidance.", "category": "pattern", "source": "architecture-doc"},
    {"text": "Conversation memory uses a three-tier approach: short-term (recent N messages in context window), medium-term (episodic memory in Qdrant with timestamps and summaries), and long-term (knowledge base with curated facts and learned patterns). Each tier has different retention and retrieval strategies.", "category": "pattern", "source": "architecture-doc"},
    {"text": "State persistence strategy: Zustand store syncs to localStorage for UI state, Qdrant collections store vector embeddings for semantic retrieval, file-based notebook stores structured daily notes and connections, and engine state is ephemeral with recovery via health checks and re-initialization.", "category": "pattern", "source": "architecture-doc"},
    {"text": "Error handling follows the principle of graceful degradation: if a subsystem fails, stub objects provide minimal functionality rather than crashing the entire system. Errors are logged with context, reported through the health monitoring system, and queued for automatic healing.", "category": "principle", "source": "architecture-doc"},
    {"text": "Tool execution protocol uses a standardized JSON format: each tool call includes tool name, parameters, timeout, and retry policy. Tool responses include status, result data, execution time, and error details. The protocol supports both synchronous and streaming execution modes.", "category": "pattern", "source": "architecture-doc"},
    {"text": "The frontend-backend communication pattern uses REST for query operations (GET health, status, history), Server-Sent Events for streaming responses (chat, tool execution progress), and periodic polling for monitoring (health checks every 5 seconds from FloatingMonitor).", "category": "pattern", "source": "architecture-doc"},
    {"text": "Security principle of least privilege: each tool has granular permission settings per user role. Tool execution requires explicit authorization from the ToolPermission guard. Sensitive operations (file write, browser navigation, clipboard access) require additional confirmation.", "category": "principle", "source": "architecture-doc"},
    {"text": "The system uses Egyptian Arabic as its primary language with English technical terms. This is enforced through the system prompt and LoRA fine-tuning. The model was fine-tuned on the ADAM_COMPLETE dataset (2317 conversations, ~2.2M tokens) with QLoRA on Gemma 4 E4B.", "category": "identity", "source": "architecture-doc"},
    {"text": "Active self-improvement: the agent periodically searches GitHub and news sources for new tools, libraries, and techniques. Findings are stored in the knowledge Qdrant collection and referenced during context building. This enables continuous evolution without manual retraining.", "category": "pattern", "source": "architecture-doc"},
]
populate("architecture_docs", arch_docs)
search_and_print("architecture_docs", "What are the core architecture principles?")

print("\n" + "="*60)
print("🎯 ALL COLLECTIONS POPULATED AND VERIFIED SUCCESSFULLY")
print("="*60)
