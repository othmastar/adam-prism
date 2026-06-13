"""أدوات النظام — mouse, keyboard, clipboard, screen, window"""

import os
import subprocess
import uuid


class SystemToolsMixin:
    """Mixin: mouse, keyboard, clipboard, screen, window tools"""

    async def _tool_mouse(self, tool_name: str, params: dict) -> dict:
        _ws_bin = self._local_bin
        _env = {**os.environ, "PATH": f"{_ws_bin}:{os.environ.get('PATH', '')}"}
        try:
            if tool_name == "mouse_click":
                x, y = params.get("x"), params.get("y")
                button = params.get("button", "left")
                btn = {"left": "1", "middle": "2", "right": "3"}.get(button, "1")
                cmd = ["xdotool"]
                if x is not None and y is not None:
                    cmd += ["mousemove", "--", str(int(x)), str(int(y))]
                cmd += ["click", btn]
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=5, env=_env)
                return {"success": r.returncode == 0, "error": r.stderr.strip() or ""}

            elif tool_name == "mouse_move":
                x, y = params.get("x"), params.get("y")
                if x is None or y is None:
                    return {"success": False, "error": "مفيش x, y"}
                r = subprocess.run(["xdotool", "mousemove", "--", str(int(x)), str(int(y))],
                                  capture_output=True, text=True, timeout=5, env=_env)
                return {"success": r.returncode == 0, "error": r.stderr.strip() or ""}

            elif tool_name == "mouse_scroll":
                dx, dy = params.get("delta_x", 0) or 0, params.get("delta_y", 0) or 0
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
                    subprocess.run(["xdotool", *clicks], capture_output=True, timeout=5, env=_env)
                return {"success": True}

            elif tool_name == "mouse_drag":
                sx, sy = params.get("start_x"), params.get("start_y")
                ex, ey = params.get("end_x"), params.get("end_y")
                if None in (sx, sy, ex, ey):
                    return {"success": False, "error": "مفيش start_x, start_y, end_x, end_y"}
                r = subprocess.run(
                    ["xdotool", "mousemove", "--", str(int(sx)), str(int(sy)),
                     "mousedown", "1", "mousemove", "--", str(int(ex)), str(int(ey)), "mouseup", "1"],
                    capture_output=True, text=True, timeout=10, env=_env)
                return {"success": r.returncode == 0, "error": r.stderr.strip() or ""}

            elif tool_name == "mouse_position":
                r = subprocess.run(["xdotool", "getmouselocation"], capture_output=True, text=True, timeout=5, env=_env)
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

    async def _tool_keyboard(self, tool_name: str, params: dict) -> dict:
        _ws_bin = self._local_bin
        _env = {**os.environ, "PATH": f"{_ws_bin}:{os.environ.get('PATH', '')}"}
        try:
            if tool_name == "keyboard_type":
                text = params.get("text", "")
                if not text:
                    return {"success": False, "error": "مفيش نص"}
                r = subprocess.run(["xdotool", "type", text], capture_output=True, text=True, timeout=10, env=_env)
                return {"success": r.returncode == 0, "error": r.stderr.strip() or ""}

            elif tool_name == "keyboard_press":
                key = params.get("key", "")
                if not key:
                    return {"success": False, "error": "مفيش key"}
                r = subprocess.run(["xdotool", "key", key], capture_output=True, text=True, timeout=5, env=_env)
                return {"success": r.returncode == 0, "error": r.stderr.strip() or ""}

            elif tool_name == "keyboard_hotkey":
                keys = params.get("keys", [])
                if not keys:
                    return {"success": False, "error": "مفيش keys"}
                r = subprocess.run(["xdotool", "key"] + [str(k) for k in keys],
                                  capture_output=True, text=True, timeout=5, env=_env)
                return {"success": r.returncode == 0, "error": r.stderr.strip() or ""}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _tool_clipboard(self, tool_name: str, params: dict) -> dict:
        _ws_bin = self._local_bin
        _env = {**os.environ, "PATH": f"{_ws_bin}:{os.environ.get('PATH', '')}"}
        try:
            if tool_name == "clipboard_read":
                r = subprocess.run(["xsel", "-b", "-o"], capture_output=True, text=True, timeout=5, env=_env)
                return {"success": r.returncode == 0, "data": r.stdout, "error": r.stderr.strip() or ""}
            elif tool_name == "clipboard_write":
                text = params.get("text", "")
                if not text:
                    return {"success": False, "error": "مفيش نص"}
                r = subprocess.run(["xsel", "-b"], input=text, capture_output=True, text=True, timeout=5, env=_env)
                return {"success": r.returncode == 0, "error": r.stderr.strip() or ""}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _tool_screen(self, tool_name: str, params: dict) -> dict:
        try:
            if tool_name == "screen_info":
                r = subprocess.run(["xrandr"], capture_output=True, text=True, timeout=5)
                return {"success": r.returncode == 0, "data": r.stdout, "error": r.stderr.strip() or ""}

            elif tool_name == "screen_ocr":
                _ws_bin = self._local_bin
                _env = {**os.environ, "PATH": f"{_ws_bin}:{os.environ.get('PATH', '')}"}
                shot = f"/tmp/adam_ocr_{uuid.uuid4().hex[:8]}.png"
                r1 = subprocess.run(["import", "-window", "root", shot], capture_output=True, text=True, timeout=10, env=_env)
                if r1.returncode != 0:
                    return {"success": False, "error": f"تعذر التصوير: {r1.stderr.strip()}"}
                if not os.path.exists(shot):
                    return {"success": False, "error": "تعذر التصوير: ملف مش موجود"}
                r2 = subprocess.run(["tesseract", shot, "stdout", "-l", "ara+eng"],
                                   capture_output=True, text=True, timeout=30)
                os.remove(shot)
                text = r2.stdout.strip()
                if text:
                    return {"success": True, "text": text, "lang": "ara+eng"}
                return {"success": False, "error": "مفيش نص اتشاف", "text": ""}
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "الـ OCR تجاوز الـ 30 ثانية"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _tool_window(self, tool_name: str, params: dict) -> dict:
        _ws_bin = self._local_bin
        _env = {**os.environ, "PATH": f"{_ws_bin}:{os.environ.get('PATH', '')}"}
        try:
            if tool_name == "window_focus":
                title = params.get("title", "")
                if not title:
                    return {"success": False, "error": "مفيش عنوان"}
                r = subprocess.run(["xdotool", "search", "--name", title, "windowactivate"],
                                  capture_output=True, text=True, timeout=5, env=_env)
                if r.returncode == 0 and r.stdout.strip():
                    return {"success": True}
                r2 = subprocess.run(["wmctrl", "-a", title], capture_output=True, text=True, timeout=5, env=_env)
                if r2.returncode == 0:
                    return {"success": True}
                return {"success": False, "error": "النافذة مش موجودة"}

            elif tool_name == "window_list":
                r = subprocess.run(["wmctrl", "-l", "-p"], capture_output=True, text=True, timeout=5, env=_env)
                if r.returncode == 0:
                    windows = []
                    for line in r.stdout.strip().split("\n"):
                        if line.strip():
                            parts = line.split(None, 4)
                            windows.append({
                                "id": parts[0] if len(parts) > 0 else "",
                                "desktop": parts[1] if len(parts) > 1 else "",
                                "pid": parts[2] if len(parts) > 2 else "",
                                "host": parts[3] if len(parts) > 3 else "",
                                "title": parts[4] if len(parts) > 4 else "",
                            })
                    return {"success": True, "windows": windows, "count": len(windows)}
                return {"success": False, "error": r.stderr.strip()}
        except Exception as e:
            return {"success": False, "error": str(e)}
