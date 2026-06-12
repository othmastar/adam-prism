"""
Adam Prism — Pydantic Settings
=================================
إعدادات التطبيق مع التحقق من القيم ودعم متغيرات البيئة.

Application settings using Pydantic BaseSettings with validation,
environment variable support, and .env file loading.

المميزات / Features:
  - تحميل من .env أو متغيرات البيئة — Load from .env or env vars
  - التحقق من القيم في الإنتاج — Production validation
  - إعدادات كل موديول — Per-module configuration
  - إعدادات الأمن وتحديد المعدل — Security & rate limit config
  - أعلام تفعيل/تعطيل الموديولات — Module enable/disable flags
"""

from __future__ import annotations

import os
import warnings
from typing import Any, Dict, List, Optional

try:
    from pydantic_settings import BaseSettings
    from pydantic import Field, field_validator, model_validator
except ImportError:
    # توافق مع الإصدارات القديمة — Compatibility with older pydantic
    try:
        from pydantic import BaseSettings, Field, validator as field_validator, root_validator as model_validator
    except ImportError:
        from pydantic import Field
        # إنشاء BaseSettings بسيط كبديل — Simple BaseSettings fallback
        class BaseSettings:  # type: ignore
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)

            class Config:
                env_file = ".env"

            def model_dump(self):
                return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}


# ═══════════════════════════════════════════════════════════════
# Adam Settings
# ═══════════════════════════════════════════════════════════════

