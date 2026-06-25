/**
 * MCPPanel — لوحة MCP (Model Context Protocol)
 * ================================================
 * تضيف لـ frontend القدرة على:
 * - إضافة MCP servers
 * - عرض الأدوات المتاحة من كل server
 * - حذف servers
 * - تنفيذ أدوات MCP
 *
 * Usage:
 *   <MCPPanel />
 */

"use client";

import { useState, useEffect, useCallback } from "react";
import {
  addMCPServer,
  listMCPServers,
  listMCPTools,
  removeMCPServer,
  executeTool,
  type MCPServer,
  type MCPToolInfo,
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
  Plus,
  Trash2,
  Server,
  Wrench,
  Play,
  AlertCircle,
} from "lucide-react";
import { useToast } from "@/hooks/use-toast";

export function MCPPanel() {
  const [servers, setServers] = useState<MCPServer[]>([]);
  const [tools, setTools] = useState<MCPToolInfo[]>([]);
  const [showAdd, setShowAdd] = useState(false);
  const [loading, setLoading] = useState(false);

  // Add server form
  const [name, setName] = useState("");
  const [command, setCommand] = useState("npx");
  const [args, setArgs] = useState("-y @modelcontextprotocol/server-filesystem /tmp");
  const [env, setEnv] = useState("");

  // Execute tool
  const [toolParams, setToolParams] = useState("{}");
  const [toolResult, setToolResult] = useState<string>("");

  const { toast } = useToast();

  const loadServers = useCallback(async () => {
    try {
      const data = await listMCPServers();
      setServers(data.servers || []);
    } catch (e) {
      // silent
    }
  }, []);

  const loadTools = useCallback(async () => {
    try {
      const data = await listMCPTools();
      setTools(data.tools || []);
    } catch (e) {
      // silent
    }
  }, []);

  useEffect(() => {
    loadServers();
    loadTools();
  }, [loadServers, loadTools]);

  const handleAdd = useCallback(async () => {
    if (!name.trim() || !command.trim()) return;
    setLoading(true);
    try {
      const argsList = args.split(/\s+/).filter(Boolean);
      const envObj = env.trim()
        ? JSON.parse(env)
        : undefined;

      const result = await addMCPServer(name, command, argsList, envObj);
      if (result.success) {
        toast({ title: "تمت الإضافة", description: `Server: ${name}` });
        setName("");
        setArgs("");
        setEnv("");
        setShowAdd(false);
        await loadServers();
        await loadTools();
      } else {
        toast({ title: "فشل الإضافة", variant: "destructive" });
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
  }, [name, command, args, env, toast, loadServers, loadTools]);

  const handleRemove = useCallback(
    async (serverName: string) => {
      try {
        await removeMCPServer(serverName);
        toast({ title: "تم الحذف", description: serverName });
        await loadServers();
        await loadTools();
      } catch (e) {
        toast({
          title: "فشل الحذف",
          description: e instanceof Error ? e.message : String(e),
          variant: "destructive",
        });
      }
    },
    [toast, loadServers, loadTools],
  );

  const handleExecute = useCallback(
    async (toolName: string) => {
      try {
        const params = JSON.parse(toolParams);
        const result = await executeTool(toolName, params);
        setToolResult(JSON.stringify(result, null, 2));
      } catch (e) {
        setToolResult(`Error: ${e instanceof Error ? e.message : String(e)}`);
      }
    },
    [toolParams],
  );

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Server className="h-5 w-5" />
          MCP Servers
          <Badge variant="outline">{servers.length} servers</Badge>
        </CardTitle>
        <CardDescription>
          Model Context Protocol — اربط آدم بآلاف الأدوات الخارجية
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {servers.length === 0 && (
          <div className="flex items-start gap-2 p-3 rounded bg-blue-50 border border-blue-200 text-xs">
            <AlertCircle className="h-4 w-4 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-medium">مفيش MCP servers متصلة</p>
              <p className="text-muted-foreground mt-1">
                أضف server زي: <code className="bg-muted px-1 rounded">npx -y @modelcontextprotocol/server-filesystem /tmp</code>
              </p>
            </div>
          </div>
        )}

        {/* Add server */}
        {showAdd ? (
          <div className="space-y-2 p-3 rounded border bg-muted/50">
            <Input
              placeholder="اسم الـ server (مثلاً: filesystem)"
              value={name}
              onChange={(e) => setName(e.target.value)}
              dir="ltr"
            />
            <div className="flex gap-2">
              <Input
                placeholder="command (npx, uvx, python3)"
                value={command}
                onChange={(e) => setCommand(e.target.value)}
                className="w-1/3"
                dir="ltr"
              />
              <Input
                placeholder="args (مفصولة بمسافات)"
                value={args}
                onChange={(e) => setArgs(e.target.value)}
                className="flex-1"
                dir="ltr"
              />
            </div>
            <Input
              placeholder='env vars (JSON، اختياري): {"API_KEY":"..."}'
              value={env}
              onChange={(e) => setEnv(e.target.value)}
              dir="ltr"
            />
            <div className="flex gap-2">
              <Button onClick={handleAdd} disabled={loading} size="sm">
                {loading ? "جاري..." : "إضافة"}
              </Button>
              <Button onClick={() => setShowAdd(false)} size="sm" variant="outline">
                إلغاء
              </Button>
            </div>
          </div>
        ) : (
          <Button onClick={() => setShowAdd(true)} size="sm" variant="outline">
            <Plus className="h-4 w-4 ml-1" />
            إضافة MCP server
          </Button>
        )}

        {/* Servers list */}
        {servers.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-medium">المتصلين:</h4>
            {servers.map((s) => (
              <div key={s.name} className="p-2 rounded border bg-card">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Badge variant={s.connected ? "default" : "secondary"}>
                      {s.connected ? "متصل" : "غير متصل"}
                    </Badge>
                    <span className="font-medium text-sm">{s.name}</span>
                    <span className="text-xs text-muted-foreground">
                      {s.tools_count} أداة
                    </span>
                  </div>
                  <Button
                    size="icon"
                    variant="ghost"
                    className="h-6 w-6"
                    onClick={() => handleRemove(s.name)}
                  >
                    <Trash2 className="h-3 w-3" />
                  </Button>
                </div>
                <div className="text-xs text-muted-foreground mt-1" dir="ltr">
                  {s.command} {s.args.join(" ")}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Tools */}
        {tools.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-medium flex items-center gap-2">
              <Wrench className="h-4 w-4" />
              الأدوات المتاحة ({tools.length})
            </h4>
            <ScrollArea className="h-[200px]">
              <div className="space-y-1">
                {tools.map((t) => (
                  <div
                    key={t.name}
                    className="p-2 rounded border bg-card hover:bg-accent/50"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <span className="font-mono text-xs font-medium" dir="ltr">
                          {t.name}
                        </span>
                        <Badge variant="outline" className="ml-2 text-xs">
                          {t.server}
                        </Badge>
                      </div>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => handleExecute(t.name)}
                      >
                        <Play className="h-3 w-3" />
                      </Button>
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">
                      {t.description}
                    </p>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </div>
        )}

        {/* Tool params & result */}
        <div className="space-y-2">
          <Input
            placeholder='params (JSON): {"path":"/tmp/test.txt"}'
            value={toolParams}
            onChange={(e) => setToolParams(e.target.value)}
            dir="ltr"
          />
          {toolResult && (
            <pre className="text-xs p-2 rounded bg-muted max-h-32 overflow-auto" dir="ltr">
              {toolResult}
            </pre>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
