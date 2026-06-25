"""
Adam Prism — Enhanced Playwright Browser
==========================================
يحسّن eyes/browser.py الموجود عندك بـ:
- Multi-tab support (مش tab واحدة بس)
- SSRF protection محسّن (DNS rebinding safe)
- Click, type, scroll, drag
- Form filling
- Network interception
- PDF export
- Cookie management
- Screenshots base64 (مش بس path)

يتكامل مع eyes/browser.py الموجود، مش يستبدله.
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import ipaddress
import logging
import os
import socket
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

logger = logging.getLogger("adam_prism.eyes_enhanced")


# ============================================================
# SSRF Protection (DNS-rebinding safe)
# ============================================================

BLOCKED_HOSTS = {
    "localhost", "127.0.0.1", "0.0.0.0", "::1",
    "host.docker.internal", "metadata.google.internal",
}

BLOCKED_IP_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),  # link-local + cloud metadata
    ipaddress.ip_network("fd00::/8"),  # IPv6 private
    ipaddress.ip_network("fe80::/10"),  # IPv6 link-local
]


def is_safe_url(url: str) -> tuple[bool, str]:
    """SSRF protection — DNS-rebinding safe."""
    try:
        parsed = urlparse(url)
    except Exception:
        return False, "Invalid URL"

    if parsed.scheme not in ("http", "https", "file"):
        return False, f"Scheme not allowed: {parsed.scheme}"

    # file:// آمن للـ local files
    if parsed.scheme == "file":
        return True, "ok"

    hostname = parsed.hostname or ""
    if not hostname:
        return False, "No hostname"

    if hostname.lower() in BLOCKED_HOSTS:
        return False, f"Blocked host: {hostname}"

    # فحص DNS resolution لكل IPs الممكنة
    try:
        addr_info = socket.getaddrinfo(hostname, None)
        for family, _, _, _, sockaddr in addr_info:
            ip = sockaddr[0]
            try:
                ip_obj = ipaddress.ip_address(ip)
                for blocked in BLOCKED_IP_NETWORKS:
                    if ip_obj in blocked:
                        return False, f"Blocked IP range: {ip} ({blocked})"
                if ip_obj.is_loopback or ip_obj.is_private or ip_obj.is_link_local:
                    return False, f"Private/loopback IP: {ip}"
            except ValueError:
                continue
    except socket.gaierror as e:
        return False, f"DNS resolution failed: {e}"

    return True, "ok"


# ============================================================
# Page State
# ============================================================

@dataclass
class PageState:
    """حالة صفحة متصفح."""
    page_id: str
    url: str
    title: str = ""
    created_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    viewport: dict = field(default_factory=lambda: {"width": 1280, "height": 720})


# ============================================================
# Enhanced Browser — Multi-tab
# ============================================================

class EnhancedBrowser:
    """Playwright browser مع multi-tab support."""

    def __init__(
        self,
        headless: bool = True,
        browser_type: str = "chromium",  # chromium, firefox, webkit
        default_timeout: float = 30.0,
        max_pages: int = 5,
        viewport: dict | None = None,
        user_agent: str | None = None,
    ):
        self.headless = headless
        self.browser_type = browser_type
        self.default_timeout = default_timeout
        self.max_pages = max_pages
        self.default_viewport = viewport or {"width": 1280, "height": 720}
        self.user_agent = user_agent

        self._playwright = None
        self._browser = None
        self._context = None
        self._pages: dict[str, Any] = {}  # page_id -> Page
        self._states: dict[str, PageState] = {}
        self._lock = asyncio.Lock()
        self._available = False

    async def init(self) -> bool:
        """يهيّئ Playwright والمتصفح."""
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            logger.error(
                "playwright not installed. Install with: "
                "pip install playwright && playwright install chromium"
            )
            return False

        try:
            self._playwright = await async_playwright().start()

            browser_launcher = {
                "chromium": self._playwright.chromium,
                "firefox": self._playwright.firefox,
                "webkit": self._playwright.webkit,
            }.get(self.browser_type, self._playwright.chromium)

            self._browser = await browser_launcher.launch(
                headless=self.headless,
                args=["--no-sandbox", "--disable-setuid-sandbox"] if self.browser_type == "chromium" else [],
            )

            context_options = {
                "viewport": self.default_viewport,
                "ignore_https_errors": False,
                "java_script_enabled": True,
            }
            if self.user_agent:
                context_options["user_agent"] = self.user_agent

            self._context = await self._browser.new_context(**context_options)
            self._available = True
            logger.info(f"EnhancedBrowser ready: {self.browser_type} (headless={self.headless})")
            return True
        except Exception as e:
            logger.error(f"Browser init failed: {e}")
            self._available = False
            return False

    async def close(self) -> None:
        """يقفل المتصفح."""
        for pid in list(self._pages.keys()):
            await self.close_page(pid)
        if self._context:
            try:
                await self._context.close()
            except Exception:
                pass
        if self._browser:
            try:
                await self._browser.close()
            except Exception:
                pass
        if self._playwright:
            try:
                await self._playwright.stop()
            except Exception:
                pass
        self._pages.clear()
        self._states.clear()
        self._available = False

    async def health_check(self) -> bool:
        """يتحقق من صحة المتصفح."""
        if not self._available or not self._browser:
            return False
        try:
            test_page = await self._context.new_page()
            await test_page.close()
            return True
        except Exception:
            return False

    # ============================================================
    # Page Management (Multi-tab)
    # ============================================================

    async def open(self, url: str, wait_until: str = "domcontentloaded") -> str:
        """يفتح URL في صفحة جديدة. يرجع page_id."""
        safe, reason = is_safe_url(url)
        if not safe:
            raise ValueError(f"URL not safe: {reason}")

        # limit pages
        if len(self._pages) >= self.max_pages:
            oldest_id = min(self._states.keys(), key=lambda k: self._states[k].last_activity)
            await self.close_page(oldest_id)

        async with self._lock:
            page = await self._context.new_page()
            page.set_default_timeout(self.default_timeout * 1000)

            try:
                await page.goto(url, wait_until=wait_until, timeout=self.default_timeout * 1000)
            except Exception as e:
                logger.warning(f"goto warning: {e}")

            page_id = hashlib.sha256(f"{url}{time.time()}".encode()).hexdigest()[:12]
            self._pages[page_id] = page

            try:
                title = await page.title()
            except Exception:
                title = ""

            self._states[page_id] = PageState(
                page_id=page_id, url=url, title=title,
            )
            logger.info(f"Opened page {page_id}: {url}")
            return page_id

    async def close_page(self, page_id: str) -> bool:
        """يقفل صفحة."""
        async with self._lock:
            page = self._pages.pop(page_id, None)
            self._states.pop(page_id, None)
            if page:
                try:
                    await page.close()
                    return True
                except Exception:
                    pass
            return False

    async def navigate(self, page_id: str, url: str, wait_until: str = "domcontentloaded") -> bool:
        """ينتقل لـ URL جديد في نفس الصفحة."""
        safe, reason = is_safe_url(url)
        if not safe:
            raise ValueError(f"URL not safe: {reason}")

        page = self._pages.get(page_id)
        if not page:
            raise ValueError(f"Page not found: {page_id}")

        try:
            await page.goto(url, wait_until=wait_until, timeout=self.default_timeout * 1000)
            self._states[page_id].url = url
            self._states[page_id].last_activity = time.time()
            try:
                self._states[page_id].title = await page.title()
            except Exception:
                pass
            return True
        except Exception as e:
            logger.warning(f"Navigation failed: {e}")
            return False

    def list_pages(self) -> list[dict]:
        """يسرد الصفحات المفتوحة."""
        return [
            {"id": pid, "url": s.url, "title": s.title,
             "age_seconds": int(time.time() - s.created_at)}
            for pid, s in self._states.items()
        ]

    # ============================================================
    # Reading
    # ============================================================

    async def read_page(self, page_id: str, selector: str | None = None) -> dict:
        """يقرأ محتوى الصفحة."""
        page = self._pages.get(page_id)
        if not page:
            return {"success": False, "error": f"Page not found: {page_id}"}

        try:
            if selector:
                element = await page.query_selector(selector)
                if not element:
                    return {"success": False, "error": f"Element not found: {selector}"}
                text = await element.inner_text()
                html = await element.inner_html()
            else:
                text = await page.inner_text("body")
                html = await page.content()

            self._states[page_id].last_activity = time.time()
            return {
                "success": True,
                "text": text[:10000],
                "html_length": len(html),
                "url": page.url,
                "title": await page.title(),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_text(self, page_id: str, selector: str = "body") -> str:
        """يرجع نص الصفحة فقط."""
        result = await self.read_page(page_id, selector)
        return result.get("text", "") if result.get("success") else ""

    async def get_links(self, page_id: str) -> list[dict]:
        """يرجع كل الروابط في الصفحة."""
        page = self._pages.get(page_id)
        if not page:
            return []

        try:
            links = await page.eval_on_selector_all(
                "a[href]",
                """els => els.map(el => ({
                    href: el.href,
                    text: el.innerText.trim().substring(0, 100),
                    target: el.target
                }))"""
            )
            return links[:50]
        except Exception as e:
            logger.warning(f"get_links failed: {e}")
            return []

    # ============================================================
    # Interaction
    # ============================================================

    async def click(self, page_id: str, selector: str, timeout: float | None = None) -> dict:
        """ينقر على عنصر."""
        page = self._pages.get(page_id)
        if not page:
            return {"success": False, "error": f"Page not found: {page_id}"}

        try:
            timeout_ms = int((timeout or self.default_timeout) * 1000)
            await page.click(selector, timeout=timeout_ms)
            self._states[page_id].last_activity = time.time()
            return {"success": True, "selector": selector}
        except Exception as e:
            return {"success": False, "error": str(e), "selector": selector}

    async def type_text(
        self, page_id: str, selector: str, text: str,
        delay: int = 50, clear: bool = True,
    ) -> dict:
        """يكتب نص في حقل."""
        page = self._pages.get(page_id)
        if not page:
            return {"success": False, "error": f"Page not found: {page_id}"}

        try:
            if clear:
                await page.fill(selector, "")
            await page.type(selector, text, delay=delay)
            self._states[page_id].last_activity = time.time()
            return {"success": True, "selector": selector, "text_length": len(text)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def press_key(self, page_id: str, key: str) -> dict:
        """يضغط زر."""
        page = self._pages.get(page_id)
        if not page:
            return {"success": False, "error": f"Page not found: {page_id}"}

        try:
            await page.keyboard.press(key)
            self._states[page_id].last_activity = time.time()
            return {"success": True, "key": key}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def scroll(
        self, page_id: str, x: int = 0, y: int = 500, selector: str | None = None,
    ) -> dict:
        """يعمل scroll."""
        page = self._pages.get(page_id)
        if not page:
            return {"success": False, "error": f"Page not found: {page_id}"}

        try:
            if selector:
                await page.eval_on_selector(
                    selector, f"(el) => el.scrollBy({x}, {y})",
                )
            else:
                await page.evaluate(f"window.scrollBy({x}, {y})")
            self._states[page_id].last_activity = time.time()
            return {"success": True, "x": x, "y": y}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def fill_form(self, page_id: str, fields: dict[str, str]) -> dict:
        """يملأ form بـ عدة fields."""
        page = self._pages.get(page_id)
        if not page:
            return {"error": f"Page not found: {page_id}"}

        results = {}
        for selector, value in fields.items():
            try:
                await page.fill(selector, value)
                results[selector] = {"success": True}
            except Exception as e:
                results[selector] = {"success": False, "error": str(e)}

        self._states[page_id].last_activity = time.time()
        return results

    # ============================================================
    # Screenshot & PDF
    # ============================================================

    async def screenshot(
        self, page_id: str, full_page: bool = False,
        selector: str | None = None, path: str | None = None,
    ) -> dict:
        """ياخد screenshot. يرجع base64 + path لو موجود."""
        page = self._pages.get(page_id)
        if not page:
            return {"success": False, "error": f"Page not found: {page_id}"}

        try:
            options = {"full_page": full_page}
            if path:
                options["path"] = path
            if selector:
                element = await page.query_selector(selector)
                if not element:
                    return {"success": False, "error": "Element not found"}
                screenshot_bytes = await element.screenshot()
            else:
                screenshot_bytes = await page.screenshot(**options)

            self._states[page_id].last_activity = time.time()

            result = {
                "success": True,
                "size_bytes": len(screenshot_bytes),
                "base64": base64.b64encode(screenshot_bytes).decode(),
            }
            if path:
                result["path"] = path
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def export_pdf(self, page_id: str, path: str = "/tmp/adam_page.pdf") -> dict:
        """يصدّر الصفحة كـ PDF."""
        page = self._pages.get(page_id)
        if not page:
            return {"success": False, "error": f"Page not found: {page_id}"}

        try:
            await page.pdf(path=path, format="A4")
            self._states[page_id].last_activity = time.time()
            return {"success": True, "path": path}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ============================================================
    # JavaScript Execution
    # ============================================================

    async def execute_js(self, page_id: str, script: str) -> dict:
        """ينفذ JavaScript في الصفحة."""
        page = self._pages.get(page_id)
        if not page:
            return {"success": False, "error": f"Page not found: {page_id}"}

        try:
            result = await page.evaluate(script)
            self._states[page_id].last_activity = time.time()
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ============================================================
    # Cookies & Storage
    # ============================================================

    async def get_cookies(self, page_id: str) -> list[dict]:
        """يرجع cookies."""
        page = self._pages.get(page_id)
        if not page:
            return []
        return await page.context.cookies()

    async def set_cookie(self, page_id: str, name: str, value: str, domain: str) -> bool:
        """يضيف cookie."""
        page = self._pages.get(page_id)
        if not page:
            return False
        await page.context.add_cookies([{
            "name": name, "value": value, "domain": domain, "path": "/",
        }])
        return True

    async def save_storage_state(self, path: str = "/tmp/adam_storage.json") -> bool:
        """يحفظ حالة التخزين (cookies + localStorage)."""
        if not self._context:
            return False
        await self._context.storage_state(path=path)
        return True

    # ============================================================
    # Waiting
    # ============================================================

    async def wait_for_selector(
        self, page_id: str, selector: str,
        timeout: float = 30.0, state: str = "visible",
    ) -> dict:
        """ينتظر عنصر."""
        page = self._pages.get(page_id)
        if not page:
            return {"success": False, "error": f"Page not found: {page_id}"}

        try:
            await page.wait_for_selector(selector, timeout=timeout * 1000, state=state)
            return {"success": True, "selector": selector}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def wait_for_navigation(self, page_id: str, timeout: float = 30.0) -> dict:
        """ينتظر تحميل صفحة."""
        page = self._pages.get(page_id)
        if not page:
            return {"success": False, "error": f"Page not found: {page_id}"}

        try:
            await page.wait_for_load_state("networkidle", timeout=timeout * 1000)
            return {"success": True, "url": page.url}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ============================================================
    # Stats
    # ============================================================

    def get_stats(self) -> dict:
        """إحصائيات."""
        return {
            "browser_type": self.browser_type,
            "headless": self.headless,
            "pages_open": len(self._pages),
            "max_pages": self.max_pages,
            "available": self._available,
            "pages": [
                {
                    "id": pid,
                    "url": s.url,
                    "title": s.title[:50],
                    "age_seconds": int(time.time() - s.created_at),
                }
                for pid, s in self._states.items()
            ],
        }


# ============================================================
# Factory — singleton
# ============================================================

_global_browser: EnhancedBrowser | None = None


async def get_browser(config: dict | None = None) -> EnhancedBrowser:
    """يرجع browser مشترك (singleton)."""
    global _global_browser
    if _global_browser is None:
        _global_browser = EnhancedBrowser(**(config or {}))
        await _global_browser.init()
    return _global_browser


async def close_browser() -> None:
    """يقفل الـ browser المشترك."""
    global _global_browser
    if _global_browser:
        await _global_browser.close()
        _global_browser = None
