"use client";

import { useAppStore, Message, getModeInfo, CognitiveMode, ProcessingStep } from "@/lib/store";
import { sendChatMessage, fetchSessions, fetchSession, createSession, addMessageToSession, syncSessionMessages, deleteSessionOnServer, uploadFile, checkApiHealth, getFastApiUrl, ChatResponse } from "@/lib/api";
import { AdamLogo } from "./adam-logo";
import { PermissionDialog } from "./permission-dialog";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import {
  Send,
  Menu,
  Sparkles,
  User,
  AlertCircle,
  RotateCcw,
  Brain,
  Clock,
  Database,
  Zap,
  Volume2,
  Square,
  Trash2,
  Paperclip,
  X,
  Archive,
  Plus,
  MessageSquare,
  Check,
  Wrench,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useCallback, useMemo, useRef, useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import { CapabilityBubbles } from "./capability-bubbles";
import { ShieldPulse } from "./shield-pulse";
import { VoiceButton } from "./voice-button";
import { sendAudio } from "@/lib/api";

function TypingIndicator() {
  return (
    <div className="flex items-center gap-1 px-3 py-2">
      <div className="typing-dot-1 h-2 w-2 rounded-full bg-primary" />
      <div className="typing-dot-2 h-2 w-2 rounded-full bg-cyan-400" />
      <div className="typing-dot-3 h-2 w-2 rounded-full bg-blue-400" />
    </div>
  );
}

// Map capability IDs to cognitive modes they activate
const capabilityModeMap: Record<string, CognitiveMode[]> = {
  "decode": ["analyst", "corrector"],
  "market-analysis": ["analyst", "strategist"],
  "brand-identity": ["communicator", "strategist"],
  "global-trade": ["analyst", "researcher", "strategist"],
  "pentest": ["engineer", "corrector"],
  "remote-control": ["engineer", "builder"],
  "viral": ["communicator", "strategist"],
  "global": ["strategist", "researcher"],
};

const stepIcons: Record<string, { icon: string; labelAr: string; labelEn: string }> = {
  استقبال: { icon: "📩", labelAr: "استقبال الرسالة", labelEn: "Receiving" },
  "فحص الأمان": { icon: "🛡️", labelAr: "فحص الأمان", labelEn: "Security check" },
  "تحليل القصد": { icon: "🎯", labelAr: "تحليل القصد", labelEn: "Analyzing intent" },
  "بناء السياق": { icon: "🧠", labelAr: "بناء السياق", labelEn: "Building context" },
  "البحث في الذاكرة": { icon: "🔍", labelAr: "البحث في الذاكرة", labelEn: "Searching memory" },
  التوليد: { icon: "✍️", labelAr: "توليد الرد", labelEn: "Generating" },
  "تنفيذ أداة": { icon: "🛠️", labelAr: "تنفيذ أداة", labelEn: "Running tool" },
  "التقييم الأخلاقي": { icon: "⚖️", labelAr: "التقييم الأخلاقي", labelEn: "Ethics check" },
  "التسجيل والحفظ": { icon: "💾", labelAr: "حفظ", labelEn: "Saving" },
  "اكتمال الدورة": { icon: "✅", labelAr: "اكتمل", labelEn: "Complete" },
};

function getStepStatus(currentSteps: ProcessingStep[], isArabic: boolean): { icon: string; text: string } | null {
  const running = currentSteps.filter((s) => s.status === "running").pop();
  if (!running) return null;
  const info = stepIcons[running.step] || { icon: "⏳", labelAr: running.step, labelEn: running.step };
  return { icon: info.icon, text: isArabic ? info.labelAr : info.labelEn };
}

function CognitiveModeBadge({ mode, isArabic }: { mode: CognitiveMode; isArabic: boolean }) {
  const info = getModeInfo(mode, isArabic ? "ar" : "en");
  return (
    <Badge
      variant="outline"
      className="text-[10px] gap-1 px-2 py-0.5"
      style={{ borderColor: `${info.color}50`, color: info.color, backgroundColor: `${info.color}15` }}
    >
      <span>{info.icon}</span>
      <span>{info.label}</span>
    </Badge>
  );
}

function AudioPlayButton({ audioUrl, isArabic }: { audioUrl: string; isArabic: boolean }) {
  const [playing, setPlaying] = useState(false);
  const [ended, setEnded] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const getFullUrl = (url: string) => {
    if (url.startsWith("http")) return url;
    const base = getFastApiUrl();
    return `${base}${url}`;
  };

  const stop = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
    }
    setPlaying(false);
    setEnded(false);
  }, []);

  useEffect(() => {
    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.src = "";
      }
    };
  }, []);

  const handlePlay = () => {
    if (playing) {
      stop();
      return;
    }
    setEnded(false);
    const audio = new Audio(getFullUrl(audioUrl));
    audio.crossOrigin = "anonymous";
    audioRef.current = audio;
    audio.onended = () => { setPlaying(false); setEnded(true); };
    audio.onerror = () => { setPlaying(false); };
    audio.play().then(() => setPlaying(true)).catch(() => setPlaying(false));
  };

  const handleReplay = (e: React.MouseEvent) => {
    e.stopPropagation();
    setEnded(false);
    const audio = new Audio(getFullUrl(audioUrl));
    audio.crossOrigin = "anonymous";
    audioRef.current = audio;
    audio.onended = () => { setPlaying(false); setEnded(true); };
    audio.onerror = () => { setPlaying(false); };
    audio.play().then(() => setPlaying(true)).catch(() => setPlaying(false));
  };

  return (
    <div className="flex items-center gap-1">
      {ended ? (
        <button
          onClick={handleReplay}
          className="flex items-center gap-1 px-2 py-1 rounded-lg text-[10px] bg-muted/50 text-muted-foreground hover:text-primary hover:bg-muted transition-all"
          title={isArabic ? "إعادة" : "Replay"}
        >
          <svg className="h-3 w-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="1 4 1 10 7 10" />
            <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10" />
          </svg>
          <span>Replay</span>
        </button>
      ) : (
        <button
          onClick={handlePlay}
          className={cn(
            "flex items-center gap-1 px-2 py-1 rounded-lg text-[10px] transition-all",
            playing
              ? "bg-destructive/20 text-destructive"
              : "bg-muted/50 text-muted-foreground hover:text-primary hover:bg-muted"
          )}
          title={playing ? (isArabic ? "إيقاف" : "Stop") : (isArabic ? "استماع" : "Listen")}
        >
          {playing ? (
            <Square className="h-3 w-3" fill="currentColor" />
          ) : (
            <Volume2 className="h-3 w-3" />
          )}
          <span>{playing ? "Stop" : "Listen"}</span>
        </button>
      )}
    </div>
  );
}

