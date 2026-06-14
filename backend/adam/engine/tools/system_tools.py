"""أدوات النظام — mouse, keyboard, clipboard, screen, window"""

import asyncio
import os
import uuid


class SystemToolsMixin:
    """Mixin: mouse, keyboard, clipboard, screen, window tools"""

    async def _run_cmd(self, cmd: list[str], *, env=None, timeout: float = 5.0, input_text: str | None = None) -> dict:
        """[PHASE2] Async subprocess helper - non-blocking replacement for subprocess.run"""
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.PIPE if input_text is not None else None,
                env=env,
            )
            try:
                stdin_data = input_text.encode("utf-8") if input_text else None
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(input=stdin_data), timeout=timeout
                )
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                return {"success": False, "error": "timeout", "exit_code": -1}
            return {
                "success": proc.returncode == 0,
                "stdout": stdout.decode("utf-8", errors="replace"),
                "stderr": stderr.decode("utf-8", errors="replace"),
                "exit_code": proc.returncode,
            }
        except FileNotFoundError as e:
            return {"success": False, "error": f"command not found: {e.filename}", "exit_code": -1}
        except Exception as e:
            return {"success": False, "error": str(e), "exit_code": -1}

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
                r = await self._run_cmd(cmd, env=_env, timeout=5)
                return {"success": r["success"], "error": r.get("stderr", "").strip()}

            elif tool_name == "mouse_move":
                x, y = params.get("x"), params.get("y")
                if x is None or y is None:
                    return {"success": False, "error": "مفيش x, y"}
                r = await self._run_cmd(
                    ["xdotool", "mousemove", "--", str(int(x)), str(int(y))],
                    env=_env, timeout=5
                )
                return {"success": r["success"], "error": r.get("stderr", "").strip()}

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
                    await self._run_cmd(["xdotool", *clicks], env=_env, timeout=5)
                return {"success": True}

            elif tool_name == "mouse_drag":
                sx, sy = params.get("start_x"), params.get("start_y")
                ex, ey = params.get("end_x"), params.get("end_y")
                if None in (sx, sy, ex, ey):
                    return {"success": False, "error": "مفيش start_x, start_y, end_x, end_y"}
                r = await self._run_cmd(
                    ["xdotool", "mousemove", "--", str(int(sx)), str(int(sy)),
                     "mousedown", "1", "mousemove", "--", str(int(ex)), str(int(ey)), "mouseup", "1"],
                    env=_env, timeout=10
                )
                return {"success": r["success"], "error": r.get("stderr", "").strip()}

            elif tool_name == "mouse_position":
                r = await self._run_cmd(["xdotool", "getmouselocation"], env=_env, timeout=5)
                if r["success"]:
                    parts = {}
                    for part in r.get("stdout", "").strip().split():
                        if ":" in part:
                            k, v = part.split(":")
                            parts[k] = int(v)
                    return {"success": True, "x": parts.get("x", 0), "y": parts.get("y", 0),
                            "screen": parts.get("screen", 0), "window": parts.get("window", 0)}
                return {"success": False, "error": r.get("stderr", "").strip()}
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
                r = await self._run_cmd(["xdotool", "type", text], env=_env, timeout=10)
                return {"success": r["success"], "error": r.get("stderr", "").strip()}

            elif tool_name == "keyboard_press":
                key = params.get("key", "")
                if not key:
                    return {"success": False, "error": "مفيش key"}
                r = await self._run_cmd(["xdotool", "key", key], env=_env, timeout=5)
                return {"success": r["success"], "error": r.get("stderr", "").strip()}

            elif tool_name == "keyboard_hotkey":
                keys = params.get("keys", [])
                if not keys:
                    return {"success": False, "error": "مفيش keys"}
                r = await self._run_cmd(["xdotool", "key"] + [str(k) for k in keys], env=_env, timeout=5)
                return {"success": r["success"], "error": r.get("stderr", "").strip()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _tool_clipboard(self, tool_name: str, params: dict) -> dict:
        _ws_bin = self._local_bin
        _env = {**os.environ, "PATH": f"{_ws_bin}:{os.environ.get('PATH', '')}"}
        try:
            if tool_name == "clipboard_read":
                r = await self._run_cmd(["xsel", "-b", "-o"], env=_env, timeout=5)
                return {"success": r["success"], "data": r.get("stdout", ""), "error": r.get("stderr", "").strip()}
            elif tool_name == "clipboard_write":
                text = params.get("text", "")
                if not text:
                    return {"success": False, "error": "مفيش نص"}
                r = await self._run_cmd(
                    ["xsel", "-b"], env=_env, timeout=5, input_text=text
                )
                return {"success": r["success"], "error": r.get("stderr", "").strip()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _tool_screen(self, tool_name: str, params: dict) -> dict:
        try:
            if tool_name == "screen_info":
                r = await self._run_cmd(["xrandr"], timeout=5)
                return {"success": r["success"], "data": r.get("stdout", ""), "error": r.get("stderr", "").strip()}

            elif tool_name == "screen_ocr":
                _ws_bin = self._local_bin
                _env = {**os.environ, "PATH": f"{_ws_bin}:{os.environ.get('PATH', '')}"}
                shot = f"/tmp/adam_ocr_{uuid.uuid4().hex[:8]}.png"
                r1 = await self._run_cmd(["import", "-window", "root", shot], env=_env, timeout=10)
                if not r1["success"]:
                    return {"success": False, "error": f"تعذر التصوير: {r1.get('stderr', '').strip()}"}
                if not os.path.exists(shot):
                    return {"success": False, "error": "تعذر التصوير: ملف مش موجود"}
                r2 = await self._run_cmd(["tesseract", shot, "stdout", "-l", "ara+eng"], timeout=30)
                os.remove(shot)
                text = r2.get("stdout", "").strip()
                if text:
                    return {"success": True, "text": text, "lang": "ara+eng"}
                return {"success": False, "error": "مفيش نص اتشاف", "text": ""}
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
                r = await self._run_cmd(
                    ["xdotool", "search", "--name", title, "windowactivate"],
                    env=_env, timeout=5
                )
                if r["success"] and r.get("stdout", "").strip():
                    return {"success": True}
                r2 = await self._run_cmd(["wmctrl", "-a", title], env=_env, timeout=5)
                if r2["success"]:
                    return {"success": True}
                return {"success": False, "error": "النافذة مش موجودة"}

            elif tool_name == "window_list":
                r = await self._run_cmd(["wmctrl", "-l", "-p"], env=_env, timeout=5)
                if r["success"]:
                    windows = []
                    for line in r.get("stdout", "").strip().split("\n"):
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
