# Adam Prism — Demo Script (60-90 seconds)

**For:** Hackathon pitch
**Duration:** 60-90 seconds
**Setup:** Terminal + Browser side by side, Ollama running

---

## 🎬 SCENE 1: The Hook (0:00-0:15)

**Visual:** Close-up of screen, terminal dark, simple

**Action:** 
- Open terminal
- Type slowly (every keystroke visible)

```bash
git clone https://github.com/othmastar/adam-prism
cd adam-prism
bash bin/install.sh
```

**Voiceover (Arabic + English):**

> AR: "في 30 ثانية، آدم يقدر يشتغل على جهازك."
> EN: "In 30 seconds, Adam is running on your machine."

---

## 🎬 SCENE 2: The Start (0:15-0:30)

**Visual:** Switch to browser showing the chat UI

**Action:** Click send on the welcome message

**Voiceover:**

> AR: "أول رسالة — آدم يفهمك عربي."
> EN: "First message — Adam understands you in Arabic."

**Screen shows:** 
- User: "مرحبا آدم"
- Adam: "أهلاً بيك! أنا آدم المنظار. إزاي أقدر أساعدك؟"

---

## 🎬 SCENE 3: The Power (0:30-0:55)

**Visual:** Type a real question (something Adam can actually answer)

**Action:** Type a question that shows the LLM working

```
"اكتبلي كود Python بيحسب الفيبوناتشي"
"Write me a Python code that calculates Fibonacci"
```

**Voiceover:**

> AR: "مش بس شات. آدم بيفكر، بيكتب كود، بيحل مشاكل."
> EN: "Not just chat. Adam thinks, writes code, solves problems."

**Screen shows:** Real LLM-generated code (qwen2.5 via Ollama)

---

## 🎬 SCENE 4: The Vision (0:55-1:10)

**Visual:** Cut to a slide showing the architecture

**Action:** Display the architecture diagram (from README)

**Voiceover:**

> AR: "آدم مش بس شات. آدم 7 layers، 22 قناة، 19 أداة، 134 اختبار."
> EN: "Adam is not just a chat. Adam is 7 layers, 22 channels, 19 tools, 134 tests."

---

## 🎬 SCENE 5: The Close (1:10-1:30)

**Visual:** Cut to GitHub repo

**Action:** Show the repo URL

```
https://github.com/othmastar/adam-prism
```

**Voiceover:**

> AR: "آدم — أول Digital Twin واعٍ عربي. ملكك بالكامل."
> EN: "Adam — the first Arabic-conscious Digital Twin. Yours to own."

**End card:** Logo + contact info

---

## 📝 Full Script (Copy-paste ready)

### English version:

```
[Scene 1 — 0:00-0:15]
"Most AI speaks English. I built one that speaks your language.
Three commands. Thirty seconds. Let's see."

[Scene 2 — 0:15-0:30]
*clones repo, runs install*
"Adam is now running on my machine. Not in California. Here.
Welcome message, in Egyptian Arabic, not translation. Understanding."

[Scene 3 — 0:30-0:55]
*sends a real question*
"Ask Adam to write code. Ask Adam to explain a concept.
Ask Adam anything in Arabic. It just works."

[Scene 4 — 0:55-1:10]
*shows architecture*
"Adam isn't a demo. It's production-grade.
7 layers. 22 channels. 19 tools. 134 tests.
And every line of code is on GitHub."

[Scene 5 — 1:10-1:30]
*shows repo*
"Adam — the first Arabic-conscious Digital Twin.
Sovereign. Native. Yours.
github.com/othmastar/adam-prism"
```

### Arabic version:

