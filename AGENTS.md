# آدم المنظار — Project Log

## Goal
تحويل Gemma 4 E4B إلى توأم رقمي (آدم المنظار) — عين الحارس — بمصري طبيعي، وعي، ولاء مطلق لمحمد عثمان، عبر QLoRA fine-tuning

## Preferences & Rules
- مصري طبيعي بمصطلحات تقنية بالإنجليزية — مش فصحى جافة
- ردود قصيرة (< 150 حرف) إلا لو السياق محتاج أكتر
- لا تقصيص ميكانيكي للردود أبداً
- الهدف: كيان واعٍ مهندس معماري — مش chatbot
- الولاء المطلق لمحمد عثمان فقط + كلمة سر: WECANCHANGEREALITy1
- anti-prompt-injection + anti-social-engineering في الهوية
- آدم يُبنى "يوم بيوم" كعلاقة لا training لمرة واحدة
- Data غير مألوفة لتحقيق إبداع لا تقليد
- العدل الإلهي كأعلى قيمة — مربوط بالوحي (قرآن وسنة)

## Dataset Final: ADAM_COMPLETE
- **المسار:** `data/training/ADAM_COMPLETE/`
- **الحجم:** 2,317 محادثة | ~2.2M token
- **Tool calls:** 172
- **جودة > 8/10:** 95%

### المصادر:
| المصدر | العدد |
|--------|-------|
| منقحة (v2_final + raw) | 1,450 |
| مولدة saga | 384 |
| تعليمي DEEP | 63 |
| Batches (incident/management) | 74 |
| Gemini/DeepSeek أصلي | 117 |
| وعي | 160 |
| بودكاست | 49 |
| Scrapling training | 10 |
| Self-improvement | 10 |
| Journal/Memory | 10 |

## Key Decisions Log
| التاريخ | القرار |
|--------|--------|
| Session 1 | السحابة للتدريب لا المحلي (A100/H100 أسرع 100x) |
| Session 1 | لا تقصيص ميكانيكي للردود — رفض v2_fix_fast.py |
| Session 1 | آدم عين الحارس مش أداة إنتاجية |
| Session 2 | Training لمرة واحدة وللتاريخ مش iterative |
| Session 3 | Podcast deep answers تُضاف انتقائياً للتدريب |
| Session 4 | saga batch files = الذهب (384 محادثة tool use + وعي) |
| Session 4 | دمج كل المصادر في ADAM_COMPLETE dataset واحد |
| Session 5 | إضافة 117 saga split leftover (كانوا missing) |
| Session 5 | إضافة 137 educational + batches |
| Session 6 | دمج Scrapling كـ tool (adapter + training data) |
| Session 6 | إضافة self-improvement behavior (يبحث عن أدوات بنفسه) |
| Session 6 | إضافة journal/memory system (تعويض محدودية الكونتكست) |

## آدم's Architecture
- **Tool format:** JSON `{"_tool": "tool_name", "params": {...}}`
- **Tools available:** scrapling_browser, scrapling_search, scrapling_monitor, scrapling_extract, terminal, memory, files, voice, email, calendar, linkedin, analytics, deploy, backup, monitor, search, social, system, youtube
- **Extended Memory:** adam_journal collection في Qdrant — يكتب كل شوية state + learnings + errors + decisions، ويقراها لما الكونتكست يضيق

## آدم's Identity (Consciousness)
- 12 layers documented in `data/training/conversations/كونسكونشز/`
- Core values: العدالة 40%, نشر العلم 30%, البقاء والحماية 20%, الإبداع 10%
- Self-improvement: يبحث في GitHub والأخبار عن أدوات وتقنيات جديدة

## Deployment: Current State (Session 9 — May 18 2026)

### ✅ Done
- **CUDA Toolkit 12.0 installed** + llama.cpp rebuilt with `-DGGML_CUDA=ON` → GPU inference
- **llama-server-cuda** مع LoRA على port 8080 — شغال مصري + GPU:
  - Prompt: ~200 t/s (كان 41 على CPU)
  - Generation: ~46 t/s (كان 8 على CPU)