function MessageBubble({ message }: { message: Message }) {
  const { settings } = useAppStore();
  const isArabic = settings.language === "ar";
  const isUser = message.role === "user";

  return (
    <div
      className={cn(
        "flex gap-3 animate-fade-in-up group",
        isUser ? "flex-row-reverse" : "flex-row"
      )}
    >
      {/* Avatar */}
      <div
        className={cn(
          "h-8 w-8 rounded-full flex items-center justify-center shrink-0",
          isUser
            ? "bg-primary/20"
            : "bg-gradient-to-br from-purple-500/30 via-cyan-500/20 to-blue-500/30"
        )}
      >
        {isUser ? (
          <User className="h-4 w-4 text-primary" />
        ) : (
          <AdamLogo size={20} animate={false} />
        )}
      </div>

      {/* Bubble */}
      <div className="max-w-[85%] sm:max-w-[75%] md:max-w-[65%] space-y-1.5">
        {/* Attachment card for user messages */}
        {isUser && message.attachment && (
          <div className="flex items-center gap-3 px-3 py-2 rounded-xl bg-primary/10 border border-primary/20">
            <span className="text-lg">📎</span>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-foreground truncate">{message.attachment.name}</p>
              {message.attachment.preview && (
                <p className="text-[10px] text-muted-foreground truncate">{message.attachment.preview.slice(0, 80)}...</p>
              )}
            </div>
          </div>
        )}
        {/* Mode badge for AI messages */}
        {!isUser && message.mode && (
          <CognitiveModeBadge mode={message.mode} isArabic={isArabic} />
        )}

        {/* GOAP Scratch Pad — visible thinking for AI messages */}
        {!isUser && (() => {
          const spMatch = message.content.match(/<scratch_pad>([\s\S]*?)<\/scratch_pad>/i);
          if (!spMatch) return null;
          const spContent = spMatch[1].trim();
          const goalMatch = spContent.match(/Goal:\s*(.+)/i);
          const actionMatch = spContent.match(/Actions?:?\s*\n?([\s\S]+?)(?=Observation|Reflection|$)/i);
          const refMatch = spContent.match(/Reflection:\s*(.+)/i);
          return (
            <details className="text-[10px] rounded-lg border border-cyan-500/20 bg-cyan-500/5 overflow-hidden group">
              <summary className="px-3 py-1.5 cursor-pointer flex items-center gap-1.5 text-cyan-400 hover:text-cyan-300 select-none">
                <Brain className="h-3 w-3" />
                <span className="font-medium">{isArabic ? "التفكير" : "Thinking"}</span>
                {goalMatch && <span className="text-muted-foreground/60 truncate max-w-[200px]">— {goalMatch[1].trim().slice(0, 60)}</span>}
              </summary>
              <div className="px-3 pb-2 space-y-1 text-muted-foreground">
                {goalMatch && <p><span className="text-cyan-400/80">Goal:</span> {goalMatch[1].trim()}</p>}
                {actionMatch && <p><span className="text-purple-400/80">{isArabic ? "Actions:" : "Actions:"}</span> {actionMatch[1].trim().slice(0, 150)}</p>}
                {refMatch && <p><span className="text-emerald-400/80">Reflection:</span> {refMatch[1].trim().slice(0, 150)}</p>}
              </div>
            </details>
          );
        })()}

        {/* Tool Call Badges for AI messages */}
        {!isUser && (() => {
          const tcMatch = message.content.match(/<tool_call>([\s\S]*?)<\/tool_call>/i);
          if (!tcMatch) return null;
          try {
            const tc = JSON.parse(tcMatch[1].trim());
            return (
              <div className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-amber-500/10 border border-amber-500/20 text-[10px]">
                <Wrench className="h-3 w-3 text-amber-400" />
                <span className="text-amber-400 font-medium">{tc.name}</span>
                {tc.arguments && Object.keys(tc.arguments).length > 0 && (
                  <span className="text-muted-foreground">
                    ({Object.entries(tc.arguments).slice(0, 2).map(([k,v]) => `${k}: ${String(v).slice(0, 30)}`).join(", ")})
                  </span>
                )}
              </div>
            );
          } catch { return null; }
        })()}

        <div
          className={cn(
            "rounded-2xl px-4 py-3",
            isUser
              ? "chat-bubble-user bg-gradient-to-l from-primary to-purple-600 text-white"
              : "chat-bubble-ai glass"
          )}
        >
          {isUser ? (
            <p className="text-sm whitespace-pre-wrap leading-relaxed">{message.content}</p>
          ) : (
            <div className="text-sm prose prose-sm prose-invert max-w-none prose-pre:whitespace-pre-wrap leading-relaxed [&>*:first-child]:mt-0 [&>*:last-child]:mb-0 break-words">
              <ReactMarkdown>{message.content}</ReactMarkdown>
            </div>
          )}
        </div>

        {/* Audio playback for AI messages — يظهر فقط عند hover */}
        {!isUser && message.audioUrl && (
          <div className="px-1">
            <AudioPlayButton audioUrl={message.audioUrl} isArabic={isArabic} />
          </div>
        )}

        {/* Meta info for AI messages */}
        {!isUser && (message.knowledgeUsed !== undefined || message.durationMs !== undefined) && (
          <div className="flex items-center gap-3 px-1 text-[10px] text-muted-foreground">
            {message.knowledgeUsed !== undefined && message.knowledgeUsed > 0 && (
              <span className="flex items-center gap-1">
                <Database className="h-3 w-3" />
                {isArabic ? `${message.knowledgeUsed} مصدر` : `${message.knowledgeUsed} sources`}
              </span>
            )}
            {message.durationMs !== undefined && (
              <span className="flex items-center gap-1">
                <Clock className="h-3 w-3" />
                {message.durationMs}ms
              </span>
            )}
            {message.cycle !== undefined && message.cycle > 0 && (
              <span className="flex items-center gap-1">
                <Zap className="h-3 w-3" />
                {isArabic ? `دورة ${message.cycle}` : `Cycle ${message.cycle}`}
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function WelcomeScreen({
  isArabic,
  onSuggestionClick,
  activeCapability,
}: {
  isArabic: boolean;
  onSuggestionClick: (text: string) => void;
  activeCapability: string | null;
}) {
  const activeModes = activeCapability ? capabilityModeMap[activeCapability] || [] : [];
  const allModes: CognitiveMode[] = ["analyst", "builder", "corrector", "engineer", "researcher", "communicator", "strategist"];

  return (
    <div className="flex-1 flex items-center justify-center p-4 relative min-h-0">
      <div className="text-center max-w-2xl relative z-10">
        {/* Logo with neon glow */}
        <div className="neon-glow inline-block">
          <AdamLogo size={80} animate={true} />
        </div>

        <h1 className="text-2xl font-bold mt-6 prism-text">
          {isArabic ? "مرحباً OthMastar! أنا آدم بريزم" : "Hello OthMastar! I'm Adam Prism"}
        </h1>
        <p className="text-muted-foreground mt-2 text-sm max-w-md mx-auto">
          {isArabic
            ? "توأمك الرقمي الخيالي. اسألني، حلل، ابتكر — أنا هنا لأخذك لأبعد مما تتخيل."
            : "Your fantastical digital twin. Ask, analyze, create — I'm here to take you beyond imagination."}
        </p>

        {/* Cognitive modes showcase — تضيء حسب البطاقة المختارة */}
        <div className="flex flex-wrap justify-center gap-2 mt-4">
          {allModes.map((mode) => {
            const isLit = activeModes.includes(mode);
            const info = getModeInfo(mode, isArabic ? "ar" : "en");
            return (
              <div
                key={mode}
                className="transition-all duration-500"
                style={{
                  opacity: activeCapability && !isLit ? 0.3 : 1,
                  transform: activeCapability && isLit ? "scale(1.1)" : "scale(1)",
                  filter: activeCapability && isLit ? `drop-shadow(0 0 8px ${info.color})` : "none",
                }}
              >
                <CognitiveModeBadge mode={mode} isArabic={isArabic} />
              </div>
            );
          })}
        </div>

        {/* Capability mode legend when active */}
        {activeCapability && activeModes.length > 0 && (
          <p className="text-[10px] text-muted-foreground mt-2 animate-fade-in-up">
            {isArabic
              ? `سيتم تفعيل: ${activeModes.map((m) => getModeInfo(m, "ar").label).join("، ")}`
              : `Will activate: ${activeModes.map((m) => getModeInfo(m, "en").label).join(", ")}`}
          </p>
        )}

        {/* Khayali capability bubbles */}
        <div className="mt-8">
          <CapabilityBubbles onSelect={onSuggestionClick} />
        </div>
      </div>
    </div>
  );
}

function AutoRedirect() {
  const [count, setCount] = useState(8);
  const isArabic = useAppStore((s) => s.settings.language) === "ar";

  useEffect(() => {
    if (count <= 0) {
      window.location.href = "https://sovereignneuralfortresses.com/#contact";
      return;
    }
    const t = setTimeout(() => setCount((c) => c - 1), 1000);
    return () => clearTimeout(t);
  }, [count]);

  return (
    <p className="text-[10px] text-muted-foreground animate-pulse">
      {isArabic ? `جاري تحويلك للموقع الرئيسي... ${count}` : `Redirecting to main site... ${count}`}s
    </p>
  );
}

export function ChatInterface() {
  const {
    conversations,
    activeConversationId,
    setActiveConversationId,
    addConversation,
    updateConversation,
    deleteConversation,
    archiveConversation,
    restoreConversation,
    isStreaming,
    setIsStreaming,
    settings,
    setSidebarOpen,
    apiConnected,
    activeMode,
    setActiveMode,
    setActiveView,
    processingSteps,
    activeCapability,
    guestAttempts,
    incrementGuestAttempts,
    setApiConnected,
  } = useAppStore();
  
  // Admin bypass — ?admin=1 only (for testing)
  const isAdmin = useMemo(() => {
    if (typeof window === "undefined") return false;
    const params = new URLSearchParams(window.location.search);
    if (params.has("admin")) {
      localStorage.setItem("adam_admin", "1");
      return true;
    }
    return localStorage.getItem("adam_admin") === "1";
  }, []);

  // LinkedIn authenticated user — has valid token in URL
  const [isLinkedInUser, setIsLinkedInUser] = useState(false);
  const [linkedInName, setLinkedInName] = useState("");

  useEffect(() => {
    if (typeof window === "undefined") return;

    // Check localStorage first (persisted LinkedIn auth)
    if (localStorage.getItem("adam_linkedin_user")) {
      setIsLinkedInUser(true);
      setLinkedInName(localStorage.getItem("adam_linkedin_user") || "");
    }

    const params = new URLSearchParams(window.location.search);
    const token = params.get("token");
    if (!token) return;

    // Verify token with backend
    fetch(`${getFastApiUrl()}/api/auth/verify-token`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token }),
    })
      .then((r) => r.json())
      .then((data) => {
        if (data.valid) {
          setIsLinkedInUser(true);
          setLinkedInName(data.user?.name || "");
          localStorage.setItem("adam_linkedin_user", data.user?.name || "1");
          localStorage.setItem("adam_linkedin_email", data.user?.email || "");
          // Clean URL
          const url = new URL(window.location.href);
          url.searchParams.delete("token");
          window.history.replaceState({}, "", url.toString());
        }
      })
      .catch(() => {});
  }, []);

  const maxAttempts = typeof window !== "undefined" && (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") ? 99999 : 5;

  // Redirect non-auth users to Sovereign site (skipped on localhost)
  useEffect(() => {
    if (typeof window === "undefined") return;
    if (isAdmin) return;
    if (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") return;
    const params = new URLSearchParams(window.location.search);
    const hasToken = params.has("token");
    if (hasToken) return;
    if (window.location.pathname.startsWith("/login")) return;
    const hasLinkedIn = isLinkedInUser || localStorage.getItem("adam_linkedin_user");
    if (!hasLinkedIn && !sessionStorage.getItem("sovereign_redirected")) {
      sessionStorage.setItem("sovereign_redirected", "1");
      window.location.href = "https://sovereignneuralfortresses.com/";
    }
  }, [isAdmin, isLinkedInUser]);

  const [input, setInput] = useState("");
  const [streamingContent, setStreamingContent] = useState("");
  const [error, setError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const abortRef = useRef<AbortController | null>(null);
  const userScrolledUpRef = useRef(false);
  const prevMessagesLenRef = useRef(0);
  const scrollPositionsRef = useRef<Map<string, number>>(new Map());
  const [mounted, setMounted] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [filePreview, setFilePreview] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [showScrollDown, setShowScrollDown] = useState(false);
  const [showConvMenu, setShowConvMenu] = useState(false);
  const [keyboardVisible, setKeyboardVisible] = useState(false);

  useEffect(() => { setMounted(true); }, []);

  useEffect(() => {
    setApiConnected(true);
    checkApiHealth().then(r => {
      if (!r.connected) setApiConnected(false);
    }).catch(() => setApiConnected(false));
  }, [setApiConnected]);

  // Detect mobile keyboard visibility via visualViewport API
  useEffect(() => {
    if (typeof window === "undefined" || !window.visualViewport) return;
    const handleResize = () => {
      const isKeyboard = window.screen.height - window.visualViewport!.height > 150;
      setKeyboardVisible(isKeyboard);
      if (isKeyboard) {
        document.body.classList.add("keyboard-visible");
      } else {
        document.body.classList.remove("keyboard-visible");
      }
    };
    window.visualViewport?.addEventListener("resize", handleResize);
    return () => window.visualViewport?.removeEventListener("resize", handleResize);
  }, []);

  const activeConversation = conversations.find(
    (c) => c.id === activeConversationId
  );
  const messages = activeConversation?.messages || [];
  const isArabic = settings.language === "ar";

  const handleNewChat = useCallback(() => {
    setActiveConversationId(null);
    setInput("");
    setError(null);
  }, [setActiveConversationId]);

  const isNearBottom = useCallback(() => {
    const el = scrollRef.current;
    if (!el) return true;
    return el.scrollHeight - el.scrollTop - el.clientHeight < 120;
  }, []);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    userScrolledUpRef.current = false;
    setShowScrollDown(false);
  }, []);

  const handleScroll = useCallback(() => {
    const near = isNearBottom();
    if (near) {
      userScrolledUpRef.current = false;
      setShowScrollDown(false);
    } else {
      userScrolledUpRef.current = true;
      setShowScrollDown(true);
    }
    // Save scroll position for current conversation
    if (scrollRef.current && activeConversationId) {
      scrollPositionsRef.current.set(activeConversationId, scrollRef.current.scrollTop);
    }
  }, [isNearBottom, activeConversationId]);

  // Save/restore scroll position on conversation switch
  const prevConvRef = useRef<string | null>(null);
  useEffect(() => {
    const prevId = prevConvRef.current;
    const currId = activeConversationId ?? null;
    if (!prevId) {
      prevConvRef.current = currId;
      return;
    }
    if (prevId !== currId && scrollRef.current) {
      scrollPositionsRef.current.set(prevId, scrollRef.current.scrollTop);
      prevConvRef.current = currId;
      const saved = currId ? scrollPositionsRef.current.get(currId) : undefined;
      if (saved !== undefined) {
        requestAnimationFrame(() => {
          if (scrollRef.current) scrollRef.current.scrollTop = saved;
        });
        const el = scrollRef.current;
        const atBottom = saved >= (el.scrollHeight || 0) - (el.clientHeight || 0) - 120;
        userScrolledUpRef.current = !atBottom;
        setShowScrollDown(!atBottom);
        return;
      }
      userScrolledUpRef.current = false;
      setShowScrollDown(false);
    }
  }, [activeConversationId]);

  useEffect(() => {
    if (!userScrolledUpRef.current) {
      scrollToBottom();
    }
  }, [messages, streamingContent, scrollToBottom]);

  // Load sessions from server on mount, merge with local
  useEffect(() => {
    if (!apiConnected) return;
    (async () => {
      const store = useAppStore.getState();
      const localIds = new Set(store.conversations.map((c) => c.id));
      const serverSessions = await fetchSessions();
      if (!serverSessions?.length) return;
      // Fetch each session with messages individually
      for (const ss of serverSessions) {
        if (localIds.has(ss.id)) continue;
        const full = await fetchSession(ss.id).catch(() => null);
        if (!full?.messages) continue;
        store.addConversation({
          id: full.id,
          title: full.title,
          messages: full.messages.map((m: any) => ({
            id: m.id,
            role: m.role as "user" | "assistant" | "system",
            content: m.content,
            timestamp: Math.round(m.timestamp * 1000),
            mode: m.mode as any | undefined,
            intent: m.metadata?.intent as any,
            knowledgeUsed: m.metadata?.knowledge_used as number | undefined,
            cycle: m.metadata?.cycle as number | undefined,
            durationMs: m.metadata?.duration_ms as number | undefined,
          })),
          createdAt: Math.round(full.created_at * 1000),
          updatedAt: Math.round(full.updated_at * 1000),
        });
      }
    })();
  }, [apiConnected]);

  // Helper to sync a conversation's messages to server
  const syncToServer = useCallback(async (convId: string, msgs: typeof messages) => {
    if (!apiConnected) return;
    try {
      await syncSessionMessages(
        convId,
        msgs.map((m) => ({
          role: m.role,
          content: m.content,
          mode: m.mode,
          metadata: {
            knowledge_used: m.knowledgeUsed,
            cycle: m.cycle,
            duration_ms: m.durationMs,
            intent: m.intent,
          },
        }))
      );
      useAppStore.getState().addSyncedSessionId(convId);
    } catch {
      // silent
    }
  }, [apiConnected]);

  const handleSend = useCallback(async () => {
    const trimmed = input.trim();
    const pendingFile = selectedFile;
    if ((!trimmed && !pendingFile) || isStreaming) return;

    if (guestAttempts >= maxAttempts && !isAdmin) return;
    if (!isAdmin) incrementGuestAttempts();

    let fileUrl = "";
    let fileName = "";
    let fileContent = "";
    if (pendingFile) {
      setIsUploading(true);
      fileName = pendingFile.name;
      try {
        const result = await uploadFile(pendingFile);
        if (result) {
          fileUrl = result.url;
          fileContent = result.text_content || "";
        }
      } catch (e) {
        console.error("Upload failed:", e);
        setError("فشل رفع الملف — حاول مرة أخرى");
        setIsStreaming(false);
        setIsUploading(false);
        return;
      } finally {
        setIsUploading(false);
      }
      handleRemoveFile();
    }

    setError(null);
    setIsStreaming(true);
    setStreamingContent("");

    const displayContent = trimmed || (fileName ? `${getFileIcon(fileName)} ${fileName}` : "");
    const payloadMessage = fileContent
      ? trimmed
        ? `${trimmed}\n\n--- FILE: ${fileName} ---\n${fileContent}\n--- END FILE ---`
        : `Analyze this file (${fileName}):\n${fileContent}`
      : trimmed;

    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: displayContent,
      attachment: fileName ? { name: fileName, url: fileUrl, preview: fileContent?.slice(0, 500) } : undefined,
      timestamp: Date.now(),
    };

    let convId = activeConversationId;
    let conv = conversations.find((c) => c.id === convId);

    if (!conv) {
      convId = crypto.randomUUID();
      conv = {
        id: convId,
        title: trimmed.slice(0, 50) + (trimmed.length > 50 ? "..." : ""),
        messages: [userMessage],
        createdAt: Date.now(),
        updatedAt: Date.now(),
      };
      addConversation(conv);
      useAppStore.getState().setActiveConversationId(convId);
    } else {
      if (convId) {
        updateConversation(convId, {
          messages: [...conv.messages, userMessage],
        });
      }
    }

    setInput("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }

    try {
      abortRef.current = new AbortController();

      // Use FastAPI backend — REST only (WebSocket disabled for stability)
      const result = await sendChatMessage(payloadMessage, { history: messages.slice(-10) });

      // Update cognitive mode
      if (result.mode) {
        const modeMap: Record<string, CognitiveMode> = {
          analyst: "analyst",
          builder: "builder",
          corrector: "corrector",
          engineer: "engineer",
          researcher: "researcher",
          communicator: "communicator",
          strategist: "strategist",
        };
        setActiveMode(modeMap[result.mode] || "analyst");
      }

      const assistantMessage: Message = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: result.response,
        timestamp: Date.now(),
        mode: (result.mode as CognitiveMode) || activeMode,
        intent: result.intent,
        knowledgeUsed: result.knowledge_used,
        cycle: result.cycle,
        durationMs: result.duration_ms,
        audioUrl: result.audio_url || undefined,
      };

      if (result.permission_pending) {
        useAppStore.getState().setPermissionPending(result.permission_pending);
      }

      if (!convId) return;
      const latestConv = useAppStore
        .getState()
        .conversations.find((c) => c.id === convId);
      if (latestConv) {
        updateConversation(convId, {
          messages: [...latestConv.messages, assistantMessage],
        });
        syncToServer(convId, [...latestConv.messages, assistantMessage]);
      }

      setStreamingContent("");
    } catch (err) {
      if (err instanceof Error && err.name === "AbortError") {
        // User cancelled
      } else {
        const errorMessage =
          err instanceof Error ? err.message : "Unknown error";
        setError(errorMessage);
      }
      setStreamingContent("");
    } finally {
      setIsStreaming(false);
      abortRef.current = null;
    }
  }, [
    input,
    isStreaming,
    activeConversationId,
    conversations,
    addConversation,
    updateConversation,
    setIsStreaming,
    settings,
    apiConnected,
    activeMode,
    setActiveMode,
    messages,
  ]);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setSelectedFile(file);
    setFilePreview(file.name);
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes}B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)}MB`;
  };

  const getFileIcon = (filename: string) => {
    const ext = filename.split(".").pop()?.toLowerCase();
    if (!ext) return "📄";
    const icons: Record<string, string> = {
      pdf: "📕", doc: "📘", docx: "📘", ppt: "📊", pptx: "📊", xls: "📗", xlsx: "📗",
      png: "🖼️", jpg: "🖼️", jpeg: "🖼️", gif: "🖼️", webp: "🖼️", svg: "🖼️", bmp: "🖼️",
      mp3: "🎵", wav: "🎵", ogg: "🎵", flac: "🎵", aac: "🎵",
      mp4: "🎬", mov: "🎬", avi: "🎬", webm: "🎬", mkv: "🎬",
      py: "🐍", js: "💛", ts: "💙", jsx: "⚛️", tsx: "⚛️", html: "🌐", css: "🎨",
      json: "📋", xml: "📋", yaml: "📋", yml: "📋", toml: "📋",
      sql: "🗄️", sh: "💻", rb: "💎", go: "🔵", java: "☕", c: "⚙️", cpp: "⚙️", rs: "🦀",
      md: "📝", txt: "📄", csv: "📊", log: "📜",
      zip: "📦", tar: "📦", gz: "📦", rar: "📦", "7z": "📦",
    };
    return icons[ext] || "📎";
  };

  const handleRemoveFile = () => {
    setSelectedFile(null);
    setFilePreview(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    const textarea = e.target;
    textarea.style.height = "auto";
    textarea.style.height = Math.min(textarea.scrollHeight, 150) + "px";
  };

  const handleStopStreaming = () => {
    if (abortRef.current) {
      abortRef.current.abort();
    }
  };

  const handleSuggestionClick = (text: string) => {
    setInput(text);
    setTimeout(() => textareaRef.current?.focus(), 100);
  };

  const handleAudioReady = useCallback(async (blob: Blob) => {
    if (isStreaming) return;
    setIsStreaming(true);
    setError(null);

    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: isArabic ? "🎤 [رسالة صوتية]" : "🎤 [Voice message]",
      timestamp: Date.now(),
    };

    let convId = activeConversationId;
    let conv = conversations.find((c) => c.id === convId);

    if (!conv) {
      convId = crypto.randomUUID();
      conv = {
        id: convId,
        title: isArabic ? "رسالة صوتية" : "Voice message",
        messages: [userMessage],
        createdAt: Date.now(),
        updatedAt: Date.now(),
      };
      addConversation(conv);
      useAppStore.getState().setActiveConversationId(convId);
    } else {
      if (convId) {
        updateConversation(convId, {
          messages: [...conv.messages, userMessage],
        });
      }
    }

    try {
      const result = await sendAudio(blob, convId ?? undefined);

      const assistantMessage: Message = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: result.text || (isArabic ? "(لم يتم التعرف على الصوت)" : "(No speech detected)"),
        timestamp: Date.now(),
        mode: activeMode,
        durationMs: result.duration_ms,
        audioUrl: result.audioUrl || undefined,
      };

      if (!convId) return;
      const latestConv = useAppStore.getState().conversations.find((c) => c.id === convId);
      if (latestConv) {
        updateConversation(convId, {
          messages: [...latestConv.messages, assistantMessage],
        });
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Voice processing failed";
      setError(errorMessage);
    } finally {
      setIsStreaming(false);
    }
  }, [isStreaming, activeConversationId, conversations, addConversation, updateConversation, setIsStreaming, activeMode, isArabic]);

  const t = isArabic ? chatAr : chatEn;
  const modeInfo = getModeInfo(activeMode, isArabic ? "ar" : "en");

  if (!mounted) {
    return <div className="flex-1 flex flex-col min-h-0" />;
  }

  return (
    <div className="flex-1 flex flex-col min-h-0">
      <PermissionDialog />
      {/* Top bar */}
      <div className="h-14 border-b border-border flex items-center px-4 gap-3 glass-subtle shrink-0">
        <Button
          variant="ghost"
          size="icon"
          className="md:hidden text-muted-foreground hover:text-primary"
          onClick={() => setSidebarOpen(true)}
        >
          <Menu className="h-5 w-5" />
        </Button>

        <div className="flex items-center gap-2 flex-1 min-w-0 relative" suppressHydrationWarning>
          <AdamLogo size={24} animate={false} />
          <div className="relative" suppressHydrationWarning>
            <button
              className="text-sm font-medium truncate max-w-[200px] flex items-center gap-1.5 hover:text-primary transition-colors cursor-pointer"
              onClick={() => setShowConvMenu(!showConvMenu)}>
              <span className="truncate">{activeConversation?.title || t.newConversation}</span>
              <span className="text-[9px] text-muted-foreground/50 shrink-0">{showConvMenu ? "▲" : "▼"}</span>
            </button>
            {showConvMenu && (
              <>
                <div className="fixed inset-0 z-40" onClick={() => setShowConvMenu(false)} />
                <div className="absolute top-full left-0 mt-1 w-72 max-h-80 overflow-y-auto rounded-lg border border-border shadow-2xl z-50"
                  style={{ backgroundColor: 'hsl(var(--popover))' }}>
                  <div className="p-1.5 space-y-0.5">
                    <button
                      className="w-full flex items-center gap-2 px-2.5 py-2 text-xs rounded-md hover:bg-primary/10 text-left transition-colors"
                      onClick={() => { handleNewChat(); setShowConvMenu(false); }}>
                      <Plus className="h-3.5 w-3.5" />
                      {isArabic ? "محادثة جديدة" : "New Chat"}
                    </button>
                    <div className="h-px bg-border mx-2" />
                    {conversations.length === 0 ? (
                      <p className="px-2.5 py-3 text-[10px] text-muted-foreground text-center">
                        {isArabic ? "لا توجد محادثات" : "No conversations"}
                      </p>
                    ) : (
                      conversations.map((conv) => (
                        <div key={conv.id}
                          className={cn(
                            "flex items-center gap-1 px-2.5 py-1.5 rounded-md text-xs cursor-pointer transition-colors",
                            conv.archived && "opacity-50",
                            conv.id === activeConversationId
                              ? "bg-primary/15 text-primary"
                              : "hover:bg-muted text-muted-foreground hover:text-foreground"
                          )}
                          onClick={() => {
                            if (!conv.archived) {
                              setActiveConversationId(conv.id);
                              setActiveView("chat");
                            }
                            setShowConvMenu(false);
                          }}>
                          <MessageSquare className="h-3 w-3 shrink-0" />
                          <span className="flex-1 truncate">{conv.archived ? "📦 " : ""}{conv.title}</span>
                          <div className="flex items-center gap-0.5 shrink-0">
                            {!conv.archived && (
                              <button
                                className="h-5 w-5 flex items-center justify-center rounded hover:bg-primary/10 text-muted-foreground hover:text-primary transition-all"
                                onClick={(e) => { e.stopPropagation(); archiveConversation(conv.id); }}
                                title={isArabic ? "أرشفة" : "Archive"}
                              >
                                <Archive className="h-3 w-3" />
                              </button>
                            )}
                            {conv.archived && (
                              <button
                                className="h-5 w-5 flex items-center justify-center rounded hover:bg-emerald-500/10 text-muted-foreground hover:text-emerald-400 transition-all"
                                onClick={(e) => { e.stopPropagation(); restoreConversation(conv.id); }}
                                title={isArabic ? "استعادة" : "Restore"}
                              >
                                <RotateCcw className="h-3 w-3" />
                              </button>
                            )}
                            <button
                              className="h-5 w-5 flex items-center justify-center rounded hover:bg-destructive/20 text-muted-foreground hover:text-destructive transition-all"
                              onClick={(e) => {
                                e.stopPropagation();
                                deleteConversation(conv.id);
                                if (apiConnected) deleteSessionOnServer(conv.id).catch(() => {});
                              }}
                              title={isArabic ? "حذف" : "Delete"}
                            >
                              <Trash2 className="h-3 w-3" />
                            </button>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              </>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          {/* Active cognitive mode */}
          <Badge
            variant="outline"
            className="text-[10px] gap-1 hidden sm:flex"
            style={{ borderColor: `${modeInfo.color}50`, color: modeInfo.color, backgroundColor: `${modeInfo.color}15` }}
          >
            <Brain className="h-3 w-3" />
            {modeInfo.icon} {modeInfo.label}
          </Badge>

          {/* Connection status */}
          <Badge
            variant={apiConnected ? "default" : "destructive"}
            className={cn(
              "text-[10px] gap-1",
              apiConnected
                ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/30"
                : "bg-destructive/20 text-destructive border-destructive/30"
            )}
          >
            <div
              className={cn(
                "h-1.5 w-1.5 rounded-full",
                apiConnected ? "bg-emerald-400 pulse-ring" : "bg-destructive"
              )}
            />
            {apiConnected ? t.connected : t.disconnected}
          </Badge>
        </div>
      </div>

      {/* Messages area */}
      {messages.length === 0 && !isStreaming ? (
        <WelcomeScreen isArabic={isArabic} onSuggestionClick={handleSuggestionClick} activeCapability={activeCapability} />
      ) : (
        <div ref={scrollRef} onScroll={handleScroll} className="flex-1 min-h-0 overflow-y-auto scrollbar-thin" style={{ scrollbarWidth: "thin", scrollbarColor: "hsl(var(--border)) transparent" }}>
          <div className="w-full max-w-3xl mx-auto space-y-6 px-4 pb-4">
            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}

            {/* Streaming message */}
            {isStreaming && streamingContent && (
              <MessageBubble
                message={{
                  id: "streaming",
                  role: "assistant",
                  content: streamingContent,
                  timestamp: Date.now(),
                  mode: activeMode,
                }}
              />
            )}

            {/* Typing indicator with current step */}
            {isStreaming && !streamingContent && (
              <div className="flex gap-3 animate-fade-in-up">
                <div className="h-8 w-8 rounded-full bg-gradient-to-br from-purple-500/30 via-cyan-500/20 to-blue-500/30 flex items-center justify-center shrink-0">
                  <AdamLogo size={20} animate={true} />
                </div>
                <div className="chat-bubble-ai glass rounded-2xl px-4 py-3">
                  <TypingIndicator />
                  {(() => {
                    const status = getStepStatus(processingSteps, isArabic);
                    return status ? (
                      <div className="flex items-center gap-1.5 mt-0.5 text-[10px] text-muted-foreground border-t border-border/50 pt-1.5">
                        <span>{status.icon}</span>
                        <span>{status.text}</span>
                        <span className="relative flex h-1.5 w-1.5">
                          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75" />
                          <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-cyan-500" />
                        </span>
                      </div>
                    ) : null;
                  })()}
                </div>
              </div>
            )}

            {/* Error */}
            {error && (
              <div className="flex items-center gap-2 p-3 rounded-xl bg-destructive/10 border border-destructive/20 text-destructive text-xs max-w-md mx-auto">
                <AlertCircle className="h-4 w-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <div ref={messagesEndRef} />

            {/* Scroll-to-bottom button */}
            {showScrollDown && (
              <div className="flex justify-center pt-2">
                <button
                  onClick={scrollToBottom}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[11px] font-medium glass border border-border/50 shadow-lg hover:brightness-125 transition-all"
                >
                  <svg className="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="6 9 12 15 18 9" />
                  </svg>
                  {isArabic ? "اذهب للأسفل" : "Scroll to bottom"}
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Input area */}
      <div className="border-t border-border p-3 sm:p-4 glass-subtle shrink-0 chat-input-area" style={{ paddingBottom: "calc(env(safe-area-inset-bottom, 0px) + 0.75rem)" }}>
        <div className="max-w-3xl mx-auto">
          {error && (
            <div className="flex items-center justify-center gap-2 mb-2">
              <Button
                variant="ghost"
                size="sm"
                className="text-xs text-destructive hover:text-destructive"
                onClick={handleSend}
              >
                <RotateCcw className="h-3 w-3 ml-1" />
                {t.retry}
              </Button>
            </div>
          )}

          {/* Guest attempt counter */}
          {!isAdmin && guestAttempts > 0 && (
            <div className="flex justify-center mb-2">
              <div className={
                guestAttempts >= maxAttempts
                  ? "text-[10px] px-3 py-1 rounded-full border bg-destructive/10 border-destructive/30 text-destructive font-medium"
                  : "text-[10px] px-3 py-1 rounded-full border bg-primary/10 border-primary/20 text-primary font-medium"
              }>
                {isArabic ? "المحاولة " : "Attempt "}{guestAttempts}/{maxAttempts}
              </div>
            </div>
          )}

          {/* CTA after 3 attempts */}
          {!isAdmin && guestAttempts >= maxAttempts && (
            <div className="mb-3 animate-fade-in-up">
              <div className="rounded-xl bg-primary/5 border border-primary/20 p-4 text-center max-w-md mx-auto">
                <p className="text-sm font-medium text-foreground mb-1">
                  {isArabic ? "اكتملت الـ 3 محاولات المجانية" : "Your 3 free attempts are complete"}
                </p>
                <p className="text-xs text-muted-foreground mb-3">
                  {isArabic ? "آدم v9.5 مستعد ليك. سيتم تحويلك للموقع الرئيسي." : "Adam v9.5 is ready. Redirecting to main site."}
                </p>
                <a
                  href="https://sovereignneuralfortresses.com/#contact"
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors mb-2"
                >
                  <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8"/><path d="M12 17v4"/></svg>
                  {isArabic ? "احجز اجتماع →" : "Book a Meeting →"}
                </a>
                <AutoRedirect />
              </div>
            </div>
          )}

          <div className="flex items-end gap-2">
            <ShieldPulse />
            <input type="file" id="chat-file-upload" ref={fileInputRef} onChange={handleFileSelect} className="hidden" accept="*" />
            <Button
              onClick={() => fileInputRef.current?.click()}
              variant="outline"
              size="icon"
              disabled={isStreaming}
              className="h-11 w-11 rounded-xl shrink-0 text-muted-foreground hover:text-foreground"
              title={isArabic ? "رفع ملف" : "Upload file"}
            >
              <Paperclip className="h-4 w-4" />
            </Button>
            <div className="flex-1 flex flex-col gap-2">
              <label htmlFor="adam-chat-input" className="sr-only">
                {isArabic ? "رسالة" : "Message"}
              </label>
              {/* Attachment card */}
              {selectedFile && (
                <div className="flex items-center gap-3 px-4 py-3 rounded-xl bg-primary/5 border border-primary/20 animate-fade-in-up">
                  <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center shrink-0 text-lg">
                    {getFileIcon(selectedFile.name)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-foreground truncate">{selectedFile.name}</p>
                    <p className="text-[11px] text-muted-foreground">
                      {selectedFile.type || (isArabic ? "ملف" : "File")} · {formatFileSize(selectedFile.size)}
                      {isUploading && (
                        <span className="ml-2 inline-flex items-center gap-1 text-primary">
                          <span className="h-2 w-2 border border-primary/40 border-t-transparent rounded-full animate-spin" />
                          {isArabic ? "جاري الرفع..." : "Uploading..."}
                        </span>
                      )}
                    </p>
                  </div>
                  {selectedFile.type.startsWith("image/") && (
                    <img src={URL.createObjectURL(selectedFile)} alt="preview" className="h-10 w-10 rounded-lg object-cover shrink-0" />
                  )}
                  <button
                    onClick={handleRemoveFile}
                    className="h-6 w-6 rounded-full hover:bg-destructive/10 flex items-center justify-center shrink-0 transition-colors"
                    title={isArabic ? "إزالة" : "Remove"}
                  >
                    <X className="h-3.5 w-3.5 text-muted-foreground hover:text-destructive" />
                  </button>
                </div>
              )}
              <Textarea
                ref={textareaRef} id="adam-chat-input" name="message"
                value={input}
                onChange={handleTextareaChange}
                onKeyDown={handleKeyDown}
                placeholder={isStreaming ? t.thinking : t.placeholder}
                disabled={isStreaming || (!isAdmin && guestAttempts >= maxAttempts)}
                className="min-h-[44px] max-h-[150px] resize-none bg-muted/50 border-border focus-visible:ring-primary/50 text-sm rounded-xl"
                rows={1}
              />
            </div>

            {isStreaming ? (
              <Button
                onClick={handleStopStreaming}
                variant="outline"
                size="icon"
                className="h-11 w-11 rounded-xl border-destructive/50 text-destructive hover:bg-destructive/10 shrink-0"
              >
                <div className="h-3 w-3 rounded-sm bg-destructive" />
              </Button>
            ) : (
              <Button
                onClick={handleSend}
                disabled={(!input.trim() && !selectedFile) || (!isAdmin && guestAttempts >= maxAttempts)}
                size="icon"
                className="h-11 w-11 rounded-xl bg-gradient-to-bl from-primary via-purple-500 to-cyan-500 hover:opacity-90 text-white shrink-0"
              >
                <Send className="h-4 w-4" />
              </Button>
            )}
          </div>

          <div className="flex items-center justify-between mt-2">
            <p className="text-[10px] text-muted-foreground">
              {t.poweredBy} · Adam v9.5
            </p>
            {/* Mobile mode indicator */}
            <div className="sm:hidden">
              <Badge
                variant="outline"
                className="text-[9px] gap-0.5 px-1.5 py-0"
                style={{ borderColor: `${modeInfo.color}50`, color: modeInfo.color }}
              >
                {modeInfo.icon} {modeInfo.label}
              </Badge>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

const chatAr = {
  newConversation: "محادثة جديدة",
  connected: "متصل",
  disconnected: "غير متصل",
  placeholder: "اكتب رسالتك هنا...",
  thinking: "آدم يفكر...",
  retry: "إعادة المحاولة",
  poweredBy: "مدعوم بـ Adam Prism",
};

const chatEn = {
  newConversation: "New Conversation",
  connected: "Connected",
  disconnected: "Disconnected",
  placeholder: "Type your message here...",
  thinking: "Adam is thinking...",
  retry: "Retry",
  poweredBy: "Powered by Adam Prism",
};