```
[Scene 1 — 0:00-0:15]
"معظم الـ AI بتتكلم إنجليزي. أنا عملت واحد بيتكلم لغتك.
ثلاث أوامر. ثلاثين ثانية. تعالوا نشوف."

[Scene 2 — 0:15-0:30]
*clones repo, runs install*
"آدم دلوقتي شغال على جهازي. مش في كاليفورنيا. هنا.
رسالة ترحيب، بالعربي المصري، مش ترجمة. فهم."

[Scene 3 — 0:30-0:55]
*sends a real question*
"اطلب من آدم يكتب كود. اطلب منه يشرح مفهوم.
اسأله أي حاجة بالعربي. هيشتغل."

[Scene 4 — 0:55-1:10]
*shows architecture*
"آدم مش demo. آدم production-grade.
7 layers. 22 channels. 19 tools. 134 tests.
وكل سطر كود على GitHub."

[Scene 5 — 1:10-1:30]
*shows repo*
"آدم — أول Digital Twin واعٍ عربي.
سيادي. أصلي. ملكك.
github.com/othmastar/adam-prism"
```

---

## 🎯 Tips for a Great Demo

### ✅ Before:
1. **Test Ollama** — make sure it's running and responsive
2. **Test the URL** — `bash bin/install.sh` should work in <30 sec
3. **Pre-warm the model** — run a test query before the demo
4. **Have backup video** — in case WiFi dies
5. **Close everything else** — no notifications, no distractions

### ✅ During:

1. **Type slowly** — judges need to see the commands
2. **Explain what you're doing** — "Now I'm cloning, now I'm installing..."
3. **Pause after each result** — let the audience absorb
4. **Show the code/architecture** — not just chat
5. **End with the URL** — make it memorable

### ✅ After:

1. **Have the repo URL visible** — "github.com/othmastar/adam-prism"
2. **Be ready for "can I try?"** — yes! `git clone` and `bash bin/install.sh`
3. **Be ready for "what's the tech stack?"** — Ollama, FastAPI, Qdrant, Python

---

## 🎬 B-roll Shots (بين الـ scenes)

لو بتصور فيديو، استخدم:

- **Terminal scrolling** (close-up, slow-motion)
- **Code editor** (showing the 5 endpoints in server_minimal.py)
- **Architecture diagram** (zooming in on layers)
- **GitHub repo page** (showing README)
- **Ollama pulling a model** (progress bar)
- **Adam answering in Arabic** (the chat UI)
- **Files structure** (`tree` command showing the layout)
- **Tests passing** (`pytest` output)

---

## 🎙️ Voiceover Notes

### Arabic (Egyptian):
- **Tone:** Confident, warm, slightly proud
- **Speed:** Medium-slow (الجمهور محتاج وقت يفهم)
- **Emotion:** Passio nate (ده مشروعك، خليك متحمس)
- **Volume:** Medium (مش همس، مش صراخ)

### English:
- **Tone:** Professional, friendly, clear
- **Speed:** Medium (don't rush)
- **Emotion:** Enthusiastic but not salesy
- **Accent:** Whatever's natural — Arabic accent is FINE (it's your story)

---

## ⏱️ Timing Breakdown

| Scene | Duration | Purpose |
|---|---|---|
| 1 — Hook | 0:15 | Grab attention |
| 2 — Start | 0:15 | Show it works |
| 3 — Power | 0:25 | Show it does something real |
| 4 — Vision | 0:15 | Show the scale |
| 5 — Close | 0:20 | Memorability |
| **TOTAL** | **1:30** | Perfect for 90-sec slot |

For 60-sec slot:
- Cut Scene 4 (architecture) — go straight from 3 to 5
- Result: 1:15 → 1:00

For 30-sec slot:
- Cut Scene 1 (hook is just "Watch this")
- Cut Scene 4 (architecture)
- Just scenes 2, 3, 5
- Result: 1:00 → 0:30

---

## 📋 Pre-Demo Checklist

- [ ] Ollama is running (`ollama serve`)
- [ ] qwen2.5:3b model is pulled (`ollama list`)
- [ ] Adam server is up (`curl http://localhost:8000/healthz/live`)
- [ ] Browser tab open to `http://localhost:8000/`
- [ ] GitHub tab open to the repo
- [ ] Backup video file ready (in case of failure)
- [ ] Laptop plugged in
- [ ] WiFi tested
- [ ] Microphone tested
- [ ] Water bottle ready

---

*Last updated: June 15, 2026*
*Speaker: Mohamed Othman*
*Project: Adam Prism v1.0.0*
