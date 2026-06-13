"""اختبار نظام الإضافات (plugins)"""

import pytest
from adam.plugins.manager import PluginManager
from adam.plugins.base import AdamPlugin


class TestPlugin(AdamPlugin):
    name = "test"
    version = "1.0.0"
    description = "اختبار"

    def __init__(self):
        super().__init__()
        self.before_called = False
        self.after_called = False
        self.before_tool_called = False
        self.after_tool_called = False

    async def before_generate(self, message: str, context: dict) -> dict:
        self.before_called = True
        return {"message": message + " [modified]", "context": context}

    async def after_generate(self, message: str, response: str) -> str:
        self.after_called = True
        return response + " [signed]"

    async def before_tool(self, action: dict) -> dict:
        self.before_tool_called = True
        return {**action, "type": action["type"] + "_modified"}

    async def after_tool(self, action: dict, result: dict) -> dict:
        self.after_tool_called = True
        return {**result, "plugin_processed": True}


@pytest.mark.asyncio
async def test_load_plugin():
    pm = PluginManager()
    pm.load_plugin(TestPlugin)
    assert len(pm.list_plugins()) == 1
    assert pm.list_plugins()[0]["name"] == "test"


@pytest.mark.asyncio
async def test_before_generate_hook():
    pm = PluginManager()
    pm.load_plugin(TestPlugin)
    msg, ctx = await pm.run_before_generate("hello", {"key": "val"})
    plugin = pm.get_plugin("test")
    assert plugin.before_called
    assert "[modified]" in msg


@pytest.mark.asyncio
async def test_after_generate_hook():
    pm = PluginManager()
    pm.load_plugin(TestPlugin)
    result = await pm.run_after_generate("hello", "world")
    plugin = pm.get_plugin("test")
    assert plugin.after_called
    assert "[signed]" in result


@pytest.mark.asyncio
async def test_before_tool_hook():
    pm = PluginManager()
    pm.load_plugin(TestPlugin)
    action = {"type": "browser_open", "url": "https://example.com"}
    result = await pm.run_before_tool(action)
    plugin = pm.get_plugin("test")
    assert plugin.before_tool_called
    assert result is not None
    assert "_modified" in result["type"]


@pytest.mark.asyncio
async def test_after_tool_hook():
    pm = PluginManager()
    pm.load_plugin(TestPlugin)
    result = await pm.run_after_tool({"type": "test"}, {"success": True, "data": "ok"})
    plugin = pm.get_plugin("test")
    assert plugin.after_tool_called
    assert result["plugin_processed"]


@pytest.mark.asyncio
async def test_unload():
    pm = PluginManager()
    pm.load_plugin(TestPlugin)
    assert len(pm.list_plugins()) == 1
    await pm.unload("test")
    assert len(pm.list_plugins()) == 0


@pytest.mark.asyncio
async def test_load_from_dir():
    import os, tempfile
    # [C4] السماح بـ /tmp لاختبارات
    os.environ["ADAM_PLUGIN_DIR"] = "/tmp"
    pm = PluginManager()

    # Create a temp plugin file
    with tempfile.TemporaryDirectory() as td:
        plugin_code = '''
from adam.plugins.base import AdamPlugin

class TempPlugin(AdamPlugin):
    name = "temp"
    version = "1.0.0"
    description = "temp"
'''
        plugin_path = os.path.join(td, "temp_plugin.py")
        with open(plugin_path, "w") as f:
            f.write(plugin_code)

        pm.load_from_dir(td)
        names = [p["name"] for p in pm.list_plugins()]
        assert "temp" in names


@pytest.mark.asyncio
async def test_discover():
    import tempfile, os
    pm = PluginManager()
    with tempfile.TemporaryDirectory() as td:
        # Empty dir
        found = pm.discover(td)
        assert len(found) == 0
        # Create a .py file
        open(os.path.join(td, "test.py"), "w").close()
        found = pm.discover(td)
        assert len(found) == 1
        # Create a package dir
        pkg = os.path.join(td, "mypkg")
        os.makedirs(pkg)
        open(os.path.join(pkg, "__init__.py"), "w").close()
        found = pm.discover(td)
        assert len(found) == 2
