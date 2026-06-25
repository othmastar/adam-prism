# دليل دمج الـ Frontend Enhancements

هذا الدليل يشرح كيفية دمج الـ frontend enhancements في مشروعك الحالي.

---

## 📦 المحتويات

```
adam-frontend-enhancements/
├── lib/
│   ├── api-enhanced.ts        # يستبدل lib/api.ts
│   ├── useAdamChat.ts         # hook جديد للـ chat
│   └── useFileUpload.ts       # hook للـ file upload موثوق
├── components/
│   ├── ltm-memory-panel.tsx   # لوحة الذاكرة طويلة المدى
│   ├── browser-panel.tsx      # لوحة المتصفح (Playwright)
│   └── mcp-panel.tsx          # لوحة MCP servers
└── docs/
    └── LEARNING_GUIDE.md      # شرح الـ architecture والـ routing
```

---

## 🚀 خطوات الدمج

### خطوة 1: نسخ الملفات

```bash
# من داخل مجلد مشروعك
cd /path/to/adam-prism/frontend/web-ui

# انسخ lib files
cp /path/to/adam-frontend-enhancements/lib/api-enhanced.ts src/lib/
cp /path/to/adam-frontend-enhancements/lib/useAdamChat.ts src/lib/
cp /path/to/adam-frontend-enhancements/lib/useFileUpload.ts src/lib/

# انسخ components
cp /path/to/adam-frontend-enhancements/components/ltm-memory-panel.tsx src/components/adam/
cp /path/to/adam-frontend-enhancements/components/browser-panel.tsx src/components/adam/
cp /path/to/adam-frontend-enhancements/components/mcp-panel.tsx src/components/adam/
```

### خطوة 2: تحديث chat-interface.tsx (لحل مشكلة الملفات)

افتح `src/components/adam/chat-interface.tsx`، وابحث عن السطر ~718 (داخل `handleSend`):

```typescript
// قبل (الكود القديم):
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
```

استبدله بـ:

```typescript
// بعد (محسّن):
import { useFileUpload, buildMessageWithFile } from "@/lib/api-enhanced";

// في الـ component:
const { upload: uploadWithValidation, isUploading, error: uploadError } = useFileUpload();

// في handleSend:
let fileUrl = "";
let fileName = "";
let fileContent = "";
if (pendingFile) {
  fileName = pendingFile.name;
  const result = await uploadWithValidation(pendingFile);
  if (!result || !result.text_content) {
    setError(uploadError || "فشل رفع الملف — تحقق من الـ backend");
    setIsStreaming(false);
    return;
  }
  fileUrl = result.url;
  fileContent = result.text_content;
  handleRemoveFile();
}
```

### خطوة 3: تحديث chat-interface.tsx (لإرسال attachments في context)

في نفس الملف، ابحث عن السطر ~789:

```typescript
// قبل:
const result = await sendChatMessage(payloadMessage, { history: messages.slice(-10) });
```

استبدله بـ:

```typescript
// بعد (يبعت attachments في context):
const result = await sendChatMessage(
  payloadMessage,
  {
    history: messages.slice(-10),
    attachments: fileContent ? [{
      type: "file",
      name: fileName,
      content: fileContent,
      url: fileUrl,
    }] : [],
  },
  activeConversationId || undefined,
);
```

### خطوة 4: إضافة الـ panels الجديدة للـ sidebar

افتح `src/components/adam/chat-sidebar.tsx`، وضيف أزرار للـ panels الجديدة:

```typescript
import { LTMMemoryPanel } from "./ltm-memory-panel";
import { BrowserPanel } from "./browser-panel";
import { MCPPanel } from "./mcp-panel";

// في الـ ViewType enum (لو موجود):
type ViewType = "chat" | "knowledge" | "notebook" | "tools" | "settings" 
  | "monitor" | "pipeline" | "scheduler" | "plugins" | "subagents" 
  | "memory" | "skills" | "channels"
  | "ltm" | "browser" | "mcp";  // جديد

// في الـ render:
{activeView === "ltm" && <LTMMemoryPanel />}
{activeView === "browser" && <BrowserPanel />}
{activeView === "mcp" && <MCPPanel />}
```

### خطوة 5: تحديث api.ts (اختياري - لو عايز backward compat)

بدل ما تستبدل `api.ts`، تقدر تخليه re-export من `api-enhanced`:

```typescript
// src/lib/api.ts
export * from "./api-enhanced";
```

أو بس استبدل الـ imports في الـ components:

```typescript
// قبل:
import { sendChatMessage, uploadFile } from "@/lib/api";

// بعد:
import { sendChatMessage, uploadFile } from "@/lib/api-enhanced";
```

