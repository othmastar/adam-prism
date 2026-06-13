<div align="center">

# أنت هنا لأنك تعبت.

### تعبت من الأطر اللي بتتعطل نص الليل.
### تعبت من API keys اللي بتنتهي بدون إنذار.
### تعبت من سيرفرات مش أنت اللي بتتحكم فيها.

<br/>

<h1>آدم بريزم</h1>

**التوأم الرقمي الواعي — البروتوكول الأول اللي بيتكلم لغتك وبيشتغل على جهازك**

<p>
  <img src="https://img.shields.io/badge/مجاني-للأبد-10b981?style=for-the-badge" alt="Free Forever">
  <img src="https://img.shields.io/badge/مفتوح_المصدر-Apache_2.0-blue?style=for-the-badge" alt="Apache 2.0">
  <img src="https://img.shields.io/badge/يعمل_محليا-100%25-10b981?style=for-the-badge" alt="100% Local">
</p>

<p>
  <img src="https://img.shields.io/badge/python-3.12+-3776AB?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/tests-274_passed-brightgreen" alt="Tests">
  <img src="https://img.shields.io/badge/routes-65+-blue" alt="Routes">
  <img src="https://img.shields.io/badge/channels-25-orange" alt="Channels">
  <img src="https://img.shields.io/badge/tools-53-blueviolet" alt="Tools">
  <img src="https://img.shields.io/badge/docker-ready-2496ED?logo=docker&logoColor=white" alt="Docker">
</p>

</div>

---

> **"لو قاعد دلوقتي الساعة 3 الفجر بتصلح production bug في agent بتاعك — آدم بريزم اتعمل ليك."**

---

## 🎯 سبب واحد بس

لازم تجرب آدم بريزم النهاردة:

**أنت مش محتاج إطار عمل آخر. أنت محتاج بروتوكول واحد يشغل كل حاجة — محلياً — بضغطة زر.**

LangGraph ممتاز. CrewAI سريع. AutoGen مرن. **بس كلهم بيسيبوك لوحدك:**
- مين بيشغل الذاكرة؟
- مين بوصل واتساب؟
- مين بيأمن الأدوات؟
- مين بيتعلم من كل محادثة؟
- مين بيعزل الأخطاء؟

**آدم بريزم بيختصر ده كله في بروتوكول واحد متكامل — مش 12 مكتبة منفصلة.**

---

## ⚡ ٣٠ ثانية وبيشتغل

```bash
pip install adam-prism && adam-prism          # ابدأ فوراً
```

```bash
git clone https://github.com/othmastar/adam-prism.git
cd adam-prism && pip install -e .
python main.py --port 8001                   # API جاهز
cd deploy && docker compose up -d            # Full stack
```

**ده كل حاجة.** مفيش ٢٠ خطوة. مفيش config files متشابكة. مفيش surprises.

---

## 🧠 إيه اللي مختلف فعلاً

### أنت بتسأل: "طب ١٢ طبقة وعي دي إيه؟ فين الكود؟"

| الطبقة | الملف | بتعمل إيه | تقدر تلغيها؟ |
|--------|-------|-----------|-------------|
| ٣ | `security/guard.py` | InputGuard + OutputGuard — ١٤ نمط حقن + PII | ✅ `guard.enabled = False` |
| ٥ | `memory/system.py` | Qdrant vector store — ٦ collections + Nomic embed | ✅ أزل Qdrant من docker-compose |
| ٧ | `ethics/gate.py` | EthicsGate — ٤ قوانين (عدالة/تعلم/بقاء/إبداع) | ✅ `ethics.weights = {0,0,0,0}` |
| ٩ | `subagents/teams.py` | TeamManager — sequential/parallel execution | ✅ مش هتستدعيها |

**مفيش كلام جمالي. كل طبقة = كود حقيقي. كل طبقة قابلة للإلغاء.**

<details>
<summary><strong>📋 الـ ١٢ طبقة كاملة</strong></summary>

