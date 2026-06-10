"use client";

import { useEffect, useState } from "react";
import { useAppStore } from "@/lib/store";
import { fetchChannels, ChannelInfo } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Menu, Wifi, WifiOff, RefreshCw, Hash, Globe, Mail, MessageSquare, Smartphone, Radio, Monitor, Twitter, Facebook, Bot, Signal as SignalIcon, Camera, MessageCircle, Users, Webhook, Rss, Github, BookOpen, ChevronDown, ChevronUp } from "lucide-react";
import { cn } from "@/lib/utils";

const channelIcons: Record<string, React.ElementType> = {
  telegram: MessageSquare,
  whatsapp: Smartphone,
  discord: Hash,
  slack: Hash,
  email: Mail,
  sms: MessageSquare,
  websocket: Radio,
  webchat: Globe,
  twitter: Twitter,
  facebook: Facebook,
  matrix: MessageCircle,
  signal: SignalIcon,
  instagram: Camera,
  line: MessageCircle,
  viber: Phone,
  teams: Users,
  googletalk: MessageCircle,
  irc: Radio,
  xmpp: MessageCircle,
  telegram_webhook: Webhook,
  wechat: MessageCircle,
  webhook_generic: Webhook,
  rss: Rss,
  notion: BookOpen,
  github: Github,
};

function Phone(props: any) { return <Smartphone {...props} />; }

const channelColors: Record<string, string> = {
  telegram: "text-blue-400",
  whatsapp: "text-green-400",
  discord: "text-indigo-400",
  slack: "text-purple-400",
  email: "text-yellow-400",
  sms: "text-emerald-400",
  websocket: "text-cyan-400",
  webchat: "text-sky-400",
  twitter: "text-blue-300",
  facebook: "text-blue-500",
  matrix: "text-orange-400",
  signal: "text-green-300",
  instagram: "text-pink-400",
  line: "text-green-500",
  viber: "text-purple-300",
  teams: "text-violet-400",
  googletalk: "text-teal-400",
  irc: "text-gray-400",
  xmpp: "text-rose-400",
  telegram_webhook: "text-blue-300",
  wechat: "text-green-600",
  webhook_generic: "text-cyan-300",
  rss: "text-orange-500",
  notion: "text-white",
  github: "text-gray-300",
};

export function ChannelsPanel() {
  const { settings, setSidebarOpen, apiConnected } = useAppStore();
  const isArabic = settings.language === "ar";

  const [channels, setChannels] = useState<Record<string, ChannelInfo>>({});
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState<string[]>([]);

  const loadChannels = async () => {
    if (!apiConnected) return;
    setLoading(true);
    try {
      const data = await fetchChannels();
      setChannels(data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadChannels();
    const interval = setInterval(loadChannels, 10000);
    return () => clearInterval(interval);
  }, [apiConnected]);

  const activeCount = Object.values(channels).filter((c) => c.running).length;
  const webhookCount = Object.values(channels).filter((c) => c.webhook).length;
  const pollingCount = Object.values(channels).filter((c) => !c.webhook).length;

  const toggleExpand = (name: string) => {
    setExpanded((prev) =>
      prev.includes(name) ? prev.filter((n) => n !== name) : [...prev, name]
    );
  };

  return (
    <div className="flex-1 flex flex-col h-full">
      <div className="h-14 border-b border-border flex items-center px-4 gap-3 glass-subtle shrink-0">
        <Button variant="ghost" size="icon" className="md:hidden text-muted-foreground hover:text-primary" onClick={() => setSidebarOpen(true)}>
          <Menu className="h-5 w-5" />
        </Button>
        <Wifi className="h-5 w-5 text-primary" />
        <span className="text-sm font-medium">{isArabic ? "القنوات" : "Channels"}</span>
        <Badge variant="secondary" className="text-[10px] ms-2">{Object.keys(channels).length}</Badge>
        <div className="flex-1" />
        <div className="flex gap-1.5 text-[10px] text-muted-foreground">
          <span className="flex items-center gap-1"><Wifi className="h-3 w-3 text-emerald-400" />{activeCount}</span>
          <span className="flex items-center gap-1"><Webhook className="h-3 w-3 text-cyan-400" />{webhookCount}</span>
          <span className="flex items-center gap-1"><Radio className="h-3 w-3 text-violet-400" />{pollingCount}</span>
        </div>
        <Button variant="ghost" size="icon" className="h-7 w-7" onClick={loadChannels} disabled={loading}>
          <RefreshCw className={cn("h-3.5 w-3.5", loading && "animate-spin")} />
        </Button>
      </div>

      <ScrollArea className="flex-1">
        <div className="p-4 md:p-6 max-w-4xl mx-auto space-y-1">
          {!apiConnected && (
            <div className="flex items-center gap-2 p-4 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive text-xs">
              <WifiOff className="h-4 w-4 shrink-0" />
              {isArabic ? "الخادم غير متصل. القنوات مش متاحة." : "Server offline. Channels unavailable."}
            </div>
          )}

          {apiConnected && Object.keys(channels).length === 0 && (
            <div className="flex flex-col items-center gap-3 py-12 text-muted-foreground">
              <WifiOff className="h-8 w-8 opacity-30" />
              <p className="text-xs">{isArabic ? "مافيش قنوات متاحة" : "No channels available"}</p>
            </div>
          )}

          {Object.entries(channels).map(([name, info]) => {
            const Icon = channelIcons[name] || Bot;
            const color = channelColors[name] || "text-muted-foreground";
            const isExpanded = expanded.includes(name);
            return (
              <div key={name}>
                <div
                  role="button"
                  tabIndex={0}
                  onClick={() => toggleExpand(name)}
                  onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); toggleExpand(name); } }}
                  className={cn(
                    "w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors cursor-pointer",
                    "text-muted-foreground hover:bg-muted/30 hover:text-foreground"
                  )}
                >
                  <div className="h-8 w-8 rounded-lg flex items-center justify-center shrink-0 bg-muted/20">
                    <Icon className={cn("h-4 w-4", color)} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium capitalize truncate">{name.replace(/_/g, " ")}</p>
                    <p className="text-[10px] text-muted-foreground/60">
                      {info.webhook ? "Webhook" : "Polling"}
                    </p>
                  </div>
                  <Badge variant="outline" className={cn(
                    "text-[9px] px-1.5 h-4",
                    info.running ? "border-emerald-500/30 text-emerald-400" : "border-destructive/30 text-destructive"
                  )}>
                    {info.running ? (isArabic ? "فعال" : "Active") : (isArabic ? "متوقف" : "Inactive")}
                  </Badge>
                  {isExpanded ? <ChevronUp className="h-3 w-3 text-muted-foreground/50" /> : <ChevronDown className="h-3 w-3 text-muted-foreground/50" />}
                </div>

                {isExpanded && (
                  <div className="px-3 py-2 ms-11 mb-1 rounded-lg bg-muted/10 border border-border/20 text-[10px] space-y-1">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">{isArabic ? "النوع" : "Type"}</span>
                      <span>{info.webhook ? "Webhook" : "Polling"}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">{isArabic ? "الحالة" : "Status"}</span>
                      <span className={info.running ? "text-emerald-400" : "text-destructive"}>
                        {info.running ? (isArabic ? "يعمل" : "Running") : (isArabic ? "متوقف" : "Stopped")}
                      </span>
                    </div>
                    {info.requires && info.requires.length > 0 && (
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">{isArabic ? "المتطلبات" : "Requires"}</span>
                        <span className="text-[9px]">{info.requires.join(", ")}</span>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </ScrollArea>
    </div>
  );
}
