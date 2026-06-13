"""
أدوات المتصفح — Playwright Firefox — HARDENED v2
====================================================

[FIX v2 — HIGH SECURITY]
- Added SSRF (Server-Side Request Forgery) protection
- Blocks private IPs, localhost, link-local addresses
- Validates URLs before any browser navigation
- Prevents access to internal network addresses
"""

import ipaddress
import os
import uuid
from urllib.parse import urlparse

# ═══════════════════════════════════════════════════════
# [NEW v2] SSRF Protection — منع الوصول للشبكة الداخلية
# ═══════════════════════════════════════════════════════

def _is_private_ip(hostname: str) -> bool:
    """فحص هل الـ hostname يرجع لعنوان IP خاص أو داخلي"""
    try:
        # محاولة تحويل الـ hostname لعنوان IP مباشرة
        ip = ipaddress.ip_address(hostname)
        return (
            ip.is_private or
            ip.is_loopback or
            ip.is_link_local or
            ip.is_reserved or
            ip.is_multicast or
            ip.is_unspecified
        )
    except ValueError:
        # الـ hostname مش عنوان IP — ممكن يكون اسم نطاق
        pass

    # فحص أسماء المضيفين المحلية
    localhost_names = {
        "localhost", "localhost.localdomain",
        "127.0.0.1", "0.0.0.0", "::1",
        "host.docker.internal", "host.internal",
    }
    if hostname.lower() in localhost_names:
        return True

    # فحص النطاقات الداخلية
    internal_suffixes = (".local", ".internal", ".localhost", ".docker", ".container")
    return bool(any(hostname.lower().endswith(s) for s in internal_suffixes))


def _validate_url(url: str) -> dict:
    """التحقق من صحة وأمان URL — منع SSRF"""
    if not url:
        return {"valid": False, "error": "مفيش URL"}

    try:
        parsed = urlparse(url)
    except Exception:
        return {"valid": False, "error": f"URL غير صالح: {url}"}

    # التحقق من البروتوكول
    if parsed.scheme not in ("http", "https"):
        return {"valid": False, "error": f"بروتوكول غير مسموح: {parsed.scheme} — يُسمح بـ http و https فقط"}

    # التحقق من وجود hostname
    hostname = parsed.hostname
    if not hostname:
        return {"valid": False, "error": "URL بدون hostname"}

    # التحقق من إن الـ hostname مش عنوان خاص
    if _is_private_ip(hostname):
        return {
            "valid": False,
            "error": f"SSRF محظور: لا يمكن الوصول لعناوين الشبكة الداخلية ({hostname})"
        }

    return {"valid": True}


class BrowserToolsMixin:
    """Mixin: browser tools — open, fetch, click, type, read, screenshot"""

    async def _tool_browser(self, tool_name: str, params: dict) -> dict:
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
                # [FIX v2] SSRF protection
                validation = _validate_url(url)
                if not validation["valid"]:
                    return {"success": False, "error": validation["error"]}
                await page.goto(url, timeout=30000, wait_until="domcontentloaded")
                return {"success": True, "title": await page.title(), "url": page.url}

            elif tool_name == "browser_fetch":
                url = params.get("url", "")
                # [FIX v2] SSRF protection
                validation = _validate_url(url)
                if not validation["valid"]:
                    return {"success": False, "error": validation["error"]}
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

    async def _browser_cleanup(self):
        """[M8] Properly close Playwright resources to prevent resource leaks."""
        try:
            if hasattr(self, '_pw_page') and self._pw_page is not None:
                await self._pw_page.close()
                self._pw_page = None
        except Exception as e:
            import logging
            logging.getLogger("adam_prism.core").warning(f"Error closing browser page: {e}")
        try:
            if hasattr(self, '_pw_browser') and self._pw_browser is not None:
                await self._pw_browser.close()
                self._pw_browser = None
        except Exception as e:
            import logging
            logging.getLogger("adam_prism.core").warning(f"Error closing browser: {e}")
        try:
            if hasattr(self, '_pw_playwright') and self._pw_playwright is not None:
                await self._pw_playwright.stop()
                self._pw_playwright = None
        except Exception as e:
            import logging
            logging.getLogger("adam_prism.core").warning(f"Error stopping playwright: {e}")