class AdamSettings(BaseSettings):
    """
    إعدادات آدم بريزم — Adam Prism application settings.

    تُحمَّل القيم من:
    1. متغيرات البيئة (الأولوية القصوى) — Environment variables (highest priority)
    2. ملف .env — .env file
    3. القيم الافتراضية — Default values

    الاستخدام / Usage:
        settings = AdamSettings()
        print(settings.api_key)
        print(settings.model_name)
    """

    # ─────────────────────────────────────────────
    # البيئة / Environment
    # ─────────────────────────────────────────────

    ADAM_ENVIRONMENT: str = Field(
        default="development",
        description="بيئة التشغيل — Environment (development/staging/production)",
    )

    ADAM_PRODUCTION: bool = Field(
        default=False,
        description="هل هذا إنتاج؟ — Is this production?",
    )

    # ─────────────────────────────────────────────
    # النموذج والمزود / Model & Provider
    # ─────────────────────────────────────────────

    ollama_base: str = Field(
        default="http://localhost:11434",
        description="عنوان Ollama — Ollama base URL",
    )

    model_name: str = Field(
        default="adam-prism-v13:latest",
        description="اسم النموذج — Model name",
    )

    inference_mode: str = Field(
        default="lora",
        description="وضع الاستدلال — Inference mode (lora/ollama/openai/anthropic)",
    )

    lora_server_url: str = Field(
        default="http://localhost:7861",
        description="عنوان خادم LoRA — LoRA server URL",
    )

    context_window: int = Field(
        default=4096,
        description="نافذة السياق — Context window size",
    )

    token_budget: int = Field(
        default=4000,
        description="ميزانية الرموز — Token budget per request",
    )

    # ─────────────────────────────────────────────
    # الذاكرة / Memory
    # ─────────────────────────────────────────────

    qdrant_url: str = Field(
        default="http://localhost:6333",
        description="عنوان Qdrant — Qdrant URL",
    )

    embedding_model: str = Field(
        default="nomic-embed-text",
        description="نموذج التضمين — Embedding model name",
    )

    # ─────────────────────────────────────────────
    # API / واجهة البرمجة
    # ─────────────────────────────────────────────

    api_host: str = Field(
        default="0.0.0.0",
        description="عنوان الاستماع — API listen host",
    )

    api_port: int = Field(
        default=8000,
        description="منفذ API — API listen port",
    )

    api_key: str = Field(
        default="CHANGE_ME_IN_PRODUCTION",
        description="مفتاح API — API key for authentication",
    )

    admin_key: str = Field(
        default="CHANGE_ME_ADMIN_KEY",
        description="مفتاح المسؤول — Admin key for privileged operations",
    )

    web_port: int = Field(
        default=3000,
        description="منفذ الويب — Web UI port",
    )

    # ─────────────────────────────────────────────
    # تحديد المعدل / Rate Limiting
    # ─────────────────────────────────────────────

    rate_limit_chat: int = Field(
        default=30,
        description="حد الطلبات/دقيقة للدردشة — Chat rate limit (requests/minute)",
    )

    rate_limit_voice: int = Field(
        default=15,
        description="حد الطلبات/دقيقة للصوت — Voice rate limit (requests/minute)",
    )

    rate_limit_admin: int = Field(
        default=5,
        description="حد الطلبات/دقيقة للإدارة — Admin rate limit (requests/minute)",
    )

    rate_limit_default: int = Field(
        default=60,
        description="حد الطلبات/دقيقة الافتراضي — Default rate limit (requests/minute)",
    )

    # ─────────────────────────────────────────────
    # الأمن / Security
    # ─────────────────────────────────────────────

    max_request_size_bytes: int = Field(
        default=10 * 1024 * 1024,
        description="الحد الأقصى لحجم الطلب — Max request body size in bytes",
    )

    max_conversation_history: int = Field(
        default=50,
        description="الحد الأقصى لتاريخ المحادثة — Max conversation history entries",
    )

    max_tool_calls: int = Field(
        default=3,
        description="الحد الأقصى لاستدعاءات الأدوات — Max tool calls per cycle",
    )

    tool_timeout: int = Field(
        default=30,
        description="مهلة الأداة بالثواني — Tool timeout in seconds",
    )

    cycle_timeout: int = Field(
        default=180,
        description="مهلة الدورة بالثواني — Cycle timeout in seconds",
    )

    # ─────────────────────────────────────────────
    # الصوت / Voice
    # ─────────────────────────────────────────────

    tts_backend: str = Field(
        default="edge_tts",
        description="محرك تحويل النص لصوت — TTS backend (edge_tts/elevenlabs)",
    )

    tts_dialect: str = Field(
        default="eg",
        description="لهجة TTS — TTS dialect",
    )

    tts_voice: str = Field(
        default="ar-EG-ShakirNeural",
        description="صوت TTS — TTS voice name",
    )

    # ─────────────────────────────────────────────
    # المنسق / Orchestrator
    # ─────────────────────────────────────────────

    orchestrator_health_interval: float = Field(
        default=30.0,
        description="فاصل فحص الصحة — Health check interval in seconds",
    )

    orchestrator_max_concurrent_tasks: int = Field(
        default=10,
        description="الحد الأقصى للمهام المتزامنة — Max concurrent tasks",
    )

    orchestrator_circuit_breaker_threshold: int = Field(
        default=5,
        description="عتبة قاطع الدائرة — Circuit breaker failure threshold",
    )

    orchestrator_circuit_breaker_recovery: float = Field(
        default=60.0,
        description="مدة تعافي قاطع الدائرة — Circuit breaker recovery time (seconds)",
    )

    # ─────────────────────────────────────────────
    # تفعيل/تعطيل الموديولات / Module Enable/Disable
    # ─────────────────────────────────────────────

    enable_memory: bool = Field(
        default=True,
        description="تفعيل الذاكرة — Enable memory module",
    )

    enable_ethics: bool = Field(
        default=True,
        description="تفعيل الأخلاقيات — Enable ethics module",
    )

    enable_voice: bool = Field(
        default=True,
        description="تفعيل الصوت — Enable voice module",
    )

    enable_tools: bool = Field(
        default=True,
        description="تفعيل الأدوات — Enable tools module",
    )

    enable_browser: bool = Field(
        default=True,
        description="تفعيل المتصفح — Enable browser module",
    )

    enable_plugins: bool = Field(
        default=True,
        description="تفعيل الإضافات — Enable plugins module",
    )

    enable_subagents: bool = Field(
        default=True,
        description="تفعيل الوكلاء الفرعيين — Enable sub-agents",
    )

    enable_notebook: bool = Field(
        default=True,
        description="تفعيل الدفتر — Enable notebook module",
    )

    enable_scheduler: bool = Field(
        default=True,
        description="تفعيل المجدول — Enable scheduler module",
    )

    enable_a2a: bool = Field(
        default=True,
        description="تفعيل بروتوكول A2A — Enable A2A protocol",
    )

    # ─────────────────────────────────────────────
    # منصات التواصل / Communication Platforms
    # ─────────────────────────────────────────────

    telegram_bot_token: str = Field(
        default="",
        description="رمز بوت تيليجرام — Telegram bot token",
    )

    discord_bot_token: str = Field(
        default="",
        description="رمز بوت ديسكورد — Discord bot token",
    )

    # ─────────────────────────────────────────────
    # التتبع / Observability
    # ─────────────────────────────────────────────

    tracing_enabled: bool = Field(
        default=True,
        description="تفعيل التتبع — Enable tracing",
    )

    tracing_slow_threshold_ms: float = Field(
        default=5000.0,
        description="عتبة البطء للتتبع — Slow span threshold in ms",
    )

    audit_log_dir: str = Field(
        default="",
        description="مجلد سجلات التدقيق — Audit log directory (empty = default)",
    )

    # ─────────────────────────────────────────────
    # التكوين / Configuration
    # ─────────────────────────────────────────────

    try:
        model_config = {
            "env_file": ".env",
            "env_file_encoding": "utf-8",
            "case_sensitive": False,
            "extra": "ignore",
        }
    except Exception:
        class Config:
            env_file = ".env"
            env_file_encoding = "utf-8"
            case_sensitive = False
            extra = "ignore"

    # ─────────────────────────────────────────────
    # التحقق / Validators
    # ─────────────────────────────────────────────

    @field_validator("ADAM_ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """
        التحقق من صحة بيئة التشغيل — Validate environment value.
        """
        valid = {"development", "staging", "production"}
        if v.lower() not in valid:
            raise ValueError(
                f"ADAM_ENVIRONMENT must be one of {valid}, got '{v}'"
            )
        return v.lower()

    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        """
        التحقق من مفتاح API — Validate API key.

        في الإنتاج، يجب تغيير المفتاح الافتراضي.
        In production, the default key must be changed.
        """
        if v == "CHANGE_ME_IN_PRODUCTION":
            env = os.environ.get("ADAM_ENVIRONMENT", "development")
            is_prod = os.environ.get("ADAM_PRODUCTION", "").lower() in ("true", "1", "yes")
            if is_prod or env == "production":
                raise ValueError(
                    "SECURITY: API key must be changed from default in production! "
                    "Set ADAM_API_KEY or api_key in .env"
                    "الأمان: يجب تغيير مفتاح API الافتراضي في الإنتاج!"
                )
            warnings.warn(
                "⚠️ Using default API key — change before production! "
                "استخدام مفتاح API افتراضي — غيّره قبل الإنتاج!",
                UserWarning,
                stacklevel=2,
            )
        return v

    @field_validator("admin_key")
    @classmethod
    def validate_admin_key(cls, v: str) -> str:
        """
        التحقق من مفتاح المسؤول — Validate admin key.
        """
        if v == "CHANGE_ME_ADMIN_KEY":
            env = os.environ.get("ADAM_ENVIRONMENT", "development")
            is_prod = os.environ.get("ADAM_PRODUCTION", "").lower() in ("true", "1", "yes")
            if is_prod or env == "production":
                raise ValueError(
                    "SECURITY: Admin key must be changed from default in production! "
                    "Set ADAM_ADMIN_KEY or admin_key in .env"
                    "الأمان: يجب تغيير مفتاح المسؤول الافتراضي في الإنتاج!"
                )
        return v

    # ─────────────────────────────────────────────
    # دوال مساعدة / Helper Methods
    # ─────────────────────────────────────────────

    @property
    def is_production(self) -> bool:
        """
        هل هذه بيئة إنتاج؟ — Is this a production environment?
        """
        return self.ADAM_PRODUCTION or self.ADAM_ENVIRONMENT == "production"

    @property
    def is_development(self) -> bool:
        """
        هل هذه بيئة تطوير؟ — Is this a development environment?
        """
        return self.ADAM_ENVIRONMENT == "development"

    def to_dict(self) -> Dict[str, Any]:
        """
        تحويل إلى قاموس — Convert settings to dictionary.
        """
        try:
            return self.model_dump()
        except AttributeError:
            return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}

    def get_rate_limits(self) -> Dict[str, int]:
        """
        الحصول على حدود المعدل — Get rate limit configuration.
        """
        return {
            "chat": self.rate_limit_chat,
            "voice": self.rate_limit_voice,
            "admin": self.rate_limit_admin,
            "default": self.rate_limit_default,
        }

    def get_module_flags(self) -> Dict[str, bool]:
        """
        الحصول على أعلام الموديولات — Get module enable/disable flags.
        """
        return {
            "memory": self.enable_memory,
            "ethics": self.enable_ethics,
            "voice": self.enable_voice,
            "tools": self.enable_tools,
            "browser": self.enable_browser,
            "plugins": self.enable_plugins,
            "subagents": self.enable_subagents,
            "notebook": self.enable_notebook,
            "scheduler": self.enable_scheduler,
            "a2a": self.enable_a2a,
        }

    def to_config_dict(self) -> Dict[str, Any]:
        """
        تحويل إلى قاموس إعدادات متوافق مع المحرك — Convert to engine-compatible config dict.
        """
        d = self.to_dict()
        # إضافة الحقول المحسوبة — Add computed fields
        d["memory"] = {
            "qdrant_url": self.qdrant_url,
            "ollama_base": self.ollama_base,
            "embedding_model": self.embedding_model,
        }
        d["rate_limits"] = self.get_rate_limits()
        return d


# ═══════════════════════════════════════════════════════════════
# Singleton
# ═══════════════════════════════════════════════════════════════

_settings_instance: Optional[AdamSettings] = None


def get_settings() -> AdamSettings:
    """
    الحصول على إعدادات التطبيق (Singleton) — Get application settings (singleton).

    Returns / المخرجات:
        إعدادات آدم بريزم — AdamSettings instance
    """
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = AdamSettings()
    return _settings_instance


def reload_settings() -> AdamSettings:
    """
    إعادة تحميل الإعدادات — Reload settings from environment.

    Returns / المخرجات:
        إعدادات جديدة — New AdamSettings instance
    """
    global _settings_instance
    _settings_instance = AdamSettings()
    return _settings_instance
