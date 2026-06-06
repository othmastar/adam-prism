"use client";

import { useAppStore } from "@/lib/store";
import { checkApiHealth, checkOllamaHealth } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Cpu,
  Globe,
  Thermometer,
  Sliders,
  Server,
  Menu,
  Save,
  RotateCcw,
  Check,
  Database,
  Bot,
  Shield,
  Network,
  RefreshCw,
  Wifi,
  WifiOff,
  Key,
  Users,
  Activity,
  AlertCircle,
  CheckCircle2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useCallback, useState } from "react";
import { useToast } from "@/hooks/use-toast";

export function SettingsPanel() {
  const {
    settings,
    updateSettings,
    ollamaModels,
    ollamaConnected,
    setOllamaConnected,
    setOllamaModels,
    apiConnected,
    setApiConnected,
    setSidebarOpen,
  } = useAppStore();

  const [localSettings, setLocalSettings] = useState(settings);
  const [hasChanges, setHasChanges] = useState(false);
  const [saving, setSaving] = useState(false);
  const [checkingApi, setCheckingApi] = useState(false);
  const [checkingOllama, setCheckingOllama] = useState(false);
  const { toast } = useToast();
  const isArabic = settings.language === "ar";
  const t = isArabic ? settingsAr : settingsEn;

  const handleChange = (key: string, value: unknown) => {
    setLocalSettings((prev) => ({ ...prev, [key]: value }));
    setHasChanges(true);
  };

  const handleSave = useCallback(async () => {
    setSaving(true);
    // Save to backend
    try {
      const url = localSettings.fastApiUrl;
      await fetch(`${url}/api/settings/update`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          inference_mode: localSettings.inferenceMode,
          lora_server_url: localSettings.loraServerUrl,
          model_name: localSettings.modelName,
        }),
      });
    } catch (e) {
      console.warn("Backend settings save failed:", e);
    }
    // Save to localStorage
    updateSettings(localSettings);
    setHasChanges(false);
    setSaving(false);
    toast({
      title: isArabic ? "تم الحفظ" : "Saved",
      description: isArabic ? "تم حفظ الإعدادات بنجاح" : "Settings saved successfully",
    });
  }, [localSettings, updateSettings, toast, isArabic]);

  const handleReset = () => {
    setLocalSettings({
      modelName: "gemma4:e4b",
      inferenceMode: "ollama",
      loraServerUrl: "http://localhost:8080",
      temperature: 0.7,
      topP: 0.9,
      topK: 40,
      language: "ar",
      ollamaUrl: "http://localhost:11434",
      fastApiUrl: "http://localhost:8000",
      qdrantUrl: "http://localhost:6333",
      qdrantApiKey: "",
      telegramBotToken: "",
      telegramChatId: "",
      authorizedUsers: "OthMastar",
      tailscaleIp: "",
      tailscaleStatus: "disconnected",
      systemPrompt: "أنت آدم بريزم، مساعد ذكي لـ OthMastar. تجيب بالعربي. مختصر وواضح.",
    });
    setHasChanges(true);
  };

  const handleCheckApi = useCallback(async () => {
    setCheckingApi(true);
    try {
      const result = await checkApiHealth();
      setApiConnected(result.connected);
      toast({
        title: result.connected
          ? isArabic ? "API متصل" : "API Connected"
          : isArabic ? "API غير متصل" : "API Disconnected",
        description: result.connected
          ? isArabic ? "تم الاتصال بنجاح" : "Connection successful"
          : result.error || (isArabic ? "فشل الاتصال" : "Connection failed"),
        variant: result.connected ? "default" : "destructive",
      });
    } finally {
      setCheckingApi(false);
    }
  }, [setApiConnected, toast, isArabic]);

  const handleCheckOllama = useCallback(async () => {
    setCheckingOllama(true);
    try {
      const result = await checkOllamaHealth(localSettings.ollamaUrl);
      setOllamaConnected(result.connected);
      if (result.models.length > 0) {
        setOllamaModels(result.models);
      }
      toast({
        title: result.connected
          ? isArabic ? "Ollama متصل" : "Ollama Connected"
          : isArabic ? "Ollama غير متصل" : "Ollama Disconnected",
        description: result.connected
          ? `${result.models.length} ${isArabic ? "نماذج متاحة" : "models available"}`
          : isArabic ? "فشل الاتصال" : "Connection failed",
        variant: result.connected ? "default" : "destructive",
      });
    } finally {
      setCheckingOllama(false);
    }
  }, [localSettings.ollamaUrl, setOllamaConnected, setOllamaModels, toast, isArabic]);

  return (
    <div className="flex-1 flex flex-col h-full">
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
        <div className="flex items-center gap-2 flex-1">
          <Sliders className="h-5 w-5 text-primary" />
          <span className="text-sm font-medium">{t.title}</span>
        </div>

        {hasChanges && (
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              className="text-xs text-muted-foreground"
              onClick={handleReset}
            >
              <RotateCcw className="h-3 w-3 me-1" />
              {t.reset}
            </Button>
            <Button
              size="sm"
              className="text-xs bg-gradient-to-bl from-primary via-purple-500 to-cyan-500 text-white hover:opacity-90 gap-1"
              onClick={handleSave}
              disabled={saving}
            >
              {saving ? (
                <div className="h-3 w-3 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <Check className="h-3 w-3" />
              )}
              {t.save}
            </Button>
          </div>
        )}
      </div>

      <div className="flex-1 p-4 md:p-6 overflow-y-auto">
        <div className="max-w-2xl mx-auto space-y-6">
          {/* Model Configuration */}
          <Card className="glass border-0 prism-border overflow-hidden">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-base">
                <Cpu className="h-5 w-5 text-primary" />
                {t.modelConfig}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-5">
              <div className="space-y-2">
                <Label className="text-xs text-muted-foreground">{t.modelName}</Label>
                {ollamaModels.length > 0 ? (
                  <Select
                    value={localSettings.modelName}
                    onValueChange={(val) => handleChange("modelName", val)}
                  >
                    <SelectTrigger className="bg-muted/50 border-border">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {ollamaModels.map((model) => (
                        <SelectItem key={model} value={model}>
                          {model}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                ) : (
                  <Input
                    value={localSettings.modelName}
                    onChange={(e) => handleChange("modelName", e.target.value)}
                    className="bg-muted/50 border-border"
                    placeholder="gemma4:e4b"
                  />
                )}
              </div>

              <div className="space-y-2">
                <Label className="text-xs text-muted-foreground">{t.inferenceMode}</Label>
                <Select
                  value={localSettings.inferenceMode}
                  onValueChange={(val) => handleChange("inferenceMode", val)}
                >
                  <SelectTrigger className="bg-muted/50 border-border">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="ollama">{t.inferenceOllama}</SelectItem>
                    <SelectItem value="lora">{t.inferenceLora}</SelectItem>
                  </SelectContent>
                </Select>
                <p className="text-[10px] text-muted-foreground">
                  {localSettings.inferenceMode === "lora" ? t.inferenceLoraDesc : t.inferenceOllamaDesc}
                </p>
              </div>

              {localSettings.inferenceMode === "lora" && (
                <div className="space-y-2">
                  <Label className="text-xs text-muted-foreground">{t.loraServerUrl}</Label>
                  <Input
                    value={localSettings.loraServerUrl}
                    onChange={(e) => handleChange("loraServerUrl", e.target.value)}
                    className="bg-muted/50 border-border"
                    placeholder="http://localhost:8080"
                    dir="ltr"
                  />
                </div>
              )}

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label className="text-xs text-muted-foreground flex items-center gap-1.5">
                    <Thermometer className="h-3.5 w-3.5" />
                    {t.temperature}
                  </Label>
                  <Badge variant="outline" className="text-[10px] border-primary/30 text-primary">
                    {localSettings.temperature.toFixed(1)}
                  </Badge>
                </div>
                <Slider
                  value={[localSettings.temperature]}
                  onValueChange={([val]) => handleChange("temperature", val)}
                  min={0}
                  max={2}
                  step={0.1}
                  className="[&_[role=slider]]:bg-primary [&_[role=slider]]:border-primary"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label className="text-xs text-muted-foreground">Top P</Label>
                    <Badge variant="outline" className="text-[10px] border-primary/30 text-primary">
                      {localSettings.topP.toFixed(1)}
                    </Badge>
                  </div>
                  <Slider
                    value={[localSettings.topP]}
                    onValueChange={([val]) => handleChange("topP", val)}
                    min={0}
                    max={1}
                    step={0.05}
                    className="[&_[role=slider]]:bg-primary [&_[role=slider]]:border-primary"
                  />
                </div>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label className="text-xs text-muted-foreground">Top K</Label>
                    <Badge variant="outline" className="text-[10px] border-primary/30 text-primary">
                      {localSettings.topK}
                    </Badge>
                  </div>
                  <Slider
                    value={[localSettings.topK]}
                    onValueChange={([val]) => handleChange("topK", val)}
                    min={1}
                    max={100}
                    step={1}
                    className="[&_[role=slider]]:bg-primary [&_[role=slider]]:border-primary"
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Language & Appearance */}
          <Card className="glass border-0 prism-border overflow-hidden">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-base">
                <Globe className="h-5 w-5 text-cyan-400" />
                {t.languageAppearance}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-3 p-3 rounded-lg bg-muted/50">
                <span className="text-sm">{isArabic ? "العربية" : "Arabic"}</span>
                <div className="flex-1" />
                <Switch
                  checked={localSettings.language === "en"}
                  onCheckedChange={(checked) =>
                    handleChange("language", checked ? "en" : "ar")
                  }
                />
                <span className="text-sm">{isArabic ? "English" : "الإنجليزية"}</span>
              </div>
              <div className="p-3 rounded-lg bg-primary/5 border border-primary/10">
                <p className="text-xs text-muted-foreground">
                  {localSettings.language === "ar"
                    ? "🔄 واجهة RTL (من اليمين لليسار) مفعّلة"
                    : "🔄 LTR (Left-to-Right) interface active"}
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Server Configuration */}
          <Card className="glass border-0 prism-border overflow-hidden">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-base">
                <Server className="h-5 w-5 text-blue-400" />
                {t.serverConfig}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-5">
              {/* FastAPI URL */}
              <div className="space-y-2">
                <Label className="text-xs text-muted-foreground">{t.fastApiUrl}</Label>
                <div className="flex gap-2">
                  <Input
                    value={localSettings.fastApiUrl}
                    onChange={(e) => handleChange("fastApiUrl", e.target.value)}
                    className="bg-muted/50 border-border"
                    placeholder="http://localhost:8000"
                    dir="ltr"
                  />
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleCheckApi}
                    disabled={checkingApi}
                    className={cn(
                      "gap-1 shrink-0",
                      apiConnected
                        ? "border-emerald-500/30 text-emerald-400"
                        : "border-destructive/30 text-destructive"
                    )}
                  >
                    {checkingApi ? (
                      <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                    ) : apiConnected ? (
                      <Wifi className="h-3.5 w-3.5" />
                    ) : (
                      <WifiOff className="h-3.5 w-3.5" />
                    )}
                  </Button>
                </div>
                <div className="flex items-center gap-2">
                  <div
                    className={cn(
                      "h-2 w-2 rounded-full",
                      apiConnected ? "bg-emerald-400 pulse-ring" : "bg-destructive"
                    )}
                  />
                  <span className="text-[10px] text-muted-foreground">
                    {apiConnected ? t.apiConnected : t.apiDisconnected}
                  </span>
                </div>
              </div>

              <Separator className="bg-border" />

              {/* Ollama URL */}
              <div className="space-y-2">
                <Label className="text-xs text-muted-foreground">{t.ollamaUrl}</Label>
                <div className="flex gap-2">
                  <Input
                    value={localSettings.ollamaUrl}
                    onChange={(e) => handleChange("ollamaUrl", e.target.value)}
                    className="bg-muted/50 border-border"
                    placeholder="http://localhost:11434"
                    dir="ltr"
                  />
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleCheckOllama}
                    disabled={checkingOllama}
                    className={cn(
                      "gap-1 shrink-0",
                      ollamaConnected
                        ? "border-emerald-500/30 text-emerald-400"
                        : "border-destructive/30 text-destructive"
                    )}
                  >
                    {checkingOllama ? (
                      <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                    ) : ollamaConnected ? (
                      <Wifi className="h-3.5 w-3.5" />
                    ) : (
                      <WifiOff className="h-3.5 w-3.5" />
                    )}
                  </Button>
                </div>
                <div className="flex items-center gap-2">
                  <div
                    className={cn(
                      "h-2 w-2 rounded-full",
                      ollamaConnected ? "bg-emerald-400 pulse-ring" : "bg-destructive"
                    )}
                  />
                  <span className="text-[10px] text-muted-foreground">
                    {ollamaConnected ? t.ollamaConnected : t.ollamaDisconnected}
                  </span>
                </div>
              </div>

              <Separator className="bg-border" />

              {/* System Prompt */}
              <div className="space-y-2">
                <Label className="text-xs text-muted-foreground">{t.systemPrompt}</Label>
                <Textarea
                  value={localSettings.systemPrompt}
                  onChange={(e) => handleChange("systemPrompt", e.target.value)}
                  className="min-h-[100px] bg-muted/50 border-border text-sm"
                  dir={isArabic ? "rtl" : "ltr"}
                />
              </div>
            </CardContent>
          </Card>

          {/* Qdrant Configuration */}
          <Card className="glass border-0 prism-border overflow-hidden">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-base">
                <Database className="h-5 w-5 text-primary" />
                {t.qdrantConfig}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label className="text-xs text-muted-foreground">{t.qdrantUrl}</Label>
                <Input
                  value={localSettings.qdrantUrl}
                  onChange={(e) => handleChange("qdrantUrl", e.target.value)}
                  className="bg-muted/50 border-border"
                  placeholder="http://localhost:6333"
                  dir="ltr"
                />
              </div>
              <div className="space-y-2">
                <Label className="text-xs text-muted-foreground flex items-center gap-1.5">
                  <Key className="h-3.5 w-3.5" />
                  {t.qdrantApiKey}
                </Label>
                <Input
                  value={localSettings.qdrantApiKey}
                  onChange={(e) => handleChange("qdrantApiKey", e.target.value)}
                  className="bg-muted/50 border-border"
                  placeholder="••••••••"
                  type="password"
                  dir="ltr"
                />
                <p className="text-[10px] text-muted-foreground">{t.qdrantApiKeyDesc}</p>
              </div>
            </CardContent>
          </Card>

          {/* Telegram Bot */}
          <Card className="glass border-0 prism-border overflow-hidden">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-base">
                <Bot className="h-5 w-5 text-cyan-400" />
                {t.telegramConfig}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label className="text-xs text-muted-foreground">{t.telegramBotToken}</Label>
                <Input
                  value={localSettings.telegramBotToken}
                  onChange={(e) => handleChange("telegramBotToken", e.target.value)}
                  className="bg-muted/50 border-border"
                  placeholder="123456:ABC-DEF..."
                  type="password"
                  dir="ltr"
                />
              </div>
              <div className="space-y-2">
                <Label className="text-xs text-muted-foreground">{t.telegramChatId}</Label>
                <Input
                  value={localSettings.telegramChatId}
                  onChange={(e) => handleChange("telegramChatId", e.target.value)}
                  className="bg-muted/50 border-border"
                  placeholder="-1001234567890"
                  dir="ltr"
                />
              </div>
            </CardContent>
          </Card>

          {/* Security */}
          <Card className="glass border-0 prism-border overflow-hidden">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-base">
                <Shield className="h-5 w-5 text-emerald-400" />
                {t.securityConfig}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label className="text-xs text-muted-foreground flex items-center gap-1.5">
                  <Users className="h-3.5 w-3.5" />
                  {t.authorizedUsers}
                </Label>
                <Input
                  value={localSettings.authorizedUsers}
                  onChange={(e) => handleChange("authorizedUsers", e.target.value)}
                  className="bg-muted/50 border-border"
                  placeholder="OthMastar, admin"
                  dir="ltr"
                />
                <p className="text-[10px] text-muted-foreground">{t.authorizedUsersDesc}</p>
              </div>

              <div className="p-3 rounded-lg bg-emerald-500/5 border border-emerald-500/10">
                <div className="flex items-center gap-2 mb-1">
                  <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                  <span className="text-xs font-medium text-emerald-400">{t.securityActive}</span>
                </div>
                <p className="text-[10px] text-muted-foreground">{t.securityDesc}</p>
              </div>
            </CardContent>
          </Card>

          {/* Tailscale */}
          <Card className="glass border-0 prism-border overflow-hidden">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-base">
                <Network className="h-5 w-5 text-blue-400" />
                {t.tailscaleConfig}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label className="text-xs text-muted-foreground">{t.tailscaleIp}</Label>
                <Input
                  value={localSettings.tailscaleIp}
                  onChange={(e) => handleChange("tailscaleIp", e.target.value)}
                  className="bg-muted/50 border-border"
                  placeholder="100.x.x.x"
                  dir="ltr"
                />
              </div>
              <div className="flex items-center gap-3 p-3 rounded-lg bg-muted/50">
                <Activity className="h-4 w-4 text-blue-400" />
                <span className="text-xs text-muted-foreground">{t.tailscaleStatus}</span>
                <div className="flex-1" />
                <Badge
                  variant="outline"
                  className={cn(
                    "text-[10px]",
                    localSettings.tailscaleStatus === "connected"
                      ? "border-emerald-500/30 text-emerald-400"
                      : "border-destructive/30 text-destructive"
                  )}
                >
                  {localSettings.tailscaleStatus === "connected" ? t.connected : t.disconnected}
                </Badge>
              </div>
            </CardContent>
          </Card>

          {/* About */}
          <Card className="glass border-0 prism-border overflow-hidden">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-full bg-gradient-to-br from-primary via-purple-500 to-cyan-500 flex items-center justify-center">
                  <Save className="h-5 w-5 text-white" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium prism-text">آدم بريزم v2.0</p>
                  <p className="text-[10px] text-muted-foreground">{t.aboutDesc}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

