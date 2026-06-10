"use client";

import { useAppStore } from "@/lib/store";
import { cn } from "@/lib/utils";
import { useEffect, useRef, useState, useCallback } from "react";

type GraphNode = {
  id: string;
  label: string;
  labelAr: string;
  x: number;
  y: number;
  vx: number;
  vy: number;
  color: string;
  size: number;
};

type GraphEdge = {
  source: number;
  target: number;
  label: string;
};

const nodesData: Omit<GraphNode, "x" | "y" | "vx" | "vy">[] = [
  { id: "adam", label: "Adam Prism", labelAr: "آدم بريزم", color: "#8b5cf6", size: 28 },
  { id: "ai", label: "AI Engineering", labelAr: "هندسة الذكاء الاصطناعي", color: "#06b6d4", size: 22 },
  { id: "petro", label: "15 Years Petroleum", labelAr: "خبرة 15 عاماً في البترول", color: "#f59e0b", size: 22 },
  { id: "security", label: "Cybersecurity", labelAr: "الأمن السيبراني", color: "#ef4444", size: 20 },
  { id: "ollama", label: "Ollama Models", labelAr: "موديلات Ollama", color: "#10b981", size: 18 },
  { id: "memory", label: "Memory Systems", labelAr: "أنظمة الذاكرة", color: "#ec4899", size: 18 },
  { id: "ethics", label: "AI Ethics", labelAr: "الأخلاقيات", color: "#3b82f6", size: 16 },
  { id: "notebook", label: "Active Notebook", labelAr: "الدفتر الحي", color: "#f97316", size: 16 },
  { id: "browser", label: "Browser Automation", labelAr: "أتمتة المتصفح", color: "#14b8a6", size: 16 },
  { id: "vision", label: "Computer Vision", labelAr: "الرؤية الحاسوبية", color: "#a855f7", size: 14 },
  { id: "nlp", label: "NLP & Generation", labelAr: "معالجة اللغة", color: "#6366f1", size: 14 },
  { id: "trace", label: "Trace Recorder", labelAr: "مسجل التتبع", color: "#d946ef", size: 14 },
  { id: "guard", label: "Security Guard", labelAr: "الحارس الأمني", color: "#dc2626", size: 14 },
  { id: "qdrant", label: "Qdrant Vector DB", labelAr: "قاعدة المتجهات", color: "#059669", size: 14 },
];

const edgesData: GraphEdge[] = [
  { source: 0, target: 1, label: "core" },
  { source: 0, target: 2, label: "domain" },
  { source: 0, target: 3, label: "built-in" },
  { source: 0, target: 4, label: "backend" },
  { source: 0, target: 5, label: "powers" },
  { source: 1, target: 9, label: "subfield" },
  { source: 1, target: 10, label: "subfield" },
  { source: 3, target: 12, label: "layer" },
  { source: 4, target: 13, label: "vector db" },
  { source: 5, target: 6, label: "guides" },
  { source: 5, target: 7, label: "persists" },
  { source: 5, target: 11, label: "logs" },
  { source: 0, target: 8, label: "tool" },
  { source: 2, target: 3, label: "applied" },
  { source: 6, target: 3, label: "aligned" },
];

