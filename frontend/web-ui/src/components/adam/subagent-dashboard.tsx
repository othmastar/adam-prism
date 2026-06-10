"use client";

import { useState, useEffect, useCallback } from "react";
import { useAppStore } from "@/lib/store";
import { getFastApiUrl } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Bot, Plus, Trash2, Send, RefreshCw } from "lucide-react";
import { cn } from "@/lib/utils";

type SubagentInfo = {
  id: string;
  name: string;
  status: string;
  created_at?: string;
};

export function SubagentDashboard() {
  const { settings } = useAppStore();
  const isArabic = settings.language === "ar";
  const url = getFastApiUrl();

  const [subagents, setSubagents] = useState<SubagentInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [spawnName, setSpawnName] = useState("");
  const [msg, setMsg] = useState<{ type: "ok" | "err"; text: string } | null>(null);

  const [chatAgentId, setChatAgentId] = useState<string | null>(null);
  const [chatInput, setChatInput] = useState("");
  const [chatHistory, setChatHistory] = useState<{ role: string; content: string }[]>([]);
  const [chatLoading, setChatLoading] = useState(false);

  const fetchSubagents = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${url}/api/subagents`);
      if (res.ok) {
        const data = await res.json();
        setSubagents(data.subagents || []);
      }
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }, [url]);

  useEffect(() => { fetchSubagents(); }, [fetchSubagents]);

  const showMsg = (type: "ok" | "err", text: string) => {
    setMsg({ type, text });
    setTimeout(() => setMsg(null), 3000);
  };

  const spawnSubagent = async () => {
    if (!spawnName.trim()) return;
    try {
      const res = await fetch(`${url}/api/subagents/spawn`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: spawnName.trim() }),
      });
      if (res.ok) { showMsg("ok", isArabic ? "تم إنشاء الوكيل" : "Subagent spawned"); setSpawnName(""); fetchSubagents(); }
      else { const d = await res.json(); showMsg("err", d.detail || "Failed"); }
    } catch { showMsg("err", "Error"); }
  };

  const removeSubagent = async (id: string) => {
    try {
      const res = await fetch(`${url}/api/subagents/${id}`, { method: "DELETE" });
      if (res.ok) { showMsg("ok", isArabic ? "تم الحذف" : "Deleted"); fetchSubagents(); if (chatAgentId === id) setChatAgentId(null); }
      else showMsg("err", isArabic ? "فشل" : "Failed");
    } catch { showMsg("err", "Error"); }
  };

  const openChat = (agent: SubagentInfo) => {
    if (chatAgentId === agent.id) { setChatAgentId(null); return; }
    setChatAgentId(agent.id);
    setChatHistory([]);
    setChatInput("");
  };

  const sendChat = async () => {
    if (!chatInput.trim() || !chatAgentId) return;
    const message = chatInput.trim();
    setChatInput("");
    setChatHistory((prev) => [...prev, { role: "user", content: message }]);
    setChatLoading(true);
    try {
      const res = await fetch(`${url}/api/subagents/${chatAgentId}/chat`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
      });
      if (res.ok) {
        const data = await res.json();
        setChatHistory((prev) => [...prev, { role: "assistant", content: data.response || JSON.stringify(data) }]);
      } else {
        setChatHistory((prev) => [...prev, { role: "assistant", content: isArabic ? "خطأ في الاتصال" : "Error" }]);
      }
    } catch {
      setChatHistory((prev) => [...prev, { role: "assistant", content: isArabic ? "خطأ" : "Error" }]);
    } finally {
      setChatLoading(false);
    }
  };

  return (
    <div className="flex-1 overflow-y-auto p-4">
      <div className="max-w-3xl mx-auto space-y-4">
        <div className="flex items-center gap-2 mb-2">
          <Bot className="h-5 w-5 text-primary" />
          <h2 className="text-lg font-semibold">{isArabic ? "الوكلاء الفرعيون" : "Subagents"}</h2>
          <Button variant="ghost" size="icon" className="h-7 w-7 ml-auto" onClick={fetchSubagents}>
            <RefreshCw className={cn("h-4 w-4", loading && "animate-spin")} />
          </Button>
        </div>

        {msg && (
          <div className={cn("px-3 py-2 rounded-lg text-sm", msg.type === "ok" ? "bg-emerald-500/10 text-emerald-400" : "bg-destructive/10 text-destructive")}>
            {msg.text}
          </div>
        )}

        <Card className="p-4 border-border/50 space-y-3">
          <h3 className="text-sm font-medium flex items-center gap-2"><Plus className="h-4 w-4" /> {isArabic ? "إنشاء وكيل جديد" : "Spawn New Subagent"}</h3>
          <div className="flex gap-2">
            <Input
              placeholder={isArabic ? "اسم الوكيل" : "Subagent name"}
              value={spawnName}
              onChange={(e) => setSpawnName(e.target.value)}
              className="text-sm flex-1"
              onKeyDown={(e) => e.key === "Enter" && spawnSubagent()}
            />
            <Button onClick={spawnSubagent} size="sm" className="shrink-0 gap-1.5">
              <Plus className="h-4 w-4" /> {isArabic ? "إنشاء" : "Spawn"}
            </Button>
          </div>
        </Card>

        <div className="space-y-2">
          {loading ? (
            <p className="text-sm text-muted-foreground">{isArabic ? "جاري التحميل..." : "Loading..."}</p>
          ) : subagents.length === 0 ? (
            <p className="text-sm text-muted-foreground">{isArabic ? "لا توجد وكلاء فرعيون" : "No subagents"}</p>
          ) : subagents.map((agent) => (
            <div key={agent.id}>
              <Card className="p-3 border-border/50 bg-card/50 backdrop-blur-sm">
                <div className="flex items-center justify-between gap-2">
                  <button onClick={() => openChat(agent)} className="min-w-0 flex-1 text-left">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium truncate">{agent.name}</span>
                      <Badge variant="outline" className="text-[10px]">{agent.status}</Badge>
                    </div>
                    <p className="text-xs text-muted-foreground mt-0.5 cursor-default">{agent.id}</p>
                    {agent.created_at && <p className="text-[10px] text-muted-foreground/60 cursor-default">{agent.created_at}</p>}
                  </button>
                  <Button variant="ghost" size="icon" className="h-8 w-8 shrink-0 text-destructive/60 hover:text-destructive" onClick={() => removeSubagent(agent.id)}>
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </Card>

              {chatAgentId === agent.id && (
                <Card className="mt-1 p-3 border-border/30 bg-muted/20">
                  <div className="space-y-2 max-h-60 overflow-y-auto mb-2 text-sm">
                    {chatHistory.length === 0 && (
                      <p className="text-xs text-muted-foreground/60">{isArabic ? "ابدأ محادثة مع الوكيل" : "Start chatting with subagent"}</p>
                    )}
                    {chatHistory.map((h, i) => (
                      <div key={i} className={cn("flex", h.role === "user" ? "justify-end" : "justify-start")}>
                        <div className={cn("max-w-[80%] rounded-lg px-3 py-1.5 text-xs", h.role === "user" ? "bg-primary/20 text-primary" : "bg-muted/50 text-foreground")}>
                          {h.content}
                        </div>
                      </div>
                    ))}
                    {chatLoading && <p className="text-xs text-muted-foreground/60">{isArabic ? "جاري التفكير..." : "Thinking..."}</p>}
                  </div>
                  <div className="flex gap-2">
                    <Input
                      value={chatInput}
                      onChange={(e) => setChatInput(e.target.value)}
                      placeholder={isArabic ? "رسالتك..." : "Your message..."}
                      className="text-sm flex-1"
                      disabled={chatLoading}
                      onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && (e.preventDefault(), sendChat())}
                    />
                    <Button size="icon" className="h-9 w-9 shrink-0" onClick={sendChat} disabled={chatLoading || !chatInput.trim()}>
                      <Send className="h-4 w-4" />
                    </Button>
                  </div>
                </Card>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