const settingsAr = {
  title: "الإعدادات",
  save: "حفظ",
  reset: "إعادة تعيين",
  modelConfig: "إعدادات النموذج",
  modelName: "اسم النموذج",
  inferenceMode: "وضع الاستدلال",
  inferenceOllama: "Ollama (أسرع - فصحى)",
  inferenceLora: "LoRA Server (مصري - GPU)",
  inferenceOllamaDesc: "موديل مدمج على Ollama — GPU، ردود فصحى/إنجليزي حسب الـ system prompt",
  inferenceLoraDesc: "LoRA adapter + GPU — ردود مصرية طبيعية مضمونة",
  loraServerUrl: "عنوان LoRA Server",
  temperature: "الحرارة (Temperature)",
  languageAppearance: "اللغة والمظهر",
  serverConfig: "إعدادات الخوادم",
  fastApiUrl: "عنوان FastAPI",
  ollamaUrl: "عنوان Ollama",
  apiConnected: "API متصل",
  apiDisconnected: "API غير متصل",
  ollamaConnected: "Ollama متصل",
  ollamaDisconnected: "Ollama غير متصل",
  systemPrompt: "الموجه النظامي",
  qdrantConfig: "إعدادات Qdrant",
  qdrantUrl: "عنوان Qdrant",
  qdrantApiKey: "مفتاح API",
  qdrantApiKeyDesc: "اتركه فارغاً إذا لم يكن مطلوباً",
  telegramConfig: "إعدادات Telegram",
  telegramBotToken: "رمز البوت",
  telegramChatId: "معرف المحادثة",
  securityConfig: "إعدادات الأمان",
  authorizedUsers: "المستخدمون المصرح لهم",
  authorizedUsersDesc: "أسماء المستخدمين مفصولة بفواصل",
  securityActive: "الأمان مفعّل",
  securityDesc: "المستخدمون المصرح لهم فقط يمكنهم الوصول للنظام",
  tailscaleConfig: "إعدادات Tailscale",
  tailscaleIp: "عنوان IP",
  tailscaleStatus: "حالة Tailscale",
  connected: "متصل",
  disconnected: "غير متصل",
  aboutDesc: "نظام التوأم الرقمي الذكي لـ OthMastar · مدعوم بـ FastAPI + Ollama",
};

