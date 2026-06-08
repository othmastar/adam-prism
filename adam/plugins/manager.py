"""
Adam Prism — Plugin Manager
=============================
يكتشف ويدير الإضافات. يشغل hooks قبل وبعد كل عملية.
"""

import os
import sys
import importlib
import inspect
import logging
from typing import Dict, Any, List, Optional, Type

from adam.plugins.base import AdamPlugin

logger = logging.getLogger("adam_prism.plugins")


class PluginManager:
    """مدير الإضافات — يكتشف، يحمل، يشغل hooks"""

    def __init__(self, engine=None, plugin_dirs: List[str] = None):
        self.engine = engine
        self.plugin_dirs = plugin_dirs or []
        self.plugins: Dict[str, AdamPlugin] = {}
        self._hook_order: List[str] = []

    # ─── Load / Unload ─────────────────────────────────

    def discover(self, *directories: str) -> List[str]:
        """يبحث عن plugins في مجلدات معينة"""
        found = []
        for directory in directories:
            if not os.path.isdir(directory):
                continue
            for entry in os.listdir(directory):
                if entry.startswith("_"):
                    continue
                plugin_dir = os.path.join(directory, entry)
                if os.path.isdir(plugin_dir) and os.path.isfile(os.path.join(plugin_dir, "__init__.py")):
                    found.append(plugin_dir)
                elif entry.endswith(".py") and not entry.startswith("_"):
                    found.append(plugin_dir)
        return found

    def load_from_dir(self, directory: str):
        """يحمل كل الـ plugins من مجلد"""
        entries = self.discover(directory)
        self._hook_order = []
        for path in entries:
            self._load_single(path)

    def load_plugin(self, plugin_class: Type[AdamPlugin]):
        """يحمل plugin من class مباشرة"""
        try:
            instance = plugin_class()
            name = instance.name or plugin_class.__name__
            if name in self.plugins:
                logger.warning(f"⚠️ Plugin '{name}' موجود مسبقاً — استبدال")
            self.plugins[name] = instance
            self._hook_order.append(name)
            logger.info(f"✅ Plugin loaded: {name} v{instance.version}")
        except Exception as e:
            logger.warning(f"⚠️ Plugin load failed: {e}")

    def _load_single(self, path: str):
        """يحمل plugin واحد من مسار"""
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
        except Exception as e:
            logger.warning(f"⚠️ فشل تحميل plugin من {path}: {e}")

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

    async def run_before_generate(self, message: str, context: Dict) -> tuple:
        """يشغل hooks قبل التوليد. يرجع (message, context)"""
        for name in self._hook_order:
            plugin = self.plugins[name]
            try:
                result = await plugin.before_generate(message, context)
                if result is not None:
                    if isinstance(result, dict):
                        if "message" in result:
                            message = result["message"]
                        if "context" in result:
                            context = result["context"]
            except Exception as e:
                logger.warning(f"⚠️ Plugin '{name}'.before_generate error: {e}")
        return message, context

    async def run_after_generate(self, message: str, response: str) -> str:
        """يشغل hooks بعد التوليد. يرجع الرد المعدل"""
        for name in self._hook_order:
            plugin = self.plugins[name]
            try:
                result = await plugin.after_generate(message, response)
                if result is not None:
                    response = result
            except Exception as e:
                logger.warning(f"⚠️ Plugin '{name}'.after_generate error: {e}")
        return response

    async def run_before_tool(self, action: Dict) -> Optional[Dict]:
        """يشغل hooks قبل الأداة. يرجع None لو عايز يمنع التنفيذ"""
        for name in self._hook_order:
            plugin = self.plugins[name]
            try:
                result = await plugin.before_tool(action)
                if result is None:
                    logger.info(f"🚫 Plugin '{name}' منع الأداة: {action.get('type')}")
                    return None  # امان
                action = result
            except Exception as e:
                logger.warning(f"⚠️ Plugin '{name}'.before_tool error: {e}")
        return action

    async def run_after_tool(self, action: Dict, result: Dict) -> Dict:
        """يشغل hooks بعد الأداة"""
        for name in self._hook_order:
            plugin = self.plugins[name]
            try:
                new_result = await plugin.after_tool(action, result)
                if new_result is not None:
                    result = new_result
            except Exception as e:
                logger.warning(f"⚠️ Plugin '{name}'.after_tool error: {e}")
        return result

    # ─── Query ─────────────────────────────────────────

    def list_plugins(self) -> List[Dict]:
        return [
            {
                "name": name,
                "version": p.version,
                "description": p.description,
            }
            for name, p in self.plugins.items()
        ]

    def get_plugin(self, name: str) -> Optional[AdamPlugin]:
        return self.plugins.get(name)
