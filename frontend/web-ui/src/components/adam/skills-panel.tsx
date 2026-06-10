"use client";

import { useEffect, useState, useCallback } from "react";
import { useAppStore } from "@/lib/store";
import { fetchSkillsList, loadSkill } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Sparkles,
  Loader2,
  CheckCircle2,
  AlertCircle,
  Menu,
  BookOpen,
  Code,
  Bug,
  GitCommit,
  FileText,
  Brain,
} from "lucide-react";
import { useToast } from "@/hooks/use-toast";

const skillIcons: Record<string, React.ElementType> = {
  "code-review": Code,
  debug: Bug,
  "explain-code": BookOpen,
  "git-commit": GitCommit,
  "write-test": FileText,
};

export function SkillsPanel() {
  const { settings, setSidebarOpen, skillsList, setSkillsList, skillsLoading, setSkillsLoading } = useAppStore();
  const { toast } = useToast();
  const isArabic = settings.language === "ar";
  const [loaded, setLoaded] = useState<string[]>([]);
  const [loadingSkill, setLoadingSkill] = useState<string | null>(null);

  const loadSkills = useCallback(async () => {
    setSkillsLoading(true);
    try {
      const skills = await fetchSkillsList();
      setSkillsList(skills);
    } catch {
      toast({ title: isArabic ? "فشل تحميل المهارات" : "Failed to load skills", variant: "destructive" });
    } finally {
      setSkillsLoading(false);
    }
  }, [setSkillsList, setSkillsLoading, toast, isArabic]);

  useEffect(() => {
    loadSkills();
  }, [loadSkills]);

  const handleLoad = async (path: string, name: string) => {
    setLoadingSkill(name);
    try {
      const res = await loadSkill(path);
      if (res.success) {
        setLoaded((prev) => [...prev, name]);
        toast({ title: isArabic ? `مهارة ${name} محملة` : `${name} loaded`, description: res.result?.slice(0, 100) });
      } else {
        toast({ title: isArabic ? "فشل التحميل" : "Load failed", variant: "destructive" });
      }
    } catch {
      toast({ title: isArabic ? "خطأ في التحميل" : "Load error", variant: "destructive" });
    } finally {
      setLoadingSkill(null);
    }
  };

  const t = isArabic ? skillsAr : skillsEn;

  return (
    <div className="flex-1 h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center gap-3 p-4 border-b border-border shrink-0">
        <Button variant="ghost" size="icon" className="md:hidden" onClick={() => setSidebarOpen(true)}>
          <Menu className="h-5 w-5" />
        </Button>
        <Sparkles className="h-5 w-5 text-primary" />
        <h1 className="text-lg font-semibold">{t.title}</h1>
        <Button variant="outline" size="sm" className="mr-auto text-xs" onClick={loadSkills} disabled={skillsLoading}>
          {skillsLoading ? <Loader2 className="h-3 w-3 animate-spin mr-1" /> : null}
          {t.refresh}
        </Button>
      </div>

      {/* Content */}
      <ScrollArea className="flex-1 p-4">
        {skillsLoading && skillsList.length === 0 ? (
          <div className="flex items-center justify-center h-40">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : skillsList.length === 0 ? (
          <div className="text-center py-16">
            <Brain className="h-12 w-12 mx-auto text-muted-foreground/30 mb-4" />
            <p className="text-sm text-muted-foreground/60">{t.empty}</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {skillsList.map((skill) => {
              const Icon = skillIcons[skill.name] || Sparkles;
              const isLoaded = loaded.includes(skill.name);
              return (
                <Card key={skill.path} className="relative overflow-hidden">
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-3">
                        <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center">
                          <Icon className="h-5 w-5 text-primary" />
                        </div>
                        <div>
                          <CardTitle className="text-base">{skill.name}</CardTitle>
                          <p className="text-xs text-muted-foreground/70 mt-0.5">{skill.description}</p>
                        </div>
                      </div>
                      {isLoaded && (
                        <Badge variant="outline" className="border-emerald-500/30 text-emerald-400 text-[10px]">
                          <CheckCircle2 className="h-3 w-3 mr-1" />
                          {t.loaded}
                        </Badge>
                      )}
                    </div>
                  </CardHeader>
                  <CardContent>
                    <Button
                      variant={isLoaded ? "outline" : "default"}
                      size="sm"
                      className="w-full text-xs"
                      onClick={() => handleLoad(skill.path, skill.name)}
                      disabled={loadingSkill === skill.name || isLoaded}
                    >
                      {loadingSkill === skill.name ? (
                        <Loader2 className="h-3 w-3 animate-spin mr-1" />
                      ) : null}
                      {isLoaded ? t.loadedCta : t.loadCta}
                    </Button>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}
      </ScrollArea>
    </div>
  );
}

const skillsAr = {
  title: "المهارات",
  refresh: "تحديث",
  empty: "لا توجد مهارات متاحة",
  loaded: "محملة",
  loadCta: "تحميل المهارة",
  loadedCta: "محملة",
};

const skillsEn = {
  title: "Skills",
  refresh: "Refresh",
  empty: "No skills available",
  loaded: "Loaded",
  loadCta: "Load Skill",
  loadedCta: "Loaded",
};
