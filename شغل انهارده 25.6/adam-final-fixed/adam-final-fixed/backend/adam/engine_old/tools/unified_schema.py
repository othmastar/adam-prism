"""
Adam Prism — Unified Tool Calling Schema
=========================================
صيغة موحّدة لاستدعاء الأدوات — متوافقة مع Hermes Agent

Format:
  <tool_call>
  {"name": "tool_name", "arguments": {"param1": "val1"}}
  </tool_call>

GOAP Scratch Pad (optional):
  <scratch_pad>
  Goal: <هدف المستخدم>
  Actions: <خطة الأدوات>
  Reflection: <تحليل>
  </scratch_pad>
"""

import json
import re
from typing import Any
from pydantic import BaseModel, Field


# ═══════════════════════════════════════
# Tool Schema Definitions (Pydantic)
# ═══════════════════════════════════════

class ToolCall(BaseModel):
    """Unified tool call format — matches Hermes Agent."""
    name: str = Field(..., description="Tool function name")
    arguments: dict[str, Any] = Field(default_factory=dict, description="Tool parameters")


class ToolDefinition(BaseModel):
    """Tool definition for system prompt."""
    name: str
    description: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    required: list[str] = Field(default_factory=list)


# ═══════════════════════════════════════
# Tool Registry — All 32 tools
# ═══════════════════════════════════════

TOOL_REGISTRY: dict[str, ToolDefinition] = {
    # Browser
    "browser_open": ToolDefinition(
        name="browser_open", description="Open a URL in the browser",
        parameters={"url": {"type": "string", "description": "The URL to open"}},
        required=["url"]),
    "browser_fetch": ToolDefinition(
        name="browser_fetch", description="Fetch content from a URL",
        parameters={"url": {"type": "string"}}, required=["url"]),
    "browser_click": ToolDefinition(
        name="browser_click", description="Click on an element",
        parameters={"selector": {"type": "string"}}, required=["selector"]),
    "browser_type": ToolDefinition(
        name="browser_type", description="Type text into an element",
        parameters={"selector": {"type": "string"}, "text": {"type": "string"}},
        required=["selector", "text"]),
    "browser_read": ToolDefinition(
        name="browser_read", description="Read page content",
        parameters={"selector": {"type": "string", "default": "body"}}, required=[]),
    "screenshot": ToolDefinition(
        name="screenshot", description="Take a screenshot of the browser",
        parameters={}, required=[]),

    # Shell & System
    "shell": ToolDefinition(
        name="shell", description="Execute a shell command (whitelisted)",
        parameters={"command": {"type": "string"}}, required=["command"]),
    "python_exec": ToolDefinition(
        name="python_exec", description="Execute Python code in sandbox",
        parameters={"code": {"type": "string"}}, required=["code"]),
    "disk_space": ToolDefinition(
        name="disk_space", description="Check disk space",
        parameters={}, required=[]),

    # File Operations
    "file_read": ToolDefinition(
        name="file_read", description="Read contents of a text file",
        parameters={"path": {"type": "string"}}, required=["path"]),
    "file_write": ToolDefinition(
        name="file_write", description="Write content to a file",
        parameters={"path": {"type": "string"}, "content": {"type": "string"}},
        required=["path", "content"]),
    "file_download": ToolDefinition(
        name="file_download", description="Download a file from URL",
        parameters={"url": {"type": "string"}, "save_path": {"type": "string"}},
        required=["url"]),

    # Mouse
    "mouse_click": ToolDefinition(
        name="mouse_click", description="Click mouse at coordinates",
        parameters={"x": {"type": "integer"}, "y": {"type": "integer"}},
        required=["x", "y"]),
    "mouse_move": ToolDefinition(
        name="mouse_move", description="Move mouse to coordinates",
        parameters={"x": {"type": "integer"}, "y": {"type": "integer"}},
        required=["x", "y"]),
    "mouse_scroll": ToolDefinition(
        name="mouse_scroll", description="Scroll mouse wheel",
        parameters={"amount": {"type": "integer"}}, required=["amount"]),
    "mouse_position": ToolDefinition(
        name="mouse_position", description="Get current mouse position",
        parameters={}, required=[]),

    # Keyboard
    "keyboard_type": ToolDefinition(
        name="keyboard_type", description="Type text via keyboard",
        parameters={"text": {"type": "string"}}, required=["text"]),
    "keyboard_press": ToolDefinition(
        name="keyboard_press", description="Press a key",
        parameters={"key": {"type": "string"}}, required=["key"]),
    "keyboard_hotkey": ToolDefinition(
        name="keyboard_hotkey", description="Press a key combination",
        parameters={"keys": {"type": "string"}}, required=["keys"]),

    # Clipboard
    "clipboard_read": ToolDefinition(
        name="clipboard_read", description="Read clipboard content",
        parameters={}, required=[]),
    "clipboard_write": ToolDefinition(
        name="clipboard_write", description="Write to clipboard",
        parameters={"text": {"type": "string"}}, required=["text"]),

    # Screen
    "screen_ocr": ToolDefinition(
        name="screen_ocr", description="Extract text from screen via OCR",
        parameters={"region": {"type": "string", "default": "full"}}, required=[]),
    "screen_info": ToolDefinition(
        name="screen_info", description="Get screen dimensions/info",
        parameters={}, required=[]),

    # Windows
    "window_focus": ToolDefinition(
        name="window_focus", description="Focus a window by title",
        parameters={"title": {"type": "string"}}, required=["title"]),
    "window_list": ToolDefinition(
        name="window_list", description="List all open windows",
        parameters={}, required=[]),

    # Knowledge
    "search_knowledge": ToolDefinition(
        name="search_knowledge", description="Search the knowledge base",
        parameters={"query": {"type": "string"}, "collection": {"type": "string", "default": "knowledge"}},
        required=["query"]),
    "check_preferences": ToolDefinition(
        name="check_preferences", description="Check learned preferences",
        parameters={"category": {"type": "string"}}, required=["category"]),
    "request_permission": ToolDefinition(
        name="request_permission", description="Request permission for action",
        parameters={"action": {"type": "string"}, "reason": {"type": "string"}},
        required=["action"]),

    # Memory
    "memory_store": ToolDefinition(
        name="memory_store", description="Store a fact in long-term memory",
        parameters={"content": {"type": "string"}, "data": {"type": "string"}, "priority": {"type": "integer", "default": 3}},
        required=["content"]),
    "memory_recall": ToolDefinition(
        name="memory_recall", description="Recall facts from memory",
        parameters={"query": {"type": "string"}}, required=["query"]),
    "memory_reflect": ToolDefinition(
        name="memory_reflect", description="Reflect on recent memories",
        parameters={"days": {"type": "integer", "default": 7}}, required=[]),

    # Planning
    "tool_planning": ToolDefinition(
        name="tool_planning", description="Plan a sequence of tool calls",
        parameters={"goal": {"type": "string"}, "steps": {"type": "array"}},
        required=["goal"]),
}


