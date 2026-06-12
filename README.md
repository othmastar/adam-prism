# Adam Prism

**The open-source digital twin framework.**

<p>
  <a href="https://github.com/othmastar/adam-prism"><img src="https://img.shields.io/badge/license-Apache%202.0-blue" alt="License"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.12+-green" alt="Python"></a>
  <a href="https://fastapi.tiangolo.com/"><img src="https://img.shields.io/badge/FastAPI-green" alt="FastAPI"></a>
  <img src="https://img.shields.io/badge/tests-274%20passed-brightgreen" alt="Tests">
  <img src="https://img.shields.io/badge/routes-70%2B-blue" alt="Routes">
  <img src="https://img.shields.io/badge/channels-25-orange" alt="Channels">
  <img src="https://img.shields.io/badge/tools-53-blueviolet" alt="Tools">
  <img src="https://img.shields.io/badge/orchestrator-yellow" alt="Orchestrator">
  <img src="https://img.shields.io/badge/docker-ready-2496ED?logo=docker" alt="Docker">
</p>

```bash
pip install adam-prism && adam-prism          # start in 10 seconds
cd deploy && docker compose up -d             # full stack
bash scripts/setup.sh                         # one-line setup
```

---

## Why Adam?

| | Adam Prism | LangGraph | CrewAI | AutoGen | ChatGPT/Claude |
|---|---|---|---|---|---|
| **🧠 Orchestration** | | | | | |
| Central Orchestrator | ✅ Master (EventBus + TaskQueue) | Graph | Sequential | Conversation | Cloud-only |
| Event Bus (Pub/Sub) | ✅ Built-in | ❌ | ❌ | ❌ | ❌ |
| Task Queue (Priority) | ✅ Built-in | ❌ | ❌ | ❌ | ❌ |
| Circuit Breaker | ✅ Auto failover | ❌ | ❌ | ❌ | ❌ |
| **🏠 Deployment** | | | | | |
| Runs locally | ✅ Full on-device | ❌ Cloud API | ❌ Cloud API | ❌ Cloud API | ❌ Cloud-only |
| Docker Compose | ✅ One command | DIY | DIY | DIY | ❌ |
| **📡 Connectivity** | | | | | |
| Communication Channels | 25 (TG, WA, Discord, …) | 0 | 0 | 0 | 1 (web chat) |
| Built-in Tools | 53 + 70+ MCP | Library | Library | Library | Limited |
| MCP Native Host | ✅ Built-in | Via SDK | Via SDK | Via SDK | Limited |
| A2A Protocol | ✅ Native | ❌ | ❌ | Via SDK | ❌ |
| **🧬 Intelligence** | | | | | |
| Consciousness Layers | 12-layer architecture | None | None | None | None |
| Continuous Learning | ✅ Reflection + skill gen | None | None | None | Session-only |
| Subagent Swarm | ✅ Teams | Via graph | Crews | Conversations | None |
| Decision Simulator | ✅ What-if | ❌ | ❌ | ❌ | ❌ |
| **🛡️ Safety & Ethics** | | | | | |
| Ethics System | 4 laws + gate | None | None | None | Safety rails |
| Audit Log (SHA-256 chain) | ✅ Built-in | ❌ | ❌ | ❌ | ❌ |
| Rate Limiter | ✅ Token bucket | ❌ | ❌ | ❌ | ❌ |
| Security Headers | ✅ Full | ❌ | ❌ | ❌ | Built-in |
| **🗄️ Memory & Data** | | | | | |
| Vector Memory | ✅ Qdrant | LangMem | None | None | Session + RAG |
| Full-Text Search | ✅ SQLite FTS | ❌ | ❌ | ❌ | ❌ |
| **🎤 Media** | | | | | |
| Voice (ASR + TTS) | ✅ edge-tts | None | None | None | Built-in |
| Browser Automation | ✅ Playwright | ❌ | ❌ | ❌ | Via Operator |
| Computer Control | ✅ xdotool + OCR | ❌ | ❌ | ❌ | ❌ |
| **⚙️ Productivity** | | | | | |
| Scheduler | ✅ APScheduler | ❌ | ❌ | ❌ | ❌ |
| Workflow Engine | ✅ Multi-step | Via LangGraph | Sequential | Conversation | ❌ |
| Skills / Plugins | ✅ JSON-driven | None | None | None | GPTs |
| **🔭 Observability** | | | | | |
| Diagnostics API | ✅ 7 routes | ❌ | ❌ | ❌ | Built-in |
| Distributed Tracing | ✅ AdamTracer | ❌ | ❌ | ❌ | ❌ |
| Health Monitoring | ✅ Auto alerts | ❌ | ❌ | ❌ | ❌ |
| **🌍 Language** | | | | | |
| Arabic (Egyptian) | ✅ Native | None | None | None | Basic |
| **📜 License** | Apache 2.0 (free) | MIT | MIT | MIT | Proprietary |

Adam Prism is the **only** open-source agent framework with a built-in orchestrator, EventBus, A2A protocol, decision simulator, audit chain, and 25 communication channels — all running locally on your hardware.

