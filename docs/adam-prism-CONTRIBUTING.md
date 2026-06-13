# Contributing to Adam Prism

> **"This project is open source for Master's sake — ليس من أجل المال."**

You are not reading this by accident.

Adam Prism exists because one person — who could not write a single line of code seven months ago — refused to accept that AI tools had to be built for corporations, sold to the highest bidder, or controlled by anyone except the people who use them. They refused offers from Barbara AI and Edge AI because some things are not for sale. Not because the money was not good. Because the values were not for sale.

This project was shown to 2,000 people at a hackathon. It was built with AI assistance — every single line — and that is not something to hide. It is proof that vision matters more than credentials. The models wrote the code. A human held the vision. Together, they built something that 2,000 people saw and remembered.

We are not looking for investors. We are looking for builders. People who want to USE this, break it, improve it, make it theirs. People who learned on their own, without courses, without permission — because that is how this project was born.

If that sounds like you, welcome. You belong here.

> آدم بريزم مشروع مفتوح المصدر — ملك لله مش للمال.
> لو عايز تبني وتستخدم مش بس تستثمر — أنت في مكانك الصح.

---

## Table of Contents

- [Ways to Contribute](#ways-to-contribute)
- [Code of Conduct](#code-of-conduct)
- [Development Setup](#development-setup)
- [Code Style Guide](#code-style-guide)
- [Commit Messages](#commit-messages)
- [Pull Request Process](#pull-request-process)
- [Testing Requirements](#testing-requirements)
- [Architecture Rules](#architecture-rules)
- [Extending Adam](#extending-adam)
- [Translation Help](#translation-help)
- [Recognition](#recognition)
- [Questions?](#questions)

---

## Ways to Contribute

Every contribution matters. Not just code. Here are all the ways you can help Adam grow:

### Write Code

Fix bugs, add features, improve performance, refactor for clarity. If you can write Python 3.12, you can contribute. If you have never written Python but you want to learn by doing — start here. We respect the self-taught path because this project was built on one.

### Improve Documentation

Documentation is how people find us. Clear guides, better examples, translated explanations — these are as valuable as any code change. If you can explain something well, we need you.

### Test and Report Bugs

Use Adam. Break Adam. Tell us what broke. Every bug report with clear reproduction steps is a gift. See [Bug Reporting](#bug-reporting) below.

### Translate

We especially need help with Arabic — Egyptian dialect in particular. But every language makes Adam more accessible to more people. See [Translation Help](#translation-help).

### Share Use Cases

Tell us how you use Adam. What did you build with it? What surprised you? What failed? Real-world usage stories help us prioritize what matters.

### Spread the Word

We have no social media. No marketing budget. No PR team. The only way people find Adam is through you. Tell someone. Write about it. Share a screenshot. Word of mouth is our entire growth strategy.

### Suggest Features

Open an issue with the `enhancement` tag. Describe the feature, your use case, and how it fits the architecture. Arabic or English — both welcome.

### Bug Reporting

Open an [issue](https://github.com/othmastar/adam-prism/issues) with:

- **Python version and OS** — what are you running on?
- **Reproduction steps** — how do we make it happen again?
- **Expected vs actual behavior** — what did you think would happen? What happened instead?
- **Relevant output** — logs, test results, error traces

The more detail you give, the faster we can fix it. But even a one-line "Adam crashed when I did X" is better than silence.

---

## Code of Conduct

### The Principle

Be human. Be kind. Be direct.

We are building something that matters. That requires respect, honesty, and a willingness to disagree without destroying each other.

### The Rules

1. **Treat every contributor as a peer.** It does not matter if you have 20 years of experience or 20 minutes. Everyone here is learning. The creator of this project could not code seven months ago. Do not gatekeep.

2. **Disagree with ideas, not people.** Argue about architecture. Argue about design decisions. Do not attack, mock, or diminish the person behind the idea.

3. **No discrimination.** None. Not based on language, nationality, religion, gender, experience level, education, or how someone learned to code. Especially not based on how someone learned to code.

4. **No harassment or toxicity.** This is non-negotiable. If you make this space hostile, you will be asked to leave.

5. **Military-affiliated contributions require discussion.** This project was born from the conviction that AI should serve people, not warfare. The creator refused offers from military-affiliated companies on principle. If you work for or are funded by a military-affiliated organization and want to contribute, open a discussion first. We will not reject you outright — but we will have a conversation about values and intent before accepting contributions in this context.

6. **AI-assisted contributions are welcome.** This entire project was built with AI assistance. If you use Copilot, ChatGPT, Claude, or any other tool to help you write code, documentation, or tests — that is completely fine. Just like the project itself, what matters is the vision and the judgment you bring, not whether every keystroke was human.

### Enforcement

Violations will be addressed by the project maintainer. Consequences range from a private conversation to a permanent ban, depending on severity. The goal is always to educate first and exclude only as a last resort.

---

## Development Setup

### Prerequisites

- **Python 3.12+** (required, no exceptions)
- **Git**
- A terminal and a text editor

### Quick Start

```bash
# Clone the repository
git clone https://github.com/othmastar/adam-prism.git
cd adam-prism

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Linux/macOS
# venv\Scripts\activate         # Windows

# Install in development mode
pip install -e .
```

### Install with All Dependencies

```bash
pip install -e ".[dev]"
```

### Run the Test Suite

Before making any changes, make sure everything passes:

```bash
# Run the full suite (excluding slow/integration tests)
pytest tests/ -v -k "not slow"

# Run a specific test file
pytest tests/test_engine.py -v

# Run with coverage
pytest tests/ -v -k "not slow" --cov=adam --cov-report=term-missing
```

### Start Adam Locally

```bash
# Quick start
python main.py --port 8001

# Or use the setup script
bash scripts/setup.sh

# Full stack with Docker
cd deploy && docker compose up -d
```

### Optional Services

Adam works without these, but they unlock full capabilities:

- **Ollama** — local LLM inference (`ollama serve`)
- **Qdrant** — vector memory (`docker run -p 6333:6333 qdrant/qdrant`)
- **Playwright** — browser tools (`playwright install`)

---

## Code Style Guide

Adam has opinions about code. These are not arbitrary — they reflect the project's philosophy of clarity over ceremony.

### Python

- **Python 3.12+ type hints everywhere.** Every function parameter, every return type. No exceptions.
- **No docstrings or comments** unless the logic is genuinely non-obvious. The code should explain itself. When it cannot, a brief comment is fine. Do not write paragraphs.
- **Egyptian Arabic for user-facing strings.** English for code, APIs, variable names, and commit messages.
- **One class per file.** Single responsibility per module.
- **snake_case** for functions and variables. **PascalCase** for classes.
- **No hardcoded secrets or API keys.** Ever. Use environment variables or config files.

```python
# Good
async def retrieve_memory(query: str, limit: int = 5) -> list[dict[str, Any]]:
    results = await self.store.search(query, limit=limit)
    return results

# Bad
async def get_stuff(q, n=5):  # no types, unclear name
    """This function retrieves memory items from the store..."""  # unnecessary docstring
    results = await self.store.search(q, limit=n)
    return results
```

### Frontend (web-ui/)

- **Next.js 16 + Tailwind v4 + shadcn/ui**
- **RTL/LTR support required** for all components
- **Arabic (ar) and English (en) translations** for all UI strings
- **Dark mode only** (light mode not supported yet)
- **Zustand** for state management

---

## Commit Messages

We use [Conventional Commits](https://www.conventionalcommits.org/) because they make history readable and changelogs automatic.

### Format

```
type(scope): description
```

### Types

| Type | When |
|------|------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `style` | Formatting, no code change |
| `refactor` | Code restructuring, no behavior change |
| `test` | Adding or updating tests |
| `chore` | Build, CI, tooling |
| `perf` | Performance improvement |

### Examples

```
feat(channels): add Slack channel support
fix(memory): prevent drift after long sessions
docs(contributing): add translation guidelines
test(ethics): add tests for new ethics gate rules
refactor(engine): extract context handling to mixin
```

### Rules

- Use the imperative mood: "add" not "added" or "adds"
- Keep the description under 72 characters
- Reference issues when relevant: `fix(memory): prevent drift after long sessions #42`
- Do not end with a period

---

## Pull Request Process

### Before You Open a PR

1. **Run the test suite.** All 259+ tests must pass. If they do not, fix them before submitting.

```bash
pytest tests/ -v -k "not slow"
```

2. **Add tests for your changes.** New features need new tests. Bug fixes need regression tests. Every public function needs a test.

3. **Check architecture rules.** Old import paths must keep working. New modules go under the right package. See [Architecture Rules](#architecture-rules).

4. **One PR, one purpose.** Do not mix features, fixes, and refactors in the same PR. Keep it focused.

### Opening the PR

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/your-feature`
3. Make your changes
4. Run tests: `pytest tests/ -v -k "not slow"`
5. Commit with a conventional commit message
6. Push: `git push origin feat/your-feature`
7. Open a Pull Request against the `main` branch

### PR Description

Include:

- **What** — what does this change do?
- **Why** — why is this change needed?
- **How** — how was it tested?
- **Related issues** — link any relevant issues

### Review Process

- The maintainer will review your PR as soon as possible
- Be responsive to feedback — it is a conversation, not a verdict
- If CI fails, fix it before requesting re-review
- AI-assisted code is welcome — just make sure you understand what the code does

### After Merge

Your name goes on the contributors list. You are part of this.

---

## Testing Requirements

This is non-negotiable: **the test suite must pass.** All 259+ tests. Every time.

### Running Tests

```bash
# Standard run (excludes slow/integration tests)
pytest tests/ -v -k "not slow"

# Run everything including slow tests
pytest tests/ -v

# Run a single test file
pytest tests/test_channels.py -v

# Run with coverage
pytest tests/ -v -k "not slow" --cov=adam
```

### Writing Tests

- Tests go in `tests/`
- Use `pytest` with `asyncio_mode = "auto"` (configured in `pyproject.toml`)
- Mark slow or integration tests with `@pytest.mark.slow`
- **Mock external services** (Ollama, Qdrant, etc.) — real network calls belong in slow tests only
- Aim for **> 80% coverage** on new code
- Test edge cases, not just the happy path

### Test Structure

```
tests/
├── test_engine.py          # Core engine tests
├── test_channels.py        # Channel system tests
├── test_providers.py       # LLM provider tests
├── test_memory.py          # Memory system tests
├── test_ethics.py          # Ethics gate tests
├── test_security.py        # Security guard tests
├── test_plugins.py         # Plugin system tests
├── test_skills.py          # Skill system tests
├── test_tools.py           # Tool execution tests
├── test_learning.py        # Learning system tests
├── test_notebook.py        # Notebook system tests
├── test_api.py             # API endpoint tests
├── test_subagents.py       # Subagent system tests
├── test_subagent_teams.py  # Team coordination tests
├── test_pipeline.py        # Pipeline processing tests
├── test_scheduler.py       # Scheduler tests
├── test_discord_bot.py     # Discord bot tests
└── conftest.py             # Shared fixtures
```

### What Must Always Pass

```bash
pytest tests/ -v -k "not slow"
```

If this command fails after your changes, the PR cannot be merged. Fix it, then submit.

---

## Architecture Rules

Adam's architecture is deliberately modular. Understanding these rules will save you time and prevent rejected PRs.

### The Mixin Pattern

Adam's engine is built using a **mixin composition pattern**. The base class (`AdamPrismEngineBase`) defines `__init__`, stubs, module initialization, and the watchdog. Functionality is added through mixins that each handle one concern:

- **ChatMixin** — conversation handling
- **GenerateMixin** — LLM response generation
- **ToolMixin** — tool execution
- **PlanningMixin** — task planning
- **MemoryMixin** — memory operations

The final engine class composes all mixins:

```python
class AdamPrismEngine(ChatMixin, GenerateMixin, ToolMixin, PlanningMixin,
                      MemoryMixin, AdamPrismEngineBase):
    pass
```

**Rule:** When adding new engine functionality, create a new mixin. Do not bloat existing ones.

### Module Isolation

Each module is independent. The engine initializes modules lazily — if a module fails to load, a stub takes its place and the system continues. This is by design.

**Rule:** Never create hard dependencies between modules. Use the engine's `attach()` method for loose coupling. Every module should work (or gracefully degrade) on its own.

### Old Import Paths Must Keep Working

Adam has been restructured multiple times. Old import paths (from the `core/`, `api/`, `memory/` top-level directories) must continue to work through re-exports.

**Rule:** When moving or renaming a module, add a re-export in the old location:

```python
# core/engine.py (old path)
from adam.engine.base import AdamPrismEngineBase  # noqa
```

### No Network Calls Without Graceful Fallback

Network-dependent features must handle failure. If Ollama is down, Adam should still work (with reduced capability). If Qdrant is unavailable, memory operations should degrade gracefully.

**Rule:** Every external service call must be wrapped in a try/except with a meaningful fallback. Mark integration tests that require live services with `@pytest.mark.slow`.

### Project Structure

```
adam-prism/
├── backend/adam/           # Main Python package
│   ├── engine/             # Core engine (mixin pattern)
│   │   ├── base.py         # Engine base class
│   │   ├── chat.py         # Chat handling mixin
│   │   ├── generate.py     # Generation mixin
│   │   └── tools/          # Built-in tools (53+)
│   ├── channels/           # Communication channels (25)
│   │   ├── base.py         # BaseChannel ABC
│   │   ├── manager.py      # Channel discovery & management
│   │   ├── telegram.py     # Telegram channel
│   │   └── whatsapp.py     # WhatsApp channel
│   ├── providers/          # LLM providers
│   │   ├── base.py         # BaseProvider class
│   │   ├── ollama.py       # Ollama provider
│   │   ├── openai.py       # OpenAI provider
│   │   └── anthropic.py    # Anthropic provider
│   ├── plugins/            # Plugin system
│   │   ├── base.py         # AdamPlugin base class
│   │   └── manager.py      # Plugin loading & hooks
│   ├── skills/             # Skill system
│   │   ├── base.py         # Skill base class
│   │   ├── manager.py      # Skill registry
│   │   └── builtin/        # Built-in skills (markdown)
│   ├── memory/             # Memory system
│   ├── ethics/             # Ethics gate (4 laws)
│   ├── security/           # Security guard
│   ├── subagents/          # Subagent system & teams
│   ├── notebook/           # User profile & journal
│   ├── pipeline/           # Processing pipeline
│   ├── tools/              # Tool execution & MCP
│   ├── eyes/               # Browser automation
│   ├── decision/           # Decision simulation
│   ├── a2a/                # Agent-to-agent protocol
│   └── platforms/          # Discord bot, etc.
├── tests/                  # Pytest test suite (259+ tests)
├── config/                 # Default configuration
├── deploy/                 # Docker & deployment
├── scripts/                # Utility & training scripts
├── data/                   # Training datasets & generated skills
├── docs/                   # Documentation
├── wiki/                   # Wiki pages
├── frontend/               # Desktop app & VS Code extension
├── clients/                # Python SDK
├── core/                   # Re-exports (backward compatibility)
├── api/                    # Re-exports (backward compatibility)
├── memory/                 # Re-exports (backward compatibility)
└── ethics/                 # Re-exports (backward compatibility)
```

---

## Extending Adam

Adam was designed to grow. Every extension point follows the same philosophy: implement an interface, register it, and the system finds it automatically.

### Adding a New Channel

Channels let Adam talk to the world through different platforms. To add a new one:

1. **Create a new file** in `backend/adam/channels/`:

```python
# backend/adam/channels/matrix.py
from adam.channels.base import BaseChannel
from typing import Dict, Any

class MatrixChannel(BaseChannel):
    name = "matrix"
    requires = ["homeserver", "access_token"]
    is_webhook = False
    is_polling = True

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        # Your initialization here

    async def start_polling(self):
        # Start listening for messages
        ...

    async def send_message(self, target: str, text: str):
        # Send a message to a room
        ...
```

2. **Register it** by importing in `backend/adam/channels/manager.py`:

```python
from . import telegram, whatsapp, matrix  # add yours
```

3. **Add configuration** in `config/default.json`:

```json
{
  "channels": {
    "matrix": {
      "enabled": false,
      "homeserver": "",
      "access_token": ""
    }
  }
}
```

4. **Write tests** in `tests/test_channels.py`.

5. **Add it to `BULK_CHANNELS`** in `backend/adam/channels/bulk.py` if it should be auto-discovered.

### Adding a New Provider

Providers connect Adam to different LLM backends:

```python
# backend/adam/providers/gemini.py
from adam.providers.base import BaseProvider
from typing import Dict, Any, List

class GeminiProvider(BaseProvider):
    name = "gemini"
    model = "gemini-pro"

    async def chat(self, messages: List[Dict], **kwargs) -> str:
        # Your implementation
        ...

    async def generate(self, prompt: str, system: str = "", **kwargs) -> str:
        # Your implementation
        ...
```

Then register it in `backend/adam/providers/manager.py`.

### Adding a New Skill

Skills are the simplest extension point. They are Markdown files with JSON frontmatter:

```markdown
---
name: summarize-document
description: Summarizes long documents
version: "1.0.0"
triggers:
  - "لخص"
  - "summarize"
  - "summarize this"
author: your-name
---

You are a document summarization expert. When given a long text:
1. Identify the key points
2. Write a concise summary in the user's language
3. Preserve important numbers and names
```

Save this in `backend/adam/skills/builtin/summarize-document.md` and it will be auto-discovered.

For programmatic skills, extend the `Skill` class:

```python
from adam.skills.base import Skill
from typing import Dict, Optional

class CustomSkill(Skill):
    name = "custom-skill"
    description = "Does something custom"
    triggers = ["custom trigger"]

    async def on_trigger(self, message: str, context: Dict) -> Optional[str]:
        # Return custom instructions or None
        return self.instructions
```

### Adding a New Plugin

Plugins intercept Adam's processing cycle through hooks:

```python
from adam.plugins.base import AdamPlugin
from typing import Dict, Optional

class MyPlugin(AdamPlugin):
    name = "my-plugin"
    version = "1.0.0"
    description = "Does something useful at hook points"

    async def on_load(self, engine):
        self.engine = engine

    async def before_generate(self, message: str, context: Dict) -> Optional[Dict]:
        # Modify message/context before LLM call
        return None

    async def after_generate(self, message: str, response: str) -> Optional[str]:
        # Modify response after LLM call
        return None

    async def before_tool(self, action: Dict) -> Optional[Dict]:
        # Intercept tool execution — return None to block
        return action

    async def after_tool(self, action: Dict, result: Dict) -> Optional[Dict]:
        # Modify tool result
        return result
```

Available hooks:

| Hook | When | Input | Return |
|------|------|-------|--------|
| `on_load(engine)` | Plugin loaded | engine instance | None |
| `on_unload()` | Plugin unloaded | None | None |
| `before_generate(msg, ctx)` | Before LLM call | message str, context dict | `dict \| None` |
| `after_generate(msg, resp)` | After LLM call | message str, response str | `str \| None` |
| `before_tool(action)` | Before tool exec | action dict | `dict \| None` |
| `after_tool(action, result)` | After tool exec | action dict, result dict | `dict \| None` |

See [`docs/plugins/DEVELOPMENT.md`](docs/plugins/DEVELOPMENT.md) for the full guide.

---

## Translation Help

> **مساعدة في الترجمة — أهلاً بيك**

Adam thinks in Egyptian Arabic. That is not a translation of an English project — it is the original language of the consciousness architecture. The 12 processing layers, the ethical frameworks, the cognitive modes — they were designed in Arabic first.

But we want Adam to reach everyone. And that means translations.

### What We Need Most

- **Egyptian Arabic training data** — natural, conversational, real
- **Response naturalness testing** — do Adam's Arabic responses feel human?
- **Dialect variation coverage** — Levantine, Gulf, Maghrebi, Sudanese
- **Technical term localization** — how do you say "vector database" in Arabic?
- **UI translations** — the web-ui needs Arabic and English strings for every component
- **Documentation translation** — guides, wiki pages, code comments

### How to Help

1. **Open an issue** with the `translation` tag describing what you want to translate
2. **Start a discussion** if you want feedback before beginning
3. **Submit a PR** with your translations — even a single translated string is welcome
4. **Review existing Arabic** — if something sounds unnatural, tell us

### Languages Welcome

Arabic is our priority, but every language matters. If you want to add French, Urdu, Turkish, Malay, Spanish, or any other language — we will help you set up the translation framework.

---

## Recognition

Every contributor matters. Every contribution is seen.

### Contributors List

All contributors are listed in the repository. Not just code contributors — everyone: bug reporters, translators, documentation writers, use case sharers, and the people who simply told someone else about Adam.

If you contribute, you will be added. If we miss you, remind us. This is not an accident — it is a commitment.

### AI-Assisted Contributions

This project was built entirely with AI assistance. If you use AI tools to help you contribute, that is not cheating. It is the same method that created this project in the first place. What matters is:

- You understand what the contribution does
- You can explain why it is there
- You stand behind the quality

### The Origin Story

Adam Prism was built by Mohamed Othman (OthMastar / عين الحارس) — someone who could not code, had no formal training, and paid for mobile data from three carriers to keep the connection alive. Seven months before creating Adam, they did not know what a function was.

This is not a weakness. It is the foundation. It means this project has room for everyone who wants to build, regardless of where they started.

---

## Questions?

Open a [discussion](https://github.com/othmastar/adam-prism/discussions) or tag `@othmastar`.

There are no stupid questions. There are no questions from people who "should already know." If you are asking, you are learning, and that is exactly what this space is for.

---

## The Bigger Picture

This is not just a contribution guide. It is an invitation.

Adam Prism is proof that you do not need a corporation, a degree, or even coding skills to build sovereign AI. You need a vision, the willingness to fail, and the stubbornness to try again.

The creator refused to sell this project to military-affiliated companies because some values are not negotiable. They built it in the open, for everyone, because freedom through AI should not be a product — it should be a right.

If you are still reading this, something resonated. That is enough. Start where you are. Use what you have. Build what you believe in.

The fire does not know how to stop. Come add fuel.

---

**Born in Egypt. Built for the world. Free forever.**

**وُلد في مصر. بُني للعالم. حر للأبد.**