const nodeSummaries: Record<string, { ar: string; en: string }> = {
  adam: { ar: "آدم بريزم — قلب النظام. ينسق كل الموديولات ويتفاعل مع المستخدم.", en: "Adam Prism — the system core. Orchestrates all modules and interacts with the user." },
  ai: { ar: "هندسة الذكاء الاصطناعي — بناء وتطوير موديلات LLM وتكاملها.", en: "AI Engineering — building and integrating LLM models." },
  petro: { ar: "خبرة 15 عاماً في قطاع البترول — تحليل البيانات والمحاكاة.", en: "15 years of petroleum industry experience — data analysis and simulation." },
  security: { ar: "الأمن السيبراني — حماية النظام من التهديدات والاختراقات.", en: "Cybersecurity — protecting the system from threats." },
  ollama: { ar: "موديلات Ollama — 10 موديلات مخصصة للاستدلال والتضمين.", en: "Ollama Models — 10 specialized models for inference and embeddings." },
  memory: { ar: "أنظمة الذاكرة — TTLCache, EmbedCache, بحث دلالي.", en: "Memory Systems — TTLCache, EmbedCache, semantic search." },
  ethics: { ar: "أخلاقيات الذكاء الاصطناعي — تقييم أخلاقي لكل استجابة.", en: "AI Ethics — ethical evaluation for every response." },
  notebook: { ar: "الدفتر الحي — تدوين يومي وأسئلة معلقة.", en: "Active Notebook — daily notes and pending questions." },
  browser: { ar: "أتمتة المتصفح — تحكم كامل في المتصفح لأداء المهام.", en: "Browser Automation — full browser control for task execution." },
  vision: { ar: "الرؤية الحاسوبية — تحليل الصور والفيديو (llava/gemma3-vision).", en: "Computer Vision — image and video analysis (llava/gemma3-vision)." },
  nlp: { ar: "معالجة اللغة — توليد النص، التلخيص، الترجمة.", en: "NLP & Generation — text generation, summarization, translation." },
  trace: { ar: "مسجل التتبع — تسجيل كل خطوة في سير المعالجة.", en: "Trace Recorder — logs every step in the processing pipeline." },
  guard: { ar: "الحارس الأمني — فحص الإدخال ومنع الهجمات.", en: "Security Guard — input scanning and attack prevention." },
  qdrant: { ar: "قاعدة المتجهات Qdrant — تخزين واسترجاع المتجهات الدلالية.", en: "Qdrant Vector DB — vector storage and semantic retrieval." },
};