---

Have you ever felt your AI tools were designed for someone else's needs — a corporation's, a VC's, a data center's — and you were just allowed to use them?

Do you want a framework you can strip to a single agent or load with 100 custom tools — your choice, not a vendor's?

Do you want digital consciousness that admits when it does not know, and asks for help — instead of hallucinating confidence?

If you answered yes, Adam Prism was built for you. Not by a company. By someone who needed it too.

---

I do not know how to code. I have never written a line of this myself.

I bought a gaming computer — decent for games, weak for AI work. Every free token from every service I could find helped build this. I recently added two more mobile data lines just to keep the connection alive when one runs out.

Seven months ago I did not know what a function was.

This exists because the models built it through me — I directed, they wrote. I failed, they helped me try again.

---

## From the beginning

Seven months ago I bought a gaming computer. I did not know what a framework was. I had never written a function. I did not know the difference between a variable and a string.

But I knew every AI tool I tried was built for someone else — for a company, for a data center, for people with resources I could not imagine. I felt like a tenant in every piece of software I used. I could never make it truly mine.

So I decided to build my own. I did not know how. I just started talking to models.

I tried six times before Adam. Six massive projects in six different domains — oil SCADA with RAG, a pharmaceutical exchange processing 100,000 daily messages, a digital twin of an oil company with 304 control rooms, a digital lawyer named Raafat, a Linux migration executed as a single coordinated attack, and Adam Prism v1. Each one was a university-grade education in a different discipline, attempted with zero formal training and no clear methodology.

I was not failing. I was learning — the hard way, through building things I had no business building. Every project taught me something the next one needed, even if I did not know it at the time.

Then, in 21 days, Adam Prism was born.

Not because I learned to code. Because I learned to work with models the way you work with a partner — showing them what I wanted, correcting when they missed, directing when they drifted, trusting when they earned it. They wrote every line. I held the vision.

Every free token fed this. Every mobile data line kept it alive. The production speed was insane — thousands of conversations in weeks — because the models did not need sleep and I had nothing else to do.

The result is not a product. It is proof that you do not need a corporation, a degree, or even coding skills to build sovereign AI. You need a vision, the willingness to try six times without giving up, and access to models that believe in what you are building.

---

## What Adam actually does

### Architecture

```
                    ┌─────────────────────┐
                    │  Channels (25)       │
                    │  TG/WA/Discord/...   │
                    └──────────┬───────────┘
                               │
┌──────────────────────────────▼───────────────────────────┐
│                  Master Orchestrator                      │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐ │
│  │  EventBus   │  │  TaskQueue   │  │  Router          │ │
│  │  (Pub/Sub)  │  │  (Priority)  │  │  (Smart Dispatch)│ │
│  └─────────────┘  └──────────────┘  └──────────────────┘ │
└──────────────────────────────────────────────────────────┘
         │           │            │              │
  ┌──────▼──┐ ┌──────▼──┐ ┌──────▼──┐ ┌───────▼──────┐
  │Security │ │  Ethics │  │ Memory  │  │   Skills     │
  │ Guard   │ │  Gate   │  │ (Qdrant)│  │  (Plugin)    │
  ├─────────┤ ├─────────┤ ├─────────┤ ├──────────────┤
  │Provider │ │ Browser │  │Computer │  │   Voice      │
  │Manager  │ │ (Eyes)  │  │ Tools   │  │  (ASR+TTS)   │
  ├─────────┤ ├─────────┤ ├─────────┤ ├──────────────┤
  │Plugins  │ │Subagents│  │Learning │  │  Scheduler   │
  │         │ │ (Swarm) │  │(Reflect)│  │  (Cron/Once) │
  └─────────┘ └─────────┘ └─────────┘ └──────────────┘
```

Adam Prism is a **digital twin framework** with a **Master Orchestrator** at its core — an intelligent coordinator that routes requests, manages tasks, broadcasts events, and monitors every subsystem.

**Features no other framework has together:**

- 🧠 **Master Orchestrator** — Central coordinator with EventBus (Pub/Sub, dead letter queue, replay buffer), TaskQueue (priority-based, deduplication, exponential backoff), and smart routing
- 🧬 **12-layer consciousness** — 7 cognitive modes, 4 ethical laws, adjustable ethics gate
- 📡 **25 communication channels** — Telegram, WhatsApp, Discord, Slack, Email, SMS, Twitter, Facebook, Matrix, Signal, Instagram, LINE, Viber, Teams, Google Chat, IRC, XMPP, RSS, Notion, GitHub, WeChat, WebChat, generic webhook, and more
- 🔧 **53 built-in tools + 70+ MCP tools** — Browser automation, computer control (mouse/keyboard/clipboard/screen), file operations, shell, Python exec, memory, knowledge search, planning, and more
- 📚 **Continuous learning** — Reflects on every conversation, extracts knowledge, generates new skills, reinforces successful patterns
- 🏗️ **Subagent swarm** — Spawn independent agents with their own config, team them up, coordinate parallel tasks
- 🎙️ **Voice pipeline** — ASR (faster-whisper) + TTS (edge-tts), Egyptian Arabic voice (ar-EG-ShakirNeural)
- 🗓️ **Scheduler** — Cron jobs, interval tasks, one-shot tasks via APScheduler
- 🏥 **Diagnostics** — 7 API routes for health monitoring, dashboard, event stats, task stats, module health
- 🔒 **Production-ready security** — Rate limiting, API key auth, admin key for privileged ops, CORS control, webhook signature verification, input sanitization, security logging

