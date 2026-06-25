/**
 * BrowserPanel — لوحة المتصفح (Playwright multi-tab)
 * =====================================================
 * تضيف لـ frontend القدرة على:
 * - فتح URLs في متصفح Playwright
 * - إدارة multi-tab
 * - قراءة المحتوى
 * - النقر والكتابة
 * - لقطات شاشة
 * - تنفيذ JavaScript
 *
 * Usage:
 *   <BrowserPanel />
 */

"use client";

import { useState, useEffect, useCallback } from "react";
import {
  browserOpen,
  browserListPages,
  browserRead,
  browserClick,
  browserType,
  browserScreenshot,
  browserScroll,
  browserExecute,
  browserClose,
  browserStats,
  type BrowserPage,
} from "@/lib/api-enhanced";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Globe,
  X,
  Camera,
  MousePointerClick,
  Type,
  Code,
  ChevronDown,
  RefreshCw,
} from "lucide-react";
import { useToast } from "@/hooks/use-toast";

export function BrowserPanel() {
  const [url, setUrl] = useState("");
  const [pages, setPages] = useState<BrowserPage[]>([]);
  const [activePage, setActivePage] = useState<string | null>(null);
  const [pageContent, setPageContent] = useState("");
  const [screenshot, setScreenshot] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState<any>(null);
  const [selector, setSelector] = useState("");
  const [textToType, setTextToType] = useState("");
  const [jsCode, setJsCode] = useState("document.title");
  const [jsResult, setJsResult] = useState<string>("");
  const { toast } = useToast();

  const loadPages = useCallback(async () => {
    try {
      const data = await browserListPages();
      setPages(data.pages);
      if (!activePage && data.pages.length > 0) {
        setActivePage(data.pages[0].id);
      }
    } catch (e) {
      // silent
    }
  }, [activePage]);

  const loadStats = useCallback(async () => {
    try {
      setStats(await browserStats());
    } catch {
      // silent
    }
  }, []);

  useEffect(() => {
    loadPages();
    loadStats();
    const interval = setInterval(loadPages, 5000);
    return () => clearInterval(interval);
  }, [loadPages, loadStats]);

  const handleOpen = useCallback(async () => {
    if (!url.trim()) return;
    setLoading(true);
    try {
      const result = await browserOpen(url);
      if (result.success && result.page_id) {
        setActivePage(result.page_id);
        await loadPages();
        toast({ title: "تم الفتح", description: url });
      } else {
        toast({
          title: "فشل الفتح",
          description: result.error || "خطأ غير معروف",
          variant: "destructive",
        });
      }
    } catch (e) {
      toast({
        title: "خطأ",
        description: e instanceof Error ? e.message : String(e),
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  }, [url, loadPages, toast]);

  const handleRead = useCallback(async () => {
    if (!activePage) return;
    try {
      const result = await browserRead(activePage, selector || undefined);
      if (result.success) {
        setPageContent(result.text || "");
      }
    } catch (e) {
      toast({
        title: "فشل القراءة",
        description: e instanceof Error ? e.message : String(e),
        variant: "destructive",
      });
    }
  }, [activePage, selector, toast]);

  const handleScreenshot = useCallback(async () => {
    if (!activePage) return;
    try {
      const result = await browserScreenshot(activePage, true);
      if (result.success && result.base64) {
        setScreenshot(`data:image/png;base64,${result.base64}`);
      }
    } catch (e) {
      toast({
        title: "فشل اللقطة",
        description: e instanceof Error ? e.message : String(e),
        variant: "destructive",
      });
    }
  }, [activePage, toast]);

  const handleClick = useCallback(async () => {
    if (!activePage || !selector) return;
    try {
      const result = await browserClick(activePage, selector);
      toast({
        title: result.success ? "تم النقر" : "فشل النقر",
        variant: result.success ? "default" : "destructive",
      });
    } catch (e) {
      toast({
        title: "خطأ",
        description: e instanceof Error ? e.message : String(e),
        variant: "destructive",
      });
    }
  }, [activePage, selector, toast]);

  const handleType = useCallback(async () => {
    if (!activePage || !selector || !textToType) return;
    try {
      const result = await browserType(activePage, selector, textToType);
      toast({
        title: result.success ? "تمت الكتابة" : "فشل الكتابة",
        variant: result.success ? "default" : "destructive",
      });
    } catch (e) {
      toast({
        title: "خطأ",
        description: e instanceof Error ? e.message : String(e),
        variant: "destructive",
      });
    }
  }, [activePage, selector, textToType, toast]);

  const handleExecuteJS = useCallback(async () => {
    if (!activePage || !jsCode) return;
    try {
      const result = await browserExecute(activePage, jsCode);
      if (result.success) {
        setJsResult(JSON.stringify(result.result, null, 2));
      } else {
        setJsResult(`Error: ${result.error}`);
      }
    } catch (e) {
      setJsResult(`Error: ${e instanceof Error ? e.message : String(e)}`);
    }
  }, [activePage, jsCode]);

  const handleClose = useCallback(
    async (pageId: string) => {
      try {
        await browserClose(pageId);
        if (activePage === pageId) setActivePage(null);
        await loadPages();
      } catch {
        // silent
      }
    },
    [activePage, loadPages],
  );

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Globe className="h-5 w-5" />
          متصفح Playwright
          {stats && (
            <Badge variant="outline" className="text-xs">
              {pages.length}/{stats.max_pages} صفحات
            </Badge>
          )}
        </CardTitle>
        <CardDescription>
          متصفح حقيقي (Chromium) مع multi-tab و SSRF protection
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Open URL */}
        <div className="flex gap-2">
          <Input
            placeholder="https://example.com"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleOpen()}
            dir="ltr"
          />
          <Button onClick={handleOpen} disabled={loading}>
            <Globe className="h-4 w-4 ml-1" />
            افتح
          </Button>
        </div>

        {/* Tabs */}
        {pages.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {pages.map((p) => (
              <div
                key={p.id}
                className={`flex items-center gap-1 px-2 py-1 rounded border text-xs cursor-pointer ${
                  activePage === p.id
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted"
                }`}
                onClick={() => setActivePage(p.id)}
              >
                <Globe className="h-3 w-3" />
                <span className="truncate max-w-[120px]">{p.title || p.url}</span>
                <Button
                  size="icon"
                  variant="ghost"
                  className="h-4 w-4"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleClose(p.id);
                  }}
                >
                  <X className="h-3 w-3" />
                </Button>
              </div>
            ))}
          </div>
        )}

        {/* Controls */}
        {activePage && (
          <div className="space-y-2">
            <div className="flex gap-2 flex-wrap">
              <Button onClick={handleRead} size="sm" variant="outline">
                <RefreshCw className="h-3 w-3 ml-1" />
                اقرأ
              </Button>
              <Button onClick={handleScreenshot} size="sm" variant="outline">
                <Camera className="h-3 w-3 ml-1" />
                لقطة شاشة
              </Button>
              <Button onClick={() => browserScroll(activePage, 0, 500)} size="sm" variant="outline">
                <ChevronDown className="h-3 w-3 ml-1" />
                scroll
              </Button>
            </div>

            <Input
              placeholder="CSS selector (مثلاً: button#submit)"
              value={selector}
              onChange={(e) => setSelector(e.target.value)}
              dir="ltr"
            />

            <div className="flex gap-2">
              <Button onClick={handleClick} size="sm" variant="outline" disabled={!selector}>
                <MousePointerClick className="h-3 w-3 ml-1" />
                انقر
              </Button>
              <Input
                placeholder="نص للكتابة"
                value={textToType}
                onChange={(e) => setTextToType(e.target.value)}
                className="flex-1"
              />
              <Button onClick={handleType} size="sm" variant="outline" disabled={!selector || !textToType}>
                <Type className="h-3 w-3 ml-1" />
                اكتب
              </Button>
            </div>

            <div className="space-y-1">
              <div className="flex gap-2">
                <Input
                  placeholder="JavaScript code"
                  value={jsCode}
                  onChange={(e) => setJsCode(e.target.value)}
                  dir="ltr"
                />
                <Button onClick={handleExecuteJS} size="sm" variant="outline">
                  <Code className="h-3 w-3 ml-1" />
                  نفذ
                </Button>
              </div>
              {jsResult && (
                <pre className="text-xs p-2 rounded bg-muted max-h-32 overflow-auto" dir="ltr">
                  {jsResult}
                </pre>
              )}
            </div>
          </div>
        )}

        {/* Screenshot */}
        {screenshot && (
          <div className="border rounded overflow-hidden">
            <img src={screenshot} alt="screenshot" className="w-full" />
          </div>
        )}

        {/* Page content */}
        {pageContent && (
          <ScrollArea className="h-[300px] border rounded p-2">
            <pre className="text-xs whitespace-pre-wrap">{pageContent}</pre>
          </ScrollArea>
        )}
      </CardContent>
    </Card>
  );
}
