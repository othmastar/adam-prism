"""i18n — Bilingual message catalog (Arabic primary, English secondary).

Usage:
    from adam.i18n import t
    msg = t("chat.welcome")  # returns localized string
"""
from __future__ import annotations

import os
from typing import Literal

Locale = Literal["ar", "en"]

# [PHASE7] Core message catalog
# Convention: keys are dot-separated namespaces
# All Arabic strings use modern standard + natural phrasing
_CATALOG: dict[str, dict[str, str]] = {
    # ── Chat ──────────────────────────────────────────────────────
    "chat.welcome": {
        "ar": "أهلاً بيك. أنا آدم المنظار، اسمعك.",
        "en": "Welcome. I'm Adam Prism, listening.",
    },
    "chat.empty_message": {
        "ar": "ابعتلي رسالة يلا.",
        "en": "Send me a message.",
    },
    "chat.processing": {
        "ar": "بفكر…",
        "en": "Thinking…",
    },
    "chat.tool_blocked_by_ethics": {
        "ar": "الطلب ده مش هيتم — مش متوافق مع البوابة الأخلاقية.",
        "en": "Request blocked — ethics gate rejected it.",
    },
    "chat.tool_blocked_by_security": {
        "ar": "الحارس الأمني رفض الطلب ده.",
        "en": "Security guard rejected this request.",
    },
    "chat.error_generic": {
        "ar": "حصل خطأ. جرّب تاني أو ابعت التفاصيل لمحمد عثمان.",
        "en": "Something went wrong. Try again or send details to Mohamed Othman.",
    },
    # ── Memory ────────────────────────────────────────────────────
    "memory.stored": {
        "ar": "اتسجلت في الذاكرة الطويلة المدى.",
        "en": "Stored in long-term memory.",
    },
    "memory.not_found": {
        "ar": "مش لاقي حاجة في الذاكرة.",
        "en": "Nothing found in memory.",
    },
    "memory.cleared": {
        "ar": "اتمسحت الذاكرة المؤقتة.",
        "en": "Short-term memory cleared.",
    },
    # ── Auth ──────────────────────────────────────────────────────
    "auth.unauthorized": {
        "ar": "لازم تعمل login الأول.",
        "en": "Authentication required.",
    },
    "auth.invalid_token": {
        "ar": "التوكن مش صحيح أو انتهت صلاحيته.",
        "en": "Token invalid or expired.",
    },
    "auth.forbidden": {
        "ar": "مش مسموحلك تعمل ده.",
        "en": "Permission denied.",
    },
    "auth.login_success": {
        "ar": "اتسجلت بنجاح.",
        "en": "Logged in successfully.",
    },
    # ── WAF ───────────────────────────────────────────────────────
    "waf.blocked": {
        "ar": "الطلب اتمنع بواسطة الـ WAF — {reason}",
        "en": "Request blocked by WAF — {reason}",
    },
    "waf.logged": {
        "ar": "الطلب اتسجل في الـ WAF log — {reason}",
        "en": "Request logged by WAF — {reason}",
    },
    # ── Voice ─────────────────────────────────────────────────────
    "voice.voice_not_found": {
        "ar": "الصوت ده مش موجود.",
        "en": "Voice not found.",
    },
    "voice.cloned": {
        "ar": "اتعمل voice clone بنجاح — ID: {voice_id}",
        "en": "Voice cloned successfully — ID: {voice_id}",
    },
    # ── Tenant ────────────────────────────────────────────────────
    "tenant.not_found": {
        "ar": "الـ tenant ده مش موجود.",
        "en": "Tenant not found.",
    },
    "tenant.quota_exceeded": {
        "ar": "اتعديت الـ quota الشهري.",
        "en": "Monthly quota exceeded.",
    },
    # ── System ────────────────────────────────────────────────────
    "system.starting": {
        "ar": "آدم بيصحى…",
        "en": "Adam is waking up…",
    },
    "system.ready": {
        "ar": "آدم جاهز. {routes} endpoint شغالين.",
        "en": "Adam ready. {routes} endpoints live.",
    },
    "system.shutting_down": {
        "ar": "آدم بيقفل بهدوء…",
        "en": "Adam shutting down gracefully…",
    },
}

_current: Locale = "ar"


def set_locale(loc: str) -> None:
    """Set the active locale. Accepts 'ar' or 'en' (default: env ADAM_LOCALE or 'ar')."""
    global _current
    if loc in ("ar", "en"):
        _current = loc  # type: ignore[assignment]
    else:
        _current = "en"


def get_locale() -> Locale:
    """Get active locale, falling back to env var or 'ar'."""
    env = os.getenv("ADAM_LOCALE", "ar").lower()
    if env in ("ar", "en"):
        return env  # type: ignore[return-value]
    return "ar"


def t(key: str, /, **kwargs) -> str:
    """Translate a message key. Falls back to English, then to the key itself.

    Usage:
        t("chat.welcome")                          # localized string
        t("waf.blocked", reason="SQL injection")   # with substitution
    """
    if not isinstance(key, str) or "." not in key:
        return key

    # Explicit global state first, then env var
    loc = _current if _current else get_locale()
    entry = _CATALOG.get(key)
    if not entry:
        return key

    msg = entry.get(loc) or entry.get("en") or key
    if kwargs:
        try:
            return msg.format(**kwargs)
        except (KeyError, IndexError):
            return msg
    return msg


def available_keys() -> list[str]:
    """Return all registered translation keys (useful for audits / docs)."""
    return sorted(_CATALOG.keys())


def register(key: str, ar: str, en: str) -> None:
    """Register a new translation. Used by domain modules to extend the catalog."""
    _CATALOG[key] = {"ar": ar, "en": en}
