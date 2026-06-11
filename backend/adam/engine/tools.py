"""
Adam Prism Engine Tools - تنفيذ الأدوات
========================================
Tool dispatcher + 14 handler methods for browser, mouse, keyboard, clipboard,
screen, window, disk, file, knowledge, preferences, shell, memory, planning.
"""

import os
import re
import json
import uuid
import time
import logging
import subprocess
import asyncio
from datetime import datetime
from typing import Optional, Dict, List, Any

from core.permissions import classify_tool, log_permission
from core import memory_store
from adam.infrastructure import sanitize_path
from adam.engine.generate import AdamPrismEngineGenerate

logger = logging.getLogger("adam_prism.core")


class AdamPrismEngineTools(AdamPrismEngineGenerate):
    """
    Mixin: tool dispatcher + 14 handler methods.
    """

    def _parse_tool_request(self, text: str) -> Optional[Dict]:
        """استخراج طلب أداة من رد النموذج"""
        func_pattern = r'<\|?tool_call\|?>\s*<function=(\w+)>(.*?)</function>\s*<\|?/?tool_call\|?>'
        func_match = re.search(func_pattern, text, re.DOTALL)
        if func_match:
            tool_name = func_match.group(1)
            params_block = func_match.group(2)
            params = {}
            for param_match in re.finditer(r'<parameter=(\w+)>(.*?)</parameter>', params_block, re.DOTALL):
                params[param_match.group(1)] = param_match.group(2).strip()
            return {"_tool": tool_name, "params": params}

        tc_pattern = r'<\|?tool_call\|?>\s*call:(\w+)\s*\{([^}]*)\}\s*<\|?/?tool_call\|?>'
        tc_match = re.search(tc_pattern, text, re.DOTALL)
        if tc_match:
            tool_name = tc_match.group(1)
            params_str = tc_match.group(2).strip()
            params = {}
            if params_str:
                try:
                    params = json.loads("{" + params_str + "}")
                except json.JSONDecodeError:
                    for kv in params_str.split(","):
                        if ":" in kv:
                            k, v = kv.split(":", 1)
                            k = k.strip().strip('"').strip("'")
                            v = v.strip().strip('"').strip("'")
                            params[k] = v
            return {"_tool": tool_name, "params": params}

        lines = text.strip().split("\n")
        for i in range(len(lines) - 1, max(len(lines) - 5, 0) - 1, -1):
            line = lines[i].strip()
            try:
                parsed = json.loads(line)
                if "_tool" in parsed:
                    return parsed
            except (json.JSONDecodeError, ValueError):
                continue

        json_pattern = r'\{\s*"_tool"\s*:\s*"[^"]+"\s*,"params"\s*:\s*\{[^}]*\}\s*\}'
        match = re.search(json_pattern, text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

        return None

    async def _execute_tool(self, tool_name: str, params: Dict) -> Dict:
        """تنفيذ أداة وإرجاع النتيجة — dispatcher يوزع على الـ handlers"""
        result = {"success": False, "error": "أداة غير معروفة"}

        # Permission + Plugin check
        allowed, tool_name, params = await self._tool_check_permissions(tool_name, params)
        if not allowed:
            return result

        # Dispatch حسب نوع الأداة
        BROWSER = ("browser_open", "browser_fetch", "browser_click", "browser_type", "browser_read", "screenshot")
        MOUSE = ("mouse_click", "mouse_move", "mouse_scroll", "mouse_drag", "mouse_position")
        KEYBOARD = ("keyboard_type", "keyboard_press", "keyboard_hotkey")
        CLIPBOARD = ("clipboard_read", "clipboard_write")
        SCREEN = ("screen_info", "screen_ocr")
        WINDOW = ("window_focus", "window_list")
        MEMORY = ("memory_store", "memory_recall", "memory_reflect")

        if tool_name in BROWSER:
            result = await self._tool_browser(tool_name, params)
        elif tool_name in MOUSE:
            result = await self._tool_mouse(tool_name, params)
        elif tool_name in KEYBOARD:
            result = await self._tool_keyboard(tool_name, params)
        elif tool_name in CLIPBOARD:
            result = await self._tool_clipboard(tool_name, params)
        elif tool_name in SCREEN:
            result = await self._tool_screen(tool_name, params)
        elif tool_name in WINDOW:
            result = await self._tool_window(tool_name, params)
        elif tool_name == "disk_space":
            result = await self._tool_disk(params)
        elif tool_name in ("file_read", "file_write", "file_download"):
            result = await self._tool_file(tool_name, params)
        elif tool_name == "search_knowledge":
            result = await self._tool_knowledge(params)
        elif tool_name in ("request_permission", "check_preferences", "notebook_update_profile"):
            result = await self._tool_preferences(tool_name, params)
        elif tool_name in ("shell", "python_exec"):
            result = await self._tool_shell(tool_name, params)
        elif tool_name in MEMORY:
            result = await self._tool_memory(tool_name, params)
        elif tool_name == "tool_planning":
            result = await self._tool_planning(params)

        # Plugin hook: after_tool
        if self.plugins:
            result = await self.plugins.run_after_tool({"type": tool_name, "params": params}, result)
        return result

    async def _tool_check_permissions(self, tool_name: str, params: Dict) -> tuple:
        """Permission Guard + Plugin before_tool. يرجع (allowed, tool_name, params)"""
        if self.security_guard:
            try:
                perm_verdict = await self.security_guard.check_tool_call(tool_name, params)
                if perm_verdict.action.value == "block":
                    return False, tool_name, params
            except Exception as e:
                logger.warning(f"Tool permission check error: {e}")

        if tool_name != "request_permission":
            cat = classify_tool(tool_name)
            need = self.permission.needs_permission(cat)
            if need:
                log_permission("blocked (deferred)", tool_name, cat,
                               "يحتاج صلاحية (phase 1b not activated)", need, "deferred")

        if self.plugins:
            action_check = await self.plugins.run_before_tool({"type": tool_name, "params": params})
            if action_check is None:
                return False, tool_name, params
            tool_name = action_check.get("type", tool_name)
            params = action_check.get("params", params)

        return True, tool_name, params

    async def _tool_browser(self, tool_name: str, params: Dict) -> Dict:
        """أدوات المتصفح — Playwright Firefox مباشرة"""
        try:
            from playwright.async_api import async_playwright
            os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "/mnt/Workspace/.local/ms-playwright"
            if not hasattr(self, '_pw_playwright') or self._pw_playwright is None:
                self._pw_playwright = await async_playwright().start()
                self._pw_browser = await self._pw_playwright.firefox.launch(headless=True)
                self._pw_page = await self._pw_browser.new_page()

            page = self._pw_page
            if tool_name == "browser_open":
                url = params.get("url", "")
                if not url:
                    return {"success": False, "error": "مفيش URL"}
                await page.goto(url, timeout=30000, wait_until="domcontentloaded")
                return {"success": True, "title": await page.title(), "url": page.url}

            elif tool_name == "browser_fetch":
                url = params.get("url", "")
                if not url:
                    return {"success": False, "error": "مفيش URL"}
                await page.goto(url, timeout=30000, wait_until="domcontentloaded")
                return {"success": True, "url": page.url, "title": await page.title(), "data": (await page.inner_text("body"))[:5000]}

            elif tool_name == "browser_click":
                selector = params.get("selector", "")
                if not selector:
                    return {"success": False, "error": "مفيش selector"}
                await page.click(selector, timeout=10000)
                return {"success": True}

            elif tool_name == "browser_type":
                text = params.get("text", "")
                selector = params.get("selector", "")
                if not text:
                    return {"success": False, "error": "مفيش نص"}
                if selector:
                    await page.fill(selector, text)
                else:
                    await page.keyboard.type(text)
                return {"success": True}

            elif tool_name == "browser_read":
                return {"success": True, "text": (await page.inner_text("body"))[:5000],
                        "title": await page.title(), "url": page.url}

            elif tool_name == "screenshot":
                path = f"/tmp/adam_screenshot_{uuid.uuid4().hex[:8]}.png"
                await page.screenshot(path=path, full_page=True)
                return {"success": True, "path": path}
        except Exception as e:
            return {"success": False, "error": str(e)}

        return {"success": False, "error": "أداة متصفح غير معروفة"}

    async def _tool_mouse(self, tool_name: str, params: Dict) -> Dict:
        """أدوات الماوس — xdotool"""
        _ws_bin = "/mnt/Workspace/.local/bin"
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
                    subprocess.run(["xdotool"] + clicks, capture_output=True, timeout=5, env=_env)
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

    async def _tool_keyboard(self, tool_name: str, params: Dict) -> Dict:
        """أدوات الكيبورد — xdotool"""
        _ws_bin = "/mnt/Workspace/.local/bin"
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

    async def _tool_clipboard(self, tool_name: str, params: Dict) -> Dict:
        """أدوات الحافظة — xsel"""
        _ws_bin = "/mnt/Workspace/.local/bin"
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

    async def _tool_screen(self, tool_name: str, params: Dict) -> Dict:
        """أدوات الشاشة — xrandr, import, tesseract"""
        try:
            if tool_name == "screen_info":
                r = subprocess.run(["xrandr"], capture_output=True, text=True, timeout=5)
                return {"success": r.returncode == 0, "data": r.stdout, "error": r.stderr.strip() or ""}

            elif tool_name == "screen_ocr":
                _ws_bin = "/mnt/Workspace/.local/bin"
                _env = {**os.environ, "PATH": f"{_ws_bin}:{os.environ.get('PATH', '')}"}
                shot = f"/tmp/adam_ocr_{uuid.uuid4().hex[:8]}.png"
                r1 = subprocess.run(["import", "-window", "root", shot], capture_output=True, text=True, timeout=10, env=_env)
                if r1.returncode != 0:
                    return {"success": False, "error": f"فشل التصوير: {r1.stderr.strip()}"}
                if not os.path.exists(shot):
                    return {"success": False, "error": "فشل التصوير: ملف مش موجود"}
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

    async def _tool_window(self, tool_name: str, params: Dict) -> Dict:
        """أدوات النوافذ — xdotool, wmctrl"""
        _ws_bin = "/mnt/Workspace/.local/bin"
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

    async def _tool_disk(self, params: Dict) -> Dict:
        """أداة مساحة القرص"""
        try:
            disk_data = {}
            for path in ["/", "/mnt/Workspace"]:
                if os.path.exists(path):
                    usage = subprocess.check_output(["df", "-h", path]).decode().split("\n")[1].split()
                    disk_data[path] = {"size": usage[1], "used": usage[2], "available": usage[3], "used_pct": usage[4]}
            return {"success": True, "disks": disk_data}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _tool_file(self, tool_name: str, params: Dict) -> Dict:
        """أدوات الملفات — read, write, download"""
        import httpx
        try:
            if tool_name == "file_read":
                path = params.get("path", "")
                if not path:
                    return {"success": False, "error": "مفيش مسار"}
                safe = sanitize_path(path)
                if not safe:
                    return {"success": False, "error": "مسار غير مصرح به"}
                if not os.path.isfile(safe):
                    return {"success": False, "error": f"الملف مش موجود: {safe}"}
                max_size = 1024 * 1024
                size = os.path.getsize(safe)
                if size > max_size:
                    return {"success": False, "error": f"الملف كبير جداً ({size//1024}KB). الحد 1MB."}
                with open(safe, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                return {"success": True, "data": content, "path": safe, "size": size}

            elif tool_name == "file_write":
                path = params.get("path", "")
                content = params.get("content", "")
                if not path:
                    return {"success": False, "error": "مفيش مسار"}
                if content is None:
                    return {"success": False, "error": "مفيش محتوى"}
                safe = sanitize_path(path)
                if not safe:
                    return {"success": False, "error": "مسار غير مصرح به"}
                os.makedirs(os.path.dirname(safe) or ".", exist_ok=True)
                with open(safe, "w", encoding="utf-8") as f:
                    f.write(content)
                return {"success": True, "path": safe, "size": len(content)}

            elif tool_name == "file_download":
                url = params.get("url", "")
                if not url:
                    return {"success": False, "error": "مفيش URL"}
                async with httpx.AsyncClient(timeout=15) as hc:
                    r = await hc.get(url, follow_redirects=True)
                    r.raise_for_status()
                    dest = f"/tmp/adam_dl_{uuid.uuid4().hex[:8]}.bin"
                    with open(dest, "wb") as f:
                        f.write(r.content)
                return {"success": True, "path": dest, "size": len(r.content),
                        "content_type": r.headers.get("content-type", ""),
                        "preview": r.text[:200] if "text" in r.headers.get("content-type", "") else "(binary)"}
        except httpx.TimeoutException:
            return {"success": False, "error": "التحميل تجاوز الـ 15 ثانية"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _tool_knowledge(self, params: Dict) -> Dict:
        """البحث في Qdrant — async مع connection pooling"""
        query = params.get("query", "")
        top_k = params.get("top_k", 3)
        if not query:
            return {"success": False, "error": "مفيش query"}
        try:
            from urllib.parse import urlparse
            from qdrant_client import AsyncQdrantClient
            qdrant_url = self.config.get("qdrant_url", "http://localhost:6333")
            pu = urlparse(qdrant_url)
            ollama_base = self.config.get("ollama_base", "http://localhost:11434")

            if not hasattr(self, "_qdrant_client") or self._qdrant_client is None:
                self._qdrant_client = AsyncQdrantClient(
                    host=pu.hostname or "localhost", port=pu.port or 6333
                )
            client = self._qdrant_client

            hc = await self.shared_clients.get("ollama", ollama_base, timeout=10)
            o_resp = await hc.post("/api/embeddings", json={
                "model": "nomic-embed-text", "prompt": query
            })
            o_data = o_resp.json()
            query_vec = o_data.get("embedding")

            collected = []
            if query_vec and len(query_vec) == 768:
                cols = await client.get_collections()
                for col in cols.collections:
                    try:
                        sr = await client.query_points(collection_name=col.name, query=query_vec, limit=top_k)
                        for hit in sr.points:
                            text = (hit.payload or {}).get("text", "")
                            if text:
                                collected.append({"collection": col.name, "text": text, "score": hit.score})
                    except Exception:
                        pass
            if not collected:
                keywords = query.lower().split()
                cols = await client.get_collections()
                for col in cols.collections:
                    try:
                        points = await client.scroll(col.name, limit=200, with_payload=True, with_vectors=False)
                        for pt in points[0]:
                            text = (pt.payload or {}).get("text", "")
                            if text and any(kw in text.lower() for kw in keywords):
                                collected.append({"collection": col.name, "text": text, "score": 0.5})
                    except Exception:
                        pass
            collected.sort(key=lambda x: -x["score"])
            return {"success": True, "results": collected[:top_k], "count": min(len(collected), top_k)}
        except Exception as e:
            return {"success": False, "error": f"قاعدة المعرفة غير متصلة: {e}"}

    async def _tool_preferences(self, tool_name: str, params: Dict) -> Dict:
        """request_permission / check_preferences / notebook_update_profile"""
        if tool_name == "request_permission":
            action = params.get("action", params.get("tool", ""))
            reason = params.get("reason", "")
            level = params.get("level", "once")
            cat = classify_tool(action)
            self.permission.pending_request = {
                "category": cat, "tool": action, "reason": reason,
                "level": level, "tool_params": params.get("params", {}),
                "timestamp": datetime.now().isoformat(),
            }
            log_permission("requested", action, cat, reason, level, "pending")
            return {"success": True, "pending": True, "request_id": self.session_id,
                    "message": f"طلب صلاحية لفئة '{cat}'. المستخدم سيقرر.",
                    "category": cat, "action": action, "reason": reason, "level": level}

        if tool_name == "check_preferences":
            tool = params.get("tool", "")
            category = params.get("category", "")
            if category:
                pred = self.learner.predict(tool, category)
                summary = self.learner.get_summary()
                return {"success": True, "prediction": pred, "category": category,
                        "stats": summary.get(category, {}), "all_preferences": summary}
            return {"success": True, "prediction": "unknown", "all_preferences": self.learner.get_summary()}

        if tool_name == "notebook_update_profile":
            section = params.get("section", "")
            data = params.get("data", {})
            if not section:
                return {"success": False, "error": "مفيش section"}
            if not data:
                return {"success": False, "error": "مفيش بيانات"}
            try:
                notes_dir = "/mnt/Workspace/.local/adam_notebook"
                os.makedirs(notes_dir, exist_ok=True)
                profile_path = os.path.join(notes_dir, "user_profile.json")
                profile = {}
                if os.path.exists(profile_path):
                    with open(profile_path, "r") as f:
                        profile = json.load(f)
                if section not in profile:
                    profile[section] = {}
                profile[section].update(data)
                with open(profile_path, "w") as f:
                    json.dump(profile, f, ensure_ascii=False, indent=2)
                return {"success": True, "message": f"تم تحديث {section}"}
            except Exception as e:
                return {"success": False, "error": str(e)}

        return {"success": False, "error": "أداة تفضيلات غير معروفة"}

    async def _tool_shell(self, tool_name: str, params: Dict) -> Dict:
        """shell command + python execution"""
        if tool_name == "shell":
            command = params.get("command", "")
            if not command:
                return {"success": False, "error": "مفيش أمر"}

            # Expanded blocklist for dangerous commands (Phase 0 emergency security)
            _dangerous = [
                "rm -rf /", "rm -rf /*", "mkfs", "dd if=", "chmod 777", "chmod -R 777",
                "chown root", "chown -R root", ":(){ :|:& };:", "forkbomb",
                "wget ", "curl ", "nc ", "netcat ", "nmap ", "masscan",
                "> /etc/", ">> /etc/", "| bash", "| sh ", "| python3",
                "python3 -c ", "python -c ", "eval ", "exec ",
                "chattr ", "mkswap", "swapoff", "debugfs", "dd of=",
                "fdisk", "parted", "pvcreate", "vgcreate", "lvcreate",
                "modprobe", "insmod", "rmmod", "kmod",
                "iptables", "ufw", "firewall-cmd",
                "passwd", "useradd", "usermod", "userdel", "adduser", "deluser",
                "shutdown", "reboot", "halt", "poweroff", "init ",
                "apt remove", "apt purge", "dpkg --purge", "rpm -e",
                "pacman -R", "yum remove",
            ]
            blocked = [b for b in _dangerous if b in command.lower()]
            if blocked:
                return {"success": False, "error": f"محظور: {blocked[0]}"}

            # Block shell metacharacters that enable injection
            _unsafe_chars = ["`", "$(", "$(", "${", "|&", "&&", "||"]
            for _c in _unsafe_chars:
                if _c in command:
                    return {"success": False, "error": f"رموز غير آمنة: {_c}"}

            try:
                import subprocess as _sp
                # Preferred: use shell=False with shlex.split (safe by default)
                try:
                    import shlex
                    args = shlex.split(command)
                    r = _sp.run(args, capture_output=True, text=True, timeout=30)
                except Exception:
                    # Fallback: shell=True with validated command
                    r = _sp.run(command, shell=True, capture_output=True, text=True, timeout=30)
                output = r.stdout.strip() + ("\n" + r.stderr.strip() if r.stderr.strip() else "")
                with open("/tmp/adam_shell.log", "a") as f:
                    f.write(f"[{datetime.now().isoformat()}] cmd={command} exit={r.returncode}\n")
                return {"success": r.returncode == 0, "output": output, "exit_code": r.returncode}
            except subprocess.TimeoutExpired:
                return {"success": False, "error": "الأمر تجاوز الـ 30 ثانية"}
            except Exception as e:
                return {"success": False, "error": str(e)}

        if tool_name == "python_exec":
            code = params.get("code", "")
            if not code:
                return {"success": False, "error": "مفيش كود"}
            # Block dangerous imports in python_exec
            _blocked_imports = ["import os", "from os ", "import subprocess", "from subprocess",
                               "import shutil", "from shutil ", "import sys", "sys.modules",
                               "__import__(", "exec(", "eval(", "compile(",
                               "open(", "__builtins__", "del ", "__del__"]
            for _bi in _blocked_imports:
                if _bi in code:
                    return {"success": False, "error": f"استيراد غير آمن: {_bi}"}
            try:
                import subprocess as _sp
                r = _sp.run(["python3", "-c", code], capture_output=True, text=True, timeout=30)
                output = r.stdout.strip() + ("\n" + r.stderr.strip() if r.stderr.strip() else "")
                with open("/tmp/adam_python.log", "a") as f:
                    f.write(f"[{datetime.now().isoformat()}] code={code[:100]} exit={r.returncode}\n")
                return {"success": r.returncode == 0, "output": output, "exit_code": r.returncode}
            except subprocess.TimeoutExpired:
                return {"success": False, "error": "الكود تجاوز الـ 30 ثانية"}
            except Exception as e:
                return {"success": False, "error": str(e)}

    async def _tool_memory(self, tool_name: str, params: Dict) -> Dict:
        """الذاكرة الدائمة — store / recall / reflect"""
        try:
            if tool_name == "memory_store":
                content = params.get("content", "")
                tags = params.get("tags", "")
                priority_raw = params.get("priority", 3)
                if isinstance(priority_raw, str):
                    priority_map = {"high": 5, "medium": 3, "low": 1, "critical": 5, "urgent": 5}
                    priority = priority_map.get(priority_raw.strip().lower(), 3)
                else:
                    priority = int(priority_raw)
                priority = min(max(priority, 1), 5)
                if not content:
                    return {"success": False, "error": "مفيش محتوى للحفظ"}
                mem_id = memory_store.store(content, tags, priority)
                return {"success": True, "memory_id": mem_id, "message": "تم الحفظ"}

            elif tool_name == "memory_recall":
                query = params.get("query", "")
                limit = min(max(int(params.get("limit", 10)), 1), 50)
                if not query:
                    return {"success": False, "error": "مفيش استعلام بحث"}
                memories = memory_store.search(query, limit)
                return {"success": True, "count": len(memories), "memories": memories}

            elif tool_name == "memory_reflect":
                days = int(params.get("days", 1))
                reflection = memory_store.reflect(min(max(days, 1), 30))
                return {"success": True, "reflection": reflection, "stats": memory_store.stats()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _tool_planning(self, params: Dict) -> Dict:
        """أداة التخطيط — CRUD للمهام"""
        action = params.get("action", "list")
        todo_file = "/mnt/Workspace/adam_v8_output/todo_list.json"
        result = {"success": True, "action": action}
        try:
            from pathlib import Path as _Path
            _todo_path = _Path(todo_file)
            todos = json.loads(_todo_path.read_text(encoding='utf-8')) if _todo_path.exists() else []

            if action == "list":
                status = params.get("status")
                filtered = [t for t in todos if not status or t.get("status") == status]
                result["todos"] = filtered; result["total"] = len(todos); result["filtered"] = len(filtered)

            elif action == "create":
                task = {"id": str(uuid.uuid4())[:8], "title": params.get("title", "مهمة جديدة"),
                        "description": params.get("description", ""), "priority": params.get("priority", "medium"),
                        "status": "pending", "due_date": params.get("due_date", ""),
                        "tags": params.get("tags", []), "created_at": datetime.now().isoformat(),
                        "updated_at": datetime.now().isoformat()}
                todos.append(task)
                _todo_path.write_text(json.dumps(todos, ensure_ascii=False, indent=2), encoding='utf-8')
                result["task"] = task; result["message"] = f"تم إضافة المهمة: {task['title']}"

            elif action == "update":
                task_id = params.get("id")
                for t in todos:
                    if t["id"] == task_id:
                        for k in ["title", "description", "priority", "status", "due_date", "tags"]:
                            if k in params: t[k] = params[k]
                        t["updated_at"] = datetime.now().isoformat()
                        _todo_path.write_text(json.dumps(todos, ensure_ascii=False, indent=2), encoding='utf-8')
                        result["task"] = t; result["message"] = f"تم تحديث المهمة: {t['title']}"
                        break
                else:
                    return {"success": False, "error": "المهمة مش موجودة"}

            elif action == "delete":
                task_id = params.get("id")
                before = len(todos)
                todos = [t for t in todos if t["id"] != task_id]
                if len(todos) < before:
                    _todo_path.write_text(json.dumps(todos, ensure_ascii=False, indent=2), encoding='utf-8')
                    result["message"] = f"تم حذف المهمة {task_id}"
                else:
                    return {"success": False, "error": "المهمة مش موجودة"}

            elif action == "plan":
                tasks_created = []
                for task_data in params.get("tasks", []):
                    task = {"id": str(uuid.uuid4())[:8], "title": task_data.get("title", "مهمة جديدة"),
                            "description": task_data.get("description", ""), "priority": task_data.get("priority", "medium"),
                            "status": "pending", "due_date": task_data.get("due_date", ""),
                            "tags": task_data.get("tags", []), "created_at": datetime.now().isoformat(),
                            "updated_at": datetime.now().isoformat()}
                    todos.append(task); tasks_created.append(task)
                _todo_path.write_text(json.dumps(todos, ensure_ascii=False, indent=2), encoding='utf-8')
                result["tasks"] = tasks_created; result["message"] = f"تم إنشاء {len(tasks_created)} مهمة في الخطة"
            else:
                return {"success": False, "error": f"أمر غير معروف: {action}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
        return result
