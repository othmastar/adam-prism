"""
Adam Prism — Plugin Base Class
=================================
كل plugin يرث من AdamPlugin وينفذ hooks اللي يحتاجها.
"""

from typing import Dict, Any, Optional, List, Callable, Awaitable


class AdamPlugin:
    """القاعدة لكل الإضافات"""

    name: str = ""
    version: str = "1.0.0"
    description: str = ""
    engine = None

    async def on_load(self, engine):
        self.engine = engine

    async def on_unload(self):
        pass

    async def before_generate(self, message: str, context: Dict) -> Optional[Dict]:
        """قبل التوليد. يرجع dict معدل أو None"""
        pass

    async def after_generate(self, message: str, response: str) -> Optional[str]:
        """بعد التوليد. يرجع رد معدل أو None"""
        pass

    async def before_tool(self, action: Dict) -> Optional[Dict]:
        """قبل تنفيذ الأداة. يرجع action معدل أو None (يمنع التنفيذ)"""
        pass

    async def after_tool(self, action: Dict, result: Dict) -> Optional[Dict]:
        """بعد تنفيذ الأداة. يرجع result معدل أو None"""
        pass
