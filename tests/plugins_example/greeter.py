"""
Example Adam Plugin — Greeter
===============================
يضيف توقيع للردود.
"""

from adam.plugins.base import AdamPlugin

class GreeterPlugin(AdamPlugin):
    name = "greeter"
    version = "1.0.0"
    description = "يضيف توقيع للردود"

    async def after_generate(self, message: str, response: str) -> str:
        return response + "\n\n— آدم 🔮"