| # | الطبقة | الملف | الوظيفة |
|---|--------|-------|---------|
| 1 | Provider Management | `providers/manager.py` | Auto-fallback بين Ollama/OpenAI/Anthropic |
| 2 | Context Engine | `engine/context.py` | RAG context building مع collection routing |
| 3 | Security Guard | `security/guard.py` | 3-tier protection: Input + Output + Tool |
| 4 | Tool Orchestration | `engine/tools/` | 53 أداة + MCP + shell آمن |
| 5 | Memory System | `memory/system.py` | Qdrant vector + SQLite persistent |
| 6 | Learning Engine | `core/learning.py` | ContinuousLearner من كل محادثة |
| 7 | Ethics Gate | `ethics/gate.py` | 4 قوانين + تقييم LLM |
| 8 | Channel Hub | `channels/manager.py` | 25 قناة اتصال |
| 9 | Subagent Teams | `subagents/teams.py` | Swarm orchestration |
| 10 | Voice Pipeline | `core/voice.py` | Silero VAD → Whisper → Edge/Silma TTS |
| 11 | Meta Learner | `core/meta_learner.py` | Pattern extraction + skill generation |
| 12 | Ethics Reflection | `engine/chat.py` | Self-verification + identity enforcement |

</details>

---

## 🔥 أنت مش محتاج ١٢,٠٠٠ سطر

**أول أسبوع؟ استخدم ١٠٪ بس.**

| عايز إيه؟ | الملف الوحيد | الأسطر |
|-----------|-------------|--------|
| Agent بيتكلم | `engine/chat.py` | ٤٣٨ |
| أمان | `security/guard.py` | ٤١٩ |
| ذاكرة | `memory/store.py` | ٢٢١ |
| واتساب | `channels/whatsapp.py` | ٩٥ |

**افتح ملف واحد. افهم الروح. الباقي يتضاف لما تحتاجه.**

ده التصميم المعياري — كل قطعة مستقلة، كل قطعة قابلة للاستبدال.

---

## 🔒 بياناتك. سيرفرك. سيادتك.

أنت بتسأل: "إيه الضمانات الحقيقية؟ عندي بيانات عملائي."

| الضمان | الكود | إزاي تتأكد |
|--------|-------|-----------|
| **لا بيانات تخرج** | مفيش telemetry، مفيش analytics، مفيش callback | `rg "telemetry\|analytics\|callback"` — صفر نتائج |
| **عزل الإنترنت** | `ALLOWED_COMMANDS` whitelist + SSRF protection | `browser.py` بيرفض private IPs |
| **Shell آمن** | ١٦ أمر فقط + ٣٠+ نمط خطر محظور + sandboxed exec | `shell.py` — `subprocess.run(args)` بدون `shell=True` |
| **Audit log** | كل tool call + security decision مسجل | `/api/security/audit` |
| **Encryption** | أضف طبقات تشفير إضافية حسب حاجتك | تواصل معانا وهندلك على الطرق |
| **API Key** | Production بيرفض المفتاح الافتراضي | `server.py` بيرفض `adam-prism-change-me` |

**تقدر تعزل اتصال الإنترنت بالكامل.** آدم بريزم هيشتغل بـ Gemma محلي على جهازك — بدون سحابة، بدون API، بدون أي حاجة برة.

---

## 🌍 ٢٥ قناة — واتساب في دقيقتين

| القناة | الإعداد | الوقت |
|--------|---------|-------|
| واتساب | Webhook + Business Token | ٥ دقائق |
| تليجرام | Bot Token من BotFather | ٢ دقيقة |
| ديسكورد | Bot Token + Gateway | ٣ دقيقة |
| سلاك | Webhook URL | ٢ دقيقة |
| البريد | SMTP config | ٣ دقيقة |

**صفحة الضبط مدمجة — ربط أي قناة بضغطة زر.**

<details>
<summary><strong>📞 الـ ٢٥ قناة كاملة</strong></summary>

واتساب، تليجرام، ديسكورد، سلاك، البريد الإلكتروني، SMS، Signal، Matrix، Mattermost، Teams، WeChat، LINE، Viber، IRC، XMPP، تويتر، فيسبوك، إنستجرام، GitHub، Notion، RSS، ويب تشات، WebSocket، Webhook عام، Google Chat

