# Plugin Development Guide

## Overview

Adam Prism uses a **hook-based plugin system**. Each plugin can intercept and modify the engine's behavior at specific points in the processing cycle.

```
User Message
    │
    ▼
before_generate() ◄── Plugin Hook 1
    │
    ▼
  Engine Response
    │
    ▼
after_generate()  ◄── Plugin Hook 2
    │
    ▼
  Tool Execution
    │
    ▼
before_tool()     ◄── Plugin Hook 3
    │
    ▼
  Tool Result
    │
    ▼
after_tool()      ◄── Plugin Hook 4
    │
    ▼
  Final Response
```

## Getting Started

### 1. Create a plugin file

```python
# my_plugin.py
from adam.plugins import AdamPlugin

class MyPlugin(AdamPlugin):
    name = "my-plugin"
    version = "1.0.0"
    description = "Does something useful"
```

### 2. Implement hooks

```python
class MyPlugin(AdamPlugin):
    name = "my-plugin"
    description = "Logs all messages"

    async def on_load(self, engine):
        """Called when plugin is loaded"""
        self.engine = engine
        print(f"{self.name} loaded!")

    async def on_unload(self):
        """Called when plugin is unloaded"""
        print(f"{self.name} unloaded!")

    async def before_generate(self, message: str, context: dict) -> dict | None:
        """Modify message/context before generation.
        Return dict with 'message' and/or 'context' keys, or None to skip.
        """
        context["extra_info"] = "added by plugin"
        return {"message": message, "context": context}

    async def after_generate(self, message: str, response: str) -> str | None:
        """Modify response after generation.
        Return modified response string, or None to keep original.
        """
        return response + "\n\n— Powered by MyPlugin"

    async def before_tool(self, action: dict) -> dict | None:
        """Intercept tool execution.
        Return modified action, or None to block execution.
        """
        if action.get("tool") == "dangerous_tool":
            return None  # Block it
        return action

    async def after_tool(self, action: dict, result: dict) -> dict | None:
        """Modify tool result.
        Return modified result, or None to keep original.
        """
        result["plugin_processed"] = True
        return result
```

### 3. Load the plugin

```python
from adam.plugins import PluginManager

manager = PluginManager(engine=engine)
manager.load_plugin(MyPlugin)
```

Or load from a directory:

```python
manager.load_from_dir("path/to/plugins")
```

## Available Hooks

| Hook | When | Input | Return |
|------|------|-------|--------|
| `on_load(engine)` | Plugin loaded | engine instance | None |
| `on_unload()` | Plugin unloaded | None | None |
| `before_generate(msg, ctx)` | Before LLM call | message str, context dict | `dict \| None` |
| `after_generate(msg, resp)` | After LLM call | message str, response str | `str \| None` |
| `before_tool(action)` | Before tool exec | action dict | `dict \| None` |
| `after_tool(action, result)` | After tool exec | action dict, result dict | `dict \| None` |

## Example Plugins

### Rate Limiter

```python
import time
from adam.plugins import AdamPlugin

class RateLimiter(AdamPlugin):
    name = "rate-limiter"
    description = "Limits requests per user"

    def __init__(self):
        self.requests = {}

    async def before_generate(self, message: str, context: dict) -> dict | None:
        user = context.get("user_id", "default")
        now = time.time()

        if user not in self.requests:
            self.requests[user] = []

        # Clean old requests
        self.requests[user] = [t for t in self.requests[user] if now - t < 60]

        if len(self.requests[user]) >= 10:
            return {"message": "Rate limit exceeded. Please wait.", "context": context}

        self.requests[user].append(now)
        return None
```

### Translation Plugin

```python
class TranslateToArabic(AdamPlugin):
    name = "translate-ar"
    description = "Translates responses to Arabic"

    async def after_generate(self, message: str, response: str) -> str | None:
        # Integration with translation service
        # translated = await translate(response, target="ar")
        return response  # Replace with translated
```

## Directory Structure

```text
plugins/
├── my-plugin/
│   ├── __init__.py       # Plugin class
│   └── requirements.txt  # Optional dependencies
└── simple_plugin.py      # Single-file plugin
```

## Configuration

Plugins can access the engine config via `self.engine.config`:

```python
async def on_load(self, engine):
    self.engine = engine
    self.my_setting = engine.config.get("my_plugin_setting", "default")
```

## Best Practices

1. **Keep it async** — All hooks are async
2. **Don't block** — Heavy work should use `asyncio.create_task()`
3. **Be specific** — Only implement hooks you need
4. **Handle errors** — Never let exceptions propagate
5. **Stateless when possible** — Use engine's memory for persistence
6. **Log everything** — Use `logging` not `print`
7. **Version your plugin** — Follow semver
8. **Test your plugin** — Use pytest like the built-in tests
