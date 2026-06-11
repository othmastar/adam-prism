"""أدوات المتصفح — Playwright Firefox"""

import os
import uuid
from typing import Dict


class BrowserToolsMixin:
    """Mixin: browser tools — open, fetch, click, type, read, screenshot"""

    async def _tool_browser(self, tool_name: str, params: Dict) -> Dict:
        try:
            from playwright.async_api import async_playwright
            os.environ["PLAYWRIGHT_BROWSERS_PATH"] = self.config.get(
                "playwright_browsers_path",
                os.path.expanduser("~/.local/ms-playwright")
            )
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