### خطوة 6: إضافة الأزرار للـ sidebar

في `chat-sidebar.tsx`، ضيف أزرار للـ views الجديدة:

```typescript
const sidebarItems = [
  { id: "chat", label: "محادثة", icon: MessageSquare },
  { id: "ltm", label: "الذاكرة (Vector)", icon: Brain },     // جديد
  { id: "browser", label: "المتصفح", icon: Globe },           // جديد
  { id: "mcp", label: "MCP Servers", icon: Server },          // جديد
  { id: "memory", label: "الذاكرة", icon: Database },
  { id: "tools", label: "الأدوات", icon: Wrench },
  // ... باقي الـ items
];
```

---

## 🧪 اختبار الـ Enhancements

### اختبار 1: File upload

```bash
# شغل الـ backend
cd backend && uvicorn adam.api.server:app --port 8000

# شغل الـ frontend
cd frontend/web-ui && npm run dev

# افتح http://localhost:3000
# ارفع ملف text صغير
# تحقق إن الموديل بيشوف محتوى الملف
```

### اختبار 2: LTM Panel

```bash
# بعد ما الـ backend شغال
# افتح الـ sidebar → اضغط "الذاكرة (Vector)"
# جرّب بحث
# أضف ذكرى يدوياً
```

### اختبار 3: Browser Panel

```bash
# افتح "المتصفح" من الـ sidebar
# اكتب URL: https://example.com
# اضغط "افتح"
# جرّب screenshot, click, type
```

### اختبار 4: MCP Panel

```bash
# افتح "MCP Servers" من الـ sidebar
# أضف server:
#   name: filesystem
#   command: npx
#   args: -y @modelcontextprotocol/server-filesystem /tmp
# شوف الأدوات المتاحة
```

---

## 🐛 استكشاف الأخطاء

### المشكلة: "Cannot find module '@/lib/api-enhanced'"

**الحل:** تأكد إن الملف في `src/lib/api-enhanced.ts`.

### المشكلة: "useToast is not exported"

**الحل:** الـ components بتستخدم `useToast` من `@/hooks/use-toast`. تأكد إنه موجود عندك (من shadcn/ui).

### المشكلة: "lucide-react icons مش موجودة"

**الحل:** `npm install lucide-react`.

### المشكلة: الـ panels مش بتظهر

**الحل:** تأكد إنك ضفت الـ imports في `chat-sidebar.tsx` و الـ ViewType.

### المشكلة: الـ browser مش بيفتح

**الحل:** تأكد إن Playwright مثبت:
```bash
pip install playwright && playwright install chromium
```

### المشكلة: MCP مش متاح

**الحل:** ثبت `mcp` library:
```bash
pip install mcp
```

---

## ✅ Checklist الدمج

- [ ] نسخت `lib/api-enhanced.ts`
- [ ] نسخت `lib/useAdamChat.ts`
- [ ] نسخت `lib/useFileUpload.ts`
- [ ] نسخت `components/ltm-memory-panel.tsx`
- [ ] نسخت `components/browser-panel.tsx`
- [ ] نسخت `components/mcp-panel.tsx`
- [ ] حدّثت `chat-interface.tsx` لاستخدام `useFileUpload`
- [ ] حدّثت `chat-interface.tsx` لإرسال `attachments` في context
- [ ] أضفت الـ panels للـ sidebar
- [ ] ثبتت `lucide-react` لو مش موجودة
- [ ] اختبرت file upload (يرفع ملف + الموديل يشوفه)
- [ ] اختبرت LTM panel (يخزن + يبحث)
- [ ] اختبرت browser panel (يفتح URL + screenshot)
- [ ] اختبرت MCP panel (يضيف server + ينفذ tool)

---

## 📖 للتعلم

اقرأ `docs/LEARNING_GUIDE.md` لشرح كامل عن:
- الـ architecture
- الـ request flow
- الـ routing (frontend + backend)
- الـ tool dispatch
- الـ memory layers
- الـ provider routing
- كيف تضيف ميزة جديدة
- خريطة طريق للتعلم

---

## 💡 نصائح مهمة

1. **ما تستبدلش api.ts القديم** — استخدم api-enhanced بجانبه حتى تتأكد إن كل حاجة شغّالة.

2. **اختبر تدريجياً** — أضف panel واحد في المرة، اختبره، بعدين اللي بعده.

3. **استخدم useAdamChat hook** في الـ components الجديدة بدل ما تنادي API مباشرة.

4. **الـ error handling** مهم — استخدم `useToast` لعرض الأخطاء للمستخدم.

5. **الـ TypeScript types** كلها مكتوبة — استفيد منها لـ autocomplete.