const settingsEn = {
  title: "Settings",
  save: "Save",
  reset: "Reset",
  modelConfig: "Model Configuration",
  modelName: "Model Name",
  inferenceMode: "Inference Mode",
  inferenceOllama: "Ollama (faster - Fusha)",
  inferenceLora: "LoRA Server (Egyptian - GPU)",
  inferenceOllamaDesc: "Merged model via Ollama — GPU, Fusha/English responses",
  inferenceLoraDesc: "LoRA adapter + GPU — guaranteed Egyptian Arabic",
  loraServerUrl: "LoRA Server URL",
  temperature: "Temperature",
  languageAppearance: "Language & Appearance",
  serverConfig: "Server Configuration",
  fastApiUrl: "FastAPI URL",
  ollamaUrl: "Ollama URL",
  apiConnected: "API Connected",
  apiDisconnected: "API Disconnected",
  ollamaConnected: "Ollama Connected",
  ollamaDisconnected: "Ollama Disconnected",
  systemPrompt: "System Prompt",
  qdrantConfig: "Qdrant Configuration",
  qdrantUrl: "Qdrant URL",
  qdrantApiKey: "API Key",
  qdrantApiKeyDesc: "Leave empty if not required",
  telegramConfig: "Telegram Bot",
  telegramBotToken: "Bot Token",
  telegramChatId: "Chat ID",
  securityConfig: "Security Settings",
  authorizedUsers: "Authorized Users",
  authorizedUsersDesc: "Comma-separated usernames",
  securityActive: "Security Active",
  securityDesc: "Only authorized users can access the system",
  tailscaleConfig: "Tailscale",
  tailscaleIp: "IP Address",
  tailscaleStatus: "Tailscale Status",
  connected: "Connected",
  disconnected: "Disconnected",
  aboutDesc: "Personal Digital Twin AI for OthMastar · Powered by FastAPI + Ollama",
};