# ═══════════════════════════════════════
# Parsing Functions
# ═══════════════════════════════════════

def parse_tool_call(text: str) -> ToolCall | None:
    """Parse unified <tool_call> format. Returns ToolCall or None."""
    # Format: <tool_call>{"name": "...", "arguments": {...}}</tool_call>
    match = re.search(r'<tool_call>\s*(.*?)\s*</tool_call>', text, re.DOTALL)
    if not match:
        return None
    try:
        data = json.loads(match.group(1))
        return ToolCall(**data)
    except (json.JSONDecodeError, Exception):
        return None


def parse_scratch_pad(text: str) -> dict[str, str] | None:
    """Parse GOAP scratch pad for planning."""
    match = re.search(r'<scratch_pad>(.*?)</scratch_pad>', text, re.DOTALL)
    if not match:
        return None
    content = match.group(1)
    result = {}
    for field in ["Goal", "Actions", "Observation", "Reflection"]:
        m = re.search(rf'{field}:\s*(.*?)(?=\n\w+:|$)', content, re.DOTALL)
        if m:
            result[field.lower()] = m.group(1).strip()
    return result


def validate_tool_call(name: str, arguments: dict) -> tuple[bool, str]:
    """Validate tool call arguments against registry. Returns (valid, error)."""
    tool = TOOL_REGISTRY.get(name)
    if not tool:
        return False, f"Unknown tool: {name}"
    for req in tool.required:
        if req not in arguments or arguments[req] is None:
            return False, f"Missing required parameter: {req}"
    return True, ""


def get_tools_prompt() -> str:
    """Build the tools section for the system prompt — Hermes-compatible format."""
    tools_json = []
    for tool in TOOL_REGISTRY.values():
        func = {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": {
                    "type": "object",
                    "properties": tool.parameters,
                    "required": tool.required,
                }
            }
        }
        tools_json.append(func)
    return json.dumps(tools_json, ensure_ascii=False, indent=2)


def get_tool_names() -> list[str]:
    """Return list of all available tool names."""
    return sorted(TOOL_REGISTRY.keys())


def get_tool_count() -> int:
    """Return count of registered tools."""
    return len(TOOL_REGISTRY)