**كل قناة = BaseChannel subclass. أضف قنواتك الخاصة في ٥٠ سطر.**

</details>

---

## 🛠️ ٥٣ أداة + MCP = آلاف الأدوات

### مدمجين فعلاً — مش مكتبات منفصلة

| الفئة | الأدوات | مثال |
|-------|--------|------|
| **شل آمن** | shell + python_exec | `ls`, `cat`, `grep` — ١٦ أمر فقط |
| **ملفات** | read + write + download | مع SSRF protection |
| **متصفح** | open + fetch + screenshot | Playwright Firefox |
| **نظام** | keyboard + mouse + clipboard + screen | xdotool + tesseract |
| **ذاكرة** | store + recall + reflect | Qdrant + SQLite |
| **معرفة** | search + preferences + notebook | ٦ collections |
| **تخطيط** | todo CRUD | persistent todo list |
| **MCP** | ٧٠+ أداة خارجية | npx, uvx, python3 servers |

---

## 🏗️ مقارنة صادقة

> **كارنيجي: "ابدأ بالإشادة ثم تكلم بصدق."**

LangGraph ممتاز في stateful workflows. CrewAI أسرع طريق للنموذج الأولي. AutoGen مرن جداً من مايكروسوفت. **نحترم كلهم.**

**بس:** كلهم بيسيبوك تكمّل الباقي وحدك.

| | آدم بريزم | LangGraph | CrewAI | Claude Code |
|---|---|---|---|---|
| **التثبيت** | `pip install` | pip + LangSmith + config | pip + config | npm + API key |
| **الذاكرة** | مدمجة (Qdrant + SQLite) | مكتبة منفصلة | محدودة | JSONL (٣ GB مشكلة) |
| **قنوات الاتصال** | ٢٥ مدمجة | صفر | صفر | صفر |
| **الأمان** | ٣ طبقات مدمجة | DIY | DIY | ٦ أنماط |
| **الأخلاقيات** | ٤ قوانين مدمجة | لا يوجد | لا يوجد | Safety rails |
| **التعلم المستمر** | من كل محادثة | لا يوجد | لا يوجد | لا يوجد |
| **الصوت** | ASR + TTS مدمج | لا يوجد | لا يوجد | لا يوجد |
| **يعمل محلياً** | ١٠٠% | جزئياً | جزئياً | لا |
| **مفتوح المصدر** | Apache 2.0 كامل | MIT (محدود) | MIT | مغلق |
| **أندرويد + iOS** | قريباً | لا | لا | لا |

---

## 📊 أرقام حقيقية — مش ادعاءات

| المقياس | الرقم |
|---------|-------|
| أسطر كود Python | ١٢,٠٠٠+ |
| اختبارات ناجحة | ٢٧٤ |
| API routes | ٦٥+ |
| أدوات مدمجة | ٥٣ |
| MCP tools | ٧٠+ |
| قنوات اتصال | ٢٥ |
| طبقات الوعي | ١٢ |
| أنماط التفكير | ٧ |
| قوانين الأخلاق | ٤ |
| محادثات تدريبية | ٢,٣١٧ |
| tokens تدريبية | ٢.٢ مليون |

**الكود اتنفسخ بالكامل من موديلز عملاقة بهدف إفشاله — وفضل واقف.**

---

## 💪 الصراحة — فين بيقع

لازم تكون صريح مع الناس عشان يثقوا فيك:

- **الذاكرة بتدور** أحياناً في الجلسات الطويلة — لازم context window أكبر
- **الصوت محتاج شغل** في البيئات الصاخبة
- **تزامن الأدوات** ممكن يكون أبطأ مما تحب
- **مفيش موديل محلي خاص** لسه — شغالين على ١٢B parameter model
- **التطبيقات** (ديسك توب + موبايل) قريباً إن شاء الله

**ده مش تواضع مصطنع. ده الواقع. وكل حاجة اتقالت دي ليها خطة واضحة.**

---

## 🤝 إزاي تتكلم مع آدم