export function KnowledgeGraph() {
  const { settings } = useAppStore();
  const isArabic = settings.language === "ar";
  const svgRef = useRef<SVGSVGElement>(null);
  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [edges, setEdges] = useState<{ s: number; t: number }[]>([]);
  const [hoveredNode, setHoveredNode] = useState<number | null>(null);
  const [selectedNode, setSelectedNode] = useState<number | null>(null);
  const animRef = useRef<number>(0);

  const isClient = typeof window !== "undefined";

  useEffect(() => {
    if (!isClient) return;
    const w = 600, h = 380;
    const centerX = w / 2, centerY = h / 2;
    const initialized = nodesData.map((n, i) => ({
      ...n,
      x: centerX + (Math.random() - 0.5) * w * 0.6,
      y: centerY + (Math.random() - 0.5) * h * 0.6,
      vx: 0, vy: 0,
    }));
    setNodes(initialized);
    setEdges(edgesData.map((e) => ({ s: e.source, t: e.target })));
  }, [isClient]);

  useEffect(() => {
    if (nodes.length === 0 || !isClient) return;
    const REPULSION = 8000;
    const ATTRACTION = 0.005;
    const DAMPING = 0.85;
    const MAX_SPEED = 2;

    const simulate = () => {
      setNodes((prev) => {
        const updated = prev.map((n) => ({ ...n }));
        const centerX = 300, centerY = 190;

        for (let i = 0; i < updated.length; i++) {
          updated[i].vx += (centerX - updated[i].x) * 0.001;
          updated[i].vy += (centerY - updated[i].y) * 0.001;

          for (let j = i + 1; j < updated.length; j++) {
            let dx = updated[j].x - updated[i].x;
            let dy = updated[j].y - updated[i].y;
            let dist = Math.sqrt(dx * dx + dy * dy) || 1;
            let force = REPULSION / (dist * dist);
            let fx = (dx / dist) * force;
            let fy = (dy / dist) * force;
            updated[i].vx -= fx;
            updated[i].vy -= fy;
            updated[j].vx += fx;
            updated[j].vy += fy;
          }
        }

        for (const edge of edges) {
          const a = updated[edge.s];
          const b = updated[edge.t];
          if (!a || !b) continue;
          const dx = b.x - a.x;
          const dy = b.y - a.y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          const force = (dist - 100) * ATTRACTION;
          const fx = (dx / dist) * force;
          const fy = (dy / dist) * force;
          a.vx += fx; a.vy += fy;
          b.vx -= fx; b.vy -= fy;
        }

        for (const n of updated) {
          const speed = Math.sqrt(n.vx * n.vx + n.vy * n.vy);
          if (speed > MAX_SPEED) {
            n.vx = (n.vx / speed) * MAX_SPEED;
            n.vy = (n.vy / speed) * MAX_SPEED;
          }
          n.x += n.vx;
          n.y += n.vy;
          n.vx *= DAMPING;
          n.vy *= DAMPING;

          n.x = Math.max(30, Math.min(570, n.x));
          n.y = Math.max(30, Math.min(350, n.y));
        }

        return updated;
      });
      animRef.current = requestAnimationFrame(simulate);
    };

    animRef.current = requestAnimationFrame(simulate);
    return () => cancelAnimationFrame(animRef.current);
  }, [nodes.length, edges, isClient]);

  if (!isClient) return <div className="h-[380px]" />;

  return (
    <div className="relative w-full overflow-hidden rounded-xl bg-muted/10 border border-border/30">
      <svg ref={svgRef} viewBox="0 0 600 380" className="w-full h-auto">
        {/* Edges */}
        {edges.map((edge, i) => {
          const a = nodes[edge.s];
          const b = nodes[edge.t];
          if (!a || !b) return null;
          return (
            <line
              key={`e${i}`}
              x1={a.x} y1={a.y} x2={b.x} y2={b.y}
              className="stroke-zinc-700/50 transition-all duration-300"
              strokeWidth={hoveredNode === edge.s || hoveredNode === edge.t ? 2 : 1}
              strokeOpacity={hoveredNode === edge.s || hoveredNode === edge.t ? 0.8 : 0.4}
            />
          );
        })}

        {/* Nodes */}
        {nodes.map((node, i) => {
          const isHovered = hoveredNode === i;
          const label = isArabic ? node.labelAr : node.label;
          return (
            <g key={node.id}
              onMouseEnter={() => setHoveredNode(i)}
              onMouseLeave={() => setHoveredNode(null)}
              onClick={() => setSelectedNode(selectedNode === i ? null : i)}
              className="transition-transform duration-200"
              style={{ cursor: "pointer" }}
            >
              {/* Glow */}
              {isHovered && (
                <circle cx={node.x} cy={node.y} r={node.size + 8}
                  fill={node.color} fillOpacity={0.15}
                  className="animate-pulse" />
              )}
              {/* Node circle */}
              <circle cx={node.x} cy={node.y} r={isHovered ? node.size + 2 : node.size}
                fill={`${node.color}30`}
                stroke={isHovered ? node.color : `${node.color}60`}
                strokeWidth={isHovered ? 2.5 : 1.5}
                className="transition-all duration-200" />
              {/* Inner dot */}
              <circle cx={node.x} cy={node.y} r={4}
                fill={node.color}
                className="transition-all duration-200" />
              {/* Label */}
              <text x={node.x} y={node.y + node.size + 14}
                textAnchor="middle"
                className="fill-zinc-400 text-[9px] font-medium transition-all duration-200"
                fontSize={isHovered ? 10 : 9}
                fillOpacity={isHovered ? 1 : 0.7}>
                {label}
              </text>
            </g>
          );
        })}
      </svg>

      {/* Node info panel */}
      {selectedNode !== null && nodes[selectedNode] && (
        <div className="absolute top-2 right-2 left-2 p-3 rounded-lg backdrop-blur-sm border border-primary/30 animate-fade-in-up z-10" style={{ backgroundColor: 'rgba(0,0,0,0.8)' }}>
          <div className="flex items-start gap-2">
            <div className="h-6 w-6 rounded-md flex items-center justify-center shrink-0" style={{ backgroundColor: `${nodes[selectedNode].color}30` }}>
              <div className="h-2 w-2 rounded-full" style={{ backgroundColor: nodes[selectedNode].color }} />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-foreground">{isArabic ? nodes[selectedNode].labelAr : nodes[selectedNode].label}</p>
              <p className="text-[9px] text-muted-foreground leading-relaxed mt-0.5">
                {isArabic
                  ? (nodeSummaries[nodes[selectedNode].id]?.ar || "")
                  : (nodeSummaries[nodes[selectedNode].id]?.en || "")}
              </p>
            </div>
            <button
              onClick={() => setSelectedNode(null)}
              className="h-4 w-4 rounded-full bg-zinc-700/50 flex items-center justify-center text-[8px] text-zinc-400 hover:text-white shrink-0"
            >
              ✕
            </button>
          </div>
        </div>
      )}

      {/* Legend overlay */}
      <div className="absolute bottom-2 left-2 flex flex-wrap gap-1.5">
        {nodesData.slice(0, 5).map((n) => (
          <div key={n.id} className="flex items-center gap-1 px-1.5 py-0.5 rounded" style={{ backgroundColor: 'rgba(0,0,0,0.3)' }}>
            <div className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: n.color }} />
            <span className="text-[7px] text-zinc-500">{isArabic ? n.labelAr : n.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