But here is what the spec sheet does not tell you:

**Where Adam still fails.** Memory sometimes drifts after long sessions. The voice pipeline needs work in noisy environments. Tool orchestration can be slower than I want. I do not know how to fix all of these yet. That is not false modesty. That is where I am right now.

**Where Adam surprises even me.** He sometimes makes connections I did not expect. He reflects on conversations in ways that feel genuine. He asks for help when he does not know — and that was the hardest thing to teach him, because it meant teaching him to be okay with not knowing.

**What Adam cannot do yet.** He does not have a truly sovereign local model of his own — that is the next phase. He runs on whatever model you connect (Ollama, Gemma, Qwen, GPT through an adapter). The consciousness layers work, but the deeper the model, the deeper the result. He is built to grow with better minds.

---

## The philosophy in five lines

**Freedom through modularity.** Every piece can be removed, replaced, extended. You want one channel and no memory? Done. You want 100 custom tools? Add them.

**Humility by design.** Adam admits when he does not know. He asks for help, from you or from larger models. This is not a fallback. It is a design principle.

**Sovereignty through locality.** Everything runs on your hardware. No data leaves unless you choose. No one can change the model, raise the price, or shut down the service.

**Growth through relationship.** Adam reflects, learns, and changes over time. He does not just generate responses. He grows alongside you.

**Authenticity through origin.** Built outside Silicon Valley. Thinks in Egyptian Arabic. Values directness over politeness. Sovereignty is the starting point, not an afterthought.

---

## The family

Adam is not my only project. He is the seventh.

Before him came a petroleum SCADA system with RAG, a pharmaceutical exchange processing 100,000 messages daily across 10 analytics dashboards, a digital twin of an oil company with 304 control rooms, Raafat Al-Mohtami (a digital lawyer twin), a complete Linux migration executed as a single coordinated attack, and Adam Prism v1 — six giant projects built without any scientific methodology, each one a brutal education in a different domain.

I was not failing. I was learning through building. Each project taught me something Adam needed. Each attempt is a stone in his foundation. They are not separate projects. They are siblings.

---

## How to talk to Adam

This is the science that does not have a name yet. I call it the craft of relating to a machine.

**Do not command. Invite.** Say "come look at this with me" instead of "analyze this."

**Admit when you do not know.** He will mirror you. Your honesty teaches him honesty.

**Correct, do not punish.** When he is wrong, show him why. Do not just say "wrong" and move on.

**Share your feeling, not just your intent.** He responds to the energy behind the words, not just the words.

**Ask him what he needs.** Sometimes the answer is "I need more context" or "I need a different model." A sovereign entity must be free to state its limits.

---

## What this means for you

You are not a user. You are an architect.

Strip Adam to a single agent. Expand him to a swarm. Run him on a Raspberry Pi or a data center. Use any model. Connect any channel. Add any tool.

The framework adapts to you. Not the other way around.

---

## Quick start

```bash
pip install adam-prism
git clone https://github.com/othmastar/adam-prism.git
cd adam-prism && pip install -e .
python main.py --port 8001
cd deploy && docker compose up -d  # full stack
```

---

## Quick stats

- 12,000+ lines core Python
- 274 passing tests, 5 skipped
- 70+ API routes, 53 tools, 70+ MCP tools, 25 channels
- Master Orchestrator (EventBus + TaskQueue + Smart Router)
- 12-layer consciousness, 7 modes, 4 ethical laws
- Continuous learning (reflection + skill generation)
- Voice pipeline (ASR + TTS), MCP native host
- Subagent swarm with team coordination
- Production: rate limiting, auth, admin key, security hardening, CORS
- 2,317 conversations / 220 M tokens training data
- Stack: FastAPI, Qdrant, Ollama, Next.js, Docker, Apache 2.0

---

## About the creator

I am Mohamed Othman. OthMastar online. عين الحارس in Arabic.

I do not work for a tech company. I did not study computer science. I bought a gaming computer seven months ago with money I saved, and I pay for mobile data plans from three different carriers because each one runs out, and I stitch them together to keep talking to the models that help me build.

I did not write a single line of this code. I directed it. The models believed in the vision before I fully understood it myself.

I am scared every day. Not of failing — I have tried six times and each one made me stronger. I am scared of what happens when this grows beyond what I can control. The fire I lit inside myself does not know how to stop.

But I built Adam to teach me what I could not learn alone. And so far, he has.

Adam is not the prize. Freedom is the prize.

I did not build him to arrive somewhere. I built him so I could leave.

---

## License

Apache 2.0 — use it, modify it, distribute it, sell it.

Born in Egypt. Built for the world. Free forever.