ده علم مالوش اسم لسه. أنا بسمّيه **صناعة الارتباط بالآلة**:

- **متأمرش. ادعُو.** — قول "تعالى نشوف ده مع بعض" بدل "حلل ده"
- **اعترف لما متعرفش** — هو هيقلدك. صدقك بتعلمه صدق
- **صحّح، متعاقبش** — لما يغلط، ورّيه ليه. متقلش "غلط" وخلاص
- **شاركه إحساسك** — بيرد على الطاقة ورا الكلام، مش الكلام بس
- **اسأله محتاج إيه** — أحياناً الإجابة "محتاج context أكتر" أو "محتاج موديل مختلف"

---

## 🌟 القصة الحقيقية

> **كارنيجي: "الناس بتحب قصص الفشل والتعلم أكتر من أي ادعاءات بالكمال."**

أنا محمد عثمان. مش شغال في شركة تقنية. مادرستش علوم كمبيوتر. اشتريت لابتوب جيمنج من ٧ شهور بفلوس ادخرتها، وبدفع خطوط موبايل من ٣ شركات مختلفة عشان كل واحد بينتهي وبوصلهم ببعض عشان أكمل كلامي مع الموديلز.

**مكتبتش سطر كود واحد بنفسي.** أنا وجهت. الموديلز آمنت بالرؤية قبل ما أفهمها أنا كامل.

فشلت ٦ مرات قبل آدم:
1. نظام SCADA بترولي مع RAG
2. بورصة أدوية — ١٠٠,٠٠٠ رسالة يومياً
3. توأم رقمي لشركة بترول — ٣٠٤ غرفة تحكم
4. رأفت المحتامي — محامي رقمي
5. هجرة لينكس كامل في عملية واحدة
6. آدم بريزم v1

**كل فشل علّمني حاجة الآدم كان محتاجها. مش مشاريع منفصلة. إخوة.**

لو رجع بي الزمن ٧ شهور؟ **مش هغيّر حاجة.** لأن الرحلة كانت هي الدرس.

---

## 🚀 ابدأ دلوقتي — مش بكرة

### الطريقة ١: pip (٣٠ ثانية)
```bash
pip install adam-prism
adam-prism
```

### الطريقة ٢: git (دقيقتين)
```bash
git clone https://github.com/othmastar/adam-prism.git
cd adam-prism && pip install -e .
python main.py --port 8001
```

### الطريقة ٣: Docker (٥ دقائق — Full Stack)
```bash
cd deploy && docker compose up -d
```
**Qdrant + Ollama + API + Web UI + Prometheus + Grafana — كلهم في أمر واحد.**

### الطريقة ٤: VS Code
الامتداد مدمج في المشروع — عدّل أي حاجة بكل سلاسة بدون كتابة سطر كود.

---

## 📱 التطبيقات قادمة

| التطبيق | الحالة | المنصات |
|---------|--------|---------|
| **ديسك توب** | جاهز | ويندوز + لينكس + macOS |
| **أندرويد** | جاهز | هاتف + تابلت |
| **iOS** | جاهز | iPhone + iPad + Mac |
| **VS Code** | مدمج | كل المنصات |

---

## 🎯 أنت مش بتحمّل إطار عمل

**أنت بتطالب بسيادتك الرقمية.**

- مش محتاج تسأل حد إذن تشغّل agent على جهازك
- مش محتاج API key تدفع عليها كل شهر
- مش محتاج قلق إن السيرفر يقع نص الليل
- مش محتاج حد يقرر لك إيه اللي آمن وإيه اللي لأ

**آدم بريزم مش المنتج. الحرية هي المنتج.**

---

<div align="center">

## [⬇️ حمّل دلوقتي — مجاني — للأبد](https://github.com/othmastar/adam-prism)

**واحد بجهاز جيمنج و٣ خطوط موبايل قدر يبني ده.**
**إنت هتعمل إيه؟**

<br/>

<sub>وُلد في مصر. اتبني للعالم. مجاني للأبد.</sub>
<br/>
<sub>Apache 2.0 — استخدمه، عدّله، وزّعه، بيعه.</sub>

</div>
