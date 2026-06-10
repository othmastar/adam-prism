"""
Adam Prism — Computer Use Tools
==================================
أدوات التحكم في الحاسوب: mouse, keyboard, clipboard, screen.
تستخدم xdotool, xsel, xrandr, import (ImageMagick).
"""

import os
import subprocess
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("adam_prism.tools")

_WS_BIN = "/mnt/Workspace/.local/bin"
_ENV = {**os.environ, "PATH": f"{_WS_BIN}:{os.environ.get('PATH', '')}"}


class ComputerToolManager:
    """إدارة أدوات الحاسوب — تعمل بدون Playwright"""

    async def execute_action(self, action: Dict) -> Dict:
        action_type = action.get("type", "")
        handler = getattr(self, f"_{action_type}", None)
        if not handler:
            return {"success": False, "error": f"إجراء غير معروف: {action_type}"}
        try:
            return await handler(action)
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ─── Mouse ───────────────────────────────────────────

    async def _mouse_click(self, action: Dict) -> Dict:
        x = action.get("x")
        y = action.get("y")
        button = action.get("button", "left")
        btn = {"left": "1", "middle": "2", "right": "3"}.get(button, "1")
        try:
            cmd = ["xdotool"]
            if x is not None and y is not None:
                cmd += ["mousemove", "--", str(int(x)), str(int(y))]
            cmd += ["click", btn]
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=5, env=_ENV)
            return {"success": r.returncode == 0, "error": r.stderr.strip() or ""}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _mouse_move(self, action: Dict) -> Dict:
        x, y = action.get("x"), action.get("y")
        if x is None or y is None:
            return {"success": False, "error": "مفيش x, y"}
        try:
            r = subprocess.run(["xdotool", "mousemove", "--", str(int(x)), str(int(y))],
                              capture_output=True, text=True, timeout=5, env=_ENV)
            return {"success": r.returncode == 0, "error": r.stderr.strip() or ""}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _mouse_scroll(self, action: Dict) -> Dict:
        dx = action.get("delta_x", 0) or 0
        dy = action.get("delta_y", 0) or 0
        try:
            clicks = []
            if dy:
                btn = "4" if int(dy) < 0 else "5"
                for _ in range(min(abs(int(dy)) // 10 + 1, 20)):
                    clicks += ["click", btn]
            if dx:
                btn = "6" if int(dx) < 0 else "7"
                for _ in range(min(abs(int(dx)) // 10 + 1, 20)):
                    clicks += ["click", btn]
            if clicks:
                subprocess.run(["xdotool"] + clicks, capture_output=True, timeout=5, env=_ENV)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _mouse_drag(self, action: Dict) -> Dict:
        sx, sy = action.get("start_x"), action.get("start_y")
        ex, ey = action.get("end_x"), action.get("end_y")
        if None in (sx, sy, ex, ey):
            return {"success": False, "error": "مفيش start_x, start_y, end_x, end_y"}
        try:
            r = subprocess.run(
                ["xdotool", "mousemove", "--", str(int(sx)), str(int(sy)),
                 "mousedown", "1",
                 "mousemove", "--", str(int(ex)), str(int(ey)),
                 "mouseup", "1"],
                capture_output=True, text=True, timeout=10, env=_ENV)
            return {"success": r.returncode == 0, "error": r.stderr.strip() or ""}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _mouse_position(self, action: Dict) -> Dict:
        try:
            r = subprocess.run(["xdotool", "getmouselocation"],
                              capture_output=True, text=True, timeout=5, env=_ENV)
            if r.returncode == 0:
                parts = {}
                for part in r.stdout.strip().split():
                    if ":" in part:
                        k, v = part.split(":")
                        parts[k] = int(v)
                return {"success": True, "x": parts.get("x", 0), "y": parts.get("y", 0),
                        "screen": parts.get("screen", 0), "window": parts.get("window", 0)}
            return {"success": False, "error": r.stderr.strip()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ─── Keyboard ────────────────────────────────────────

    async def _keyboard_type(self, action: Dict) -> Dict:
        text = action.get("text", "")
        if not text:
            return {"success": False, "error": "مفيش نص"}
        try:
            r = subprocess.run(["xdotool", "type", text],
                              capture_output=True, text=True, timeout=10, env=_ENV)
            return {"success": r.returncode == 0, "error": r.stderr.strip() or ""}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _keyboard_press(self, action: Dict) -> Dict:
        key = action.get("key", "")
        if not key:
            return {"success": False, "error": "مفيش key"}
        try:
            r = subprocess.run(["xdotool", "key", key],
                              capture_output=True, text=True, timeout=5, env=_ENV)
            return {"success": r.returncode == 0, "error": r.stderr.strip() or ""}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _keyboard_hotkey(self, action: Dict) -> Dict:
        keys = action.get("keys", [])
        if not keys:
            return {"success": False, "error": "مفيش keys"}
        try:
            r = subprocess.run(["xdotool", "key"] + [str(k) for k in keys],
                              capture_output=True, text=True, timeout=5, env=_ENV)
            return {"success": r.returncode == 0, "error": r.stderr.strip() or ""}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ─── Clipboard ───────────────────────────────────────

    async def _clipboard_read(self, action: Dict) -> Dict:
        try:
            r = subprocess.run(["xsel", "-b", "-o"], capture_output=True, text=True, timeout=5, env=_ENV)
            return {"success": r.returncode == 0, "data": r.stdout, "error": r.stderr.strip() or ""}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _clipboard_write(self, action: Dict) -> Dict:
        text = action.get("text", "")
        if not text:
            return {"success": False, "error": "مفيش نص"}
        try:
            r = subprocess.run(["xsel", "-b"], input=text, capture_output=True, text=True, timeout=5, env=_ENV)
            return {"success": r.returncode == 0, "error": r.stderr.strip() or ""}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ─── Screen ──────────────────────────────────────────

    async def _screen_info(self, action: Dict) -> Dict:
        try:
            r = subprocess.run(["xrandr"], capture_output=True, text=True, timeout=5)
            return {"success": r.returncode == 0, "data": r.stdout, "error": r.stderr.strip() or ""}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _screen_ocr(self, action: Dict) -> Dict:
        """تصوير الشاشة + OCR — يحتاج tesseract"""
        try:
            import uuid
            shot = f"/tmp/adam_ocr_{uuid.uuid4().hex[:8]}.png"
            r1 = subprocess.run(["import", "-window", "root", shot],
                               capture_output=True, text=True, timeout=10, env=_ENV)
            if r1.returncode != 0:
                return {"success": False, "error": r1.stderr.strip()}
            r2 = subprocess.run(["tesseract", shot, "stdout"],
                               capture_output=True, text=True, timeout=30)
            os.remove(shot)
            return {"success": r2.returncode == 0, "data": r2.stdout.strip(),
                    "error": r2.stderr.strip() or ""}
        except FileNotFoundError:
            return {"success": False, "error": "tesseract مش مثبت. شغّل: sudo apt install tesseract-ocr"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ─── Window ──────────────────────────────────────────

    async def _window_focus(self, action: Dict) -> Dict:
        window = action.get("window", "")
        if not window:
            return {"success": False, "error": "مفيش window"}
        try:
            r = subprocess.run(["xdotool", "search", "--name", window, "windowactivate"],
                              capture_output=True, text=True, timeout=5, env=_ENV)
            return {"success": r.returncode == 0, "error": r.stderr.strip() or ""}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _window_list(self, action: Dict) -> Dict:
        try:
            r = subprocess.run(["wmctrl", "-l"], capture_output=True, text=True, timeout=5)
            windows = []
            for line in r.stdout.strip().split("\n"):
                if line:
                    parts = line.split(None, 3)
                    if len(parts) >= 4:
                        windows.append({"id": parts[0], "desktop": parts[1], "pid": parts[2], "title": parts[3]})
            return {"success": True, "windows": windows}
        except Exception as e:
            return {"success": False, "error": str(e)}
