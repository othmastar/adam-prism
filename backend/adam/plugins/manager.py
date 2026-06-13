"""
Adam Prism — Plugin Manager — HARDENED v2
=============================================
يكتشف ويدير الإضافات. يشغل hooks قبل وبعد كل عملية.

[C4 — CRITICAL SECURITY]
- Plugin loading restricted to ALLOWED_PLUGIN_DIR only
- Resolved paths validated to be within the allowed directory
- Prevents path traversal and arbitrary code execution from untrusted dirs
"""

import importlib
import inspect
import logging
import os
import sys

from adam.plugins.base import AdamPlugin

logger = logging.getLogger("adam_prism.plugins")

# [C4] المجلدات المسموح بتحميل الإضافات منها فقط
ALLOWED_PLUGIN_DIR = os.environ.get(
    "ADAM_PLUGIN_DIR",
    os.path.join(os.getcwd(), "plugins")
)


def _validate_plugin_path(path: str) -> bool:
    """التحقق من أن المسار داخل المجلد المسموح — منع path traversal"""
    if not path:
        return False
    try:
        resolved = os.path.realpath(path)
        allowed_resolved = os.path.realpath(ALLOWED_PLUGIN_DIR)
        # Check that the resolved path is within the allowed directory
        if not resolved.startswith(allowed_resolved + os.sep) and resolved != allowed_resolved:
            logger.warning(f"⚠️ Plugin path rejected (outside allowed dir): {path} -> {resolved} (allowed: {allowed_resolved})")
            return False
        return True
    except Exception:
        logger.exception("⚠️ Plugin path validation error:")
        return False


class PluginManager:
    """مدير الإضافات — يكتشف، يحمل، يشغل hooks"""

    def __init__(self, engine=None, plugin_dirs: list[str] | None = None):
        self.engine = engine
        self.plugin_dirs = plugin_dirs or []
        self.plugins: dict[str, AdamPlugin] = {}
        self._hook_order: list[str] = []

    # ─── Load / Unload ─────────────────────────────────

    def discover(self, *directories: str) -> list[str]:
        """يبحث عن plugins في مجلدات معينة"""
        found = []
        for directory in directories:
            # [C4] Validate directory is within allowed path
            if not _validate_plugin_path(directory):
                logger.warning(f"⚠️ Plugin directory rejected: {directory}")
                continue
            if not os.path.isdir(directory):
                continue
            for entry in os.listdir(directory):
                if entry.startswith("_"):
                    continue
                plugin_dir = os.path.join(directory, entry)
                if os.path.isdir(plugin_dir) and os.path.isfile(os.path.join(plugin_dir, "__init__.py")):
                    # [C4] Validate each discovered path
                    if _validate_plugin_path(plugin_dir):
                        found.append(plugin_dir)
                elif entry.endswith(".py") and not entry.startswith("_"):
                    # [C4] Validate single file path
                    if _validate_plugin_path(plugin_dir):
                        found.append(plugin_dir)
        return found

    def load_from_dir(self, directory: str):
        """يحمل كل الـ plugins من مجلد"""
        # [C4] Validate before discovering
        if not _validate_plugin_path(directory):
            logger.error(f"🚫 Plugin load rejected — directory outside allowed path: {directory}")
            return
        entries = self.discover(directory)
        self._hook_order = []
        for path in entries:
            self._load_single(path)

    def load_plugin(self, plugin_class: type[AdamPlugin]):
        """يحمل plugin من class مباشرة"""
        try:
            instance = plugin_class()
            name = instance.name or plugin_class.__name__
            if name in self.plugins:
                logger.warning(f"⚠️ Plugin '{name}' موجود مسبقاً — استبدال")
            self.plugins[name] = instance
            self._hook_order.append(name)
            logger.info(f"✅ Plugin loaded: {name} v{instance.version}")
        except Exception:
            logger.exception("⚠️ Plugin load failed:")

    def _load_single(self, path: str):
        """يحمل plugin واحد من مسار"""
        # [C4] Validate path before loading
        if not _validate_plugin_path(path):
            logger.error(f"🚫 Plugin load rejected — path outside allowed dir: {path}")
            return
        try:
            module_name = os.path.splitext(os.path.basename(path))[0]
            if path.endswith(".py"):
                # Single .py file
                spec = importlib.util.spec_from_file_location(module_name, path)
                if not spec or not spec.loader:
                    return
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
            else:
                # Package directory
                spec = importlib.util.spec_from_file_location(
                    module_name, os.path.join(path, "__init__.py")
                )
                if not spec or not spec.loader:
                    return
                mod = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = mod
                spec.loader.exec_module(mod)

            # البحث عن classes ترث AdamPlugin
            for _name, obj in inspect.getmembers(mod, inspect.isclass):
                if issubclass(obj, AdamPlugin) and obj is not AdamPlugin:
                    self.load_plugin(obj)
        except Exception:
            logger.exception("⚠️ تعذر تحميل plugin من {path}:")

    async def unload(self, plugin_name: str) -> bool:
        """إلغاء تحميل plugin"""
        plugin = self.plugins.pop(plugin_name, None)
        if plugin:
            await plugin.on_unload()
            self._hook_order = [n for n in self._hook_order if n != plugin_name]
            logger.info(f"🗑 Plugin '{plugin_name}' unloaded")
            return True
        return False

    async def unload_all(self):
        for name in list(self.plugins.keys()):
            await self.unload(name)

    # ─── Hooks ─────────────────────────────────────────

    async def run_before_generate(self, message: str, context: dict) -> tuple:
        """يشغل hooks قبل التوليد. يرجع (message, context)"""
        for name in self._hook_order:
            plugin = self.plugins[name]
            try:
                result = await plugin.before_generate(message, context)
                if result is not None and isinstance(result, dict):
                    if "message" in result:
                        message = result["message"]
                    if "context" in result:
                        context = result["context"]
            except Exception:
                logger.exception("⚠️ Plugin '{name}'.before_generate error:")
        return message, context

    async def run_after_generate(self, message: str, response: str) -> str:
        """يشغل hooks بعد التوليد. يرجع الرد المعدل"""
        for name in self._hook_order:
            plugin = self.plugins[name]
            try:
                result = await plugin.after_generate(message, response)
                if result is not None:
                    response = result
            except Exception:
                logger.exception("⚠️ Plugin '{name}'.after_generate error:")
        return response

    async def run_before_tool(self, action: dict) -> dict | None:
        """يشغل hooks قبل الأداة. يرجع None لو عايز يمنع التنفيذ"""
        for name in self._hook_order:
            plugin = self.plugins[name]
            try:
                result = await plugin.before_tool(action)
                if result is None:
                    logger.info(f"🚫 Plugin '{name}' منع الأداة: {action.get('type')}")
                    return None  # امان
                action = result
            except Exception:
                logger.exception("⚠️ Plugin '{name}'.before_tool error:")
        return action

    async def run_after_tool(self, action: dict, result: dict) -> dict:
        """يشغل hooks بعد الأداة"""
        for name in self._hook_order:
            plugin = self.plugins[name]
            try:
                new_result = await plugin.after_tool(action, result)
                if new_result is not None:
                    result = new_result
            except Exception:
                logger.exception("⚠️ Plugin '{name}'.after_tool error:")
        return result

    # ─── Query ─────────────────────────────────────────

    def list_plugins(self) -> list[dict]:
        return [
            {
                "name": name,
                "version": p.version,
                "description": p.description,
            }
            for name, p in self.plugins.items()
        ]

    def get_plugin(self, name: str) -> AdamPlugin | None:
        return self.plugins.get(name)