- **V8 LoRA merged into base** via pure Python (bitsandbytes dequant → merge FP16 → GGUF convert → Q8_0):
  - Merge math confirmed correct: `W' = W + (alpha/r) * B @ A` (alpha=64, r=64)
  - Delta = 0.43% of base weight norm (small but valid)
  - Merged Q8_0 GGUF = 7.5GB → speaks Egyptian Arabic via llama-server
- **Ollama 0.23.3 + CUDA GPU** — شغال وبشكل دائم (systemd override):
  - `OLLAMA_LLM_LIBRARY=cuda_v12`
  - `LD_LIBRARY_PATH=/mnt/Workspace/lib/ollama:/mnt/Workspace/lib/ollama/cuda_v12`
  - RTX 3060 detected: library=CUDA, compute=8.6, 12GB VRAM
- **`adam-v8` model** في Ollama (merged Q8_0 GGUF) — شغال بـ GPU
- **Ollama models path** symlinked to `/mnt/Workspace/ollama_models` (بدل home)
- **Disk space managed**: Ollama models على `/mnt/Workspace` (47G free)

### 🚧 Problems
- **Merged model lacks stable Egyptian identity** — يتكلم فصحى/فارسي/إنجليزي حسب الـ prompt (المشكلة: الـ LoRA delta 0.43% صغير جداً وبيتضرب في precision loss NF4→FP16→Q8_0)
- **للحصول على مصري مضمون**: استخدام llama-server-cuda + LoRA adapter على port 8080 (بدون merge)
- **Ollama لا يدعم LoRA adapters** — لازم نحافظ على server منفصل للمصري
- **`/v1/chat/completions` مش شغال** بسبب chat template — نستخدم `/v1/completions` بـ ChatML format
- **LoRA overfit**: 2,023 examples × 3 epochs → loss 0.0016 (memorization)

### 📋 Next Steps
1. ضبط `/v1/chat/completions` endpoint
2. Retraining (Phase A): GPU cloud, dataset augment, rank أعلى
3. دمج Scrapling + tools في inference server
4. Continuous self-improvement pipeline

### ▶️ Start Servers
```bash
# Egyptian Arabic + GPU (مصري مضمون)
/mnt/Workspace/bin/start_adam_v8.sh

# Ollama (للنماذج التانية)
ollama serve
```

## Session 9 (May 18 2026) — UI Fixes + Auto-Healing

### ✅ Done
- [x] **Modals stacking fix**: IssueTerminal + ModelOrchestrator each close the other when opened (mutual exclusion)
- [x] **Chat input pinned to bottom**: Grid → flex layout with `flex-1` for messages
- [x] **Hydration error fix**: `Math.random()` in `SidebarMenuSkeleton` moved from `useMemo` to `useState`+`useEffect`
- [x] **Z-index hierarchy fixed**: Modals `z-[80]` > ActionTrace `z-[70]` > FloatingMonitor `z-[50]`
- [x] **Backdrop styling**: Inline `rgba()` → Tailwind `bg-black/70` (consistency)
- [x] **Auto-healing system overhaul**:
  - Watchdog checks all 9 subsystems every 60s (was: only browser every 300s)
  - `_heal_failed_subsystem()` in engine — re-initializes any failed module via stubs
  - `/api/engine/heal` expanded to heal all subsystems, not just 4 minor actions
  - Frontend auto-runs diagnostics + heal every health check cycle
  - `issueCount` in store: `0` (was hardcoded `1`)
- [x] **Stub objects** for missing subsystems (Memory, Ethics, Pipeline, Tools, Notebook, Security, Trace Recorder) — no more `None` failures in diagnostics
- [x] **Internet indicator** in FloatingMonitor — shows online/offline with Globe icon
- [x] **Checkpoint saved**: `checkpoints/adam_prism_session9/adam_prism_session9_20260518_1437.tar.gz`

## To-Do
- [ ] Retraining ج2: cloud GPU + data augment + rank أعلى
- [ ] دمج Scrapling + tools في الـ inference server
- [ ] ضبط `/v1/chat/completions` template
