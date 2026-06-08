"""
Adam Prism — Browser Automation (Eyes)
========================================
أتمتة المتصفح عبر Playwright Firefox.
"""

import os
import logging
import asyncio
from typing import Optional, Dict, Any

logger = logging.getLogger("adam_prism.eyes")


class Browser:
    """التحكم في المتصفح — Playwright Firefox"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self._playwright = None
        self._browser = None
        self._page = None
        self._healthy = False
        self._browsers_path = self.config.get(
            "browsers_path",
            "/mnt/Workspace/.local/ms-playwright"
        )

    async def initialize(self):
        """تشغيل المتصفح"""
        if self._healthy:
            return True
        try:
            from playwright.async_api import async_playwright
            os.environ["PLAYWRIGHT_BROWSERS_PATH"] = self._browsers_path
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.firefox.launch(headless=True)
            self._page = await self._browser.new_page()
            self._healthy = True
            logger.info("✅ Browser initialized")
            return True
        except ImportError:
            logger.warning("⚠️ playwright غير مثبت — شغّل: pip install playwright && playwright install firefox")
            return False
        except Exception as e:
            logger.error(f"❌ Browser init failed: {e}")
            return False

    async def is_healthy(self) -> bool:
        if not self._healthy:
            return False
        try:
            await asyncio.wait_for(self._page.evaluate("1"), timeout=5)
            return True
        except Exception:
            self._healthy = False
            return False

    async def restart(self):
        """إعادة تشغيل المتصفح"""
        await self.close()
        await self.initialize()

    async def close(self):
        """إغلاق المتصفح"""
        self._healthy = False
        try:
            if self._page:
                await self._page.close()
        except Exception:
            pass
        try:
            if self._browser:
                await self._browser.close()
        except Exception:
            pass
        try:
            if self._playwright:
                await self._playwright.stop()
        except Exception:
            pass
        self._page = None
        self._browser = None
        self._playwright = None

    async def open(self, url: str) -> Dict:
        if not self._healthy:
            return {"success": False, "error": "Browser not initialized"}
        try:
            await self._page.goto(url, timeout=30000, wait_until="domcontentloaded")
            title = await self._page.title()
            return {"success": True, "title": title, "url": self._page.url}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def fetch(self, url: str) -> Dict:
        if not self._healthy:
            return {"success": False, "error": "Browser not initialized"}
        try:
            await self._page.goto(url, timeout=30000, wait_until="domcontentloaded")
            text = await self._page.inner_text("body")
            title = await self._page.title()
            return {
                "success": True, "url": self._page.url, "title": title,
                "data": text[:5000]
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def click(self, selector: str) -> Dict:
        if not self._healthy:
            return {"success": False, "error": "Browser not initialized"}
        try:
            await self._page.click(selector, timeout=10000)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def type_text(self, selector: str, text: str) -> Dict:
        if not self._healthy:
            return {"success": False, "error": "Browser not initialized"}
        try:
            if selector:
                await self._page.fill(selector, text)
            else:
                await self._page.keyboard.type(text)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def read(self) -> Dict:
        if not self._healthy:
            return {"success": False, "error": "Browser not initialized"}
        try:
            text = await self._page.inner_text("body")
            title = await self._page.title()
            return {"success": True, "text": text[:5000], "title": title, "url": self._page.url}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def screenshot(self) -> Dict:
        if not self._healthy:
            return {"success": False, "error": "Browser not initialized"}
        try:
            import uuid
            path = f"/tmp/adam_screenshot_{uuid.uuid4().hex[:8]}.png"
            await self._page.screenshot(path=path, full_page=True)
            return {"success": True, "path": path}
        except Exception as e:
            return {"success": False, "error": str(e)}
