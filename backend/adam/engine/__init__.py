"""
Adam Prism Engine - المحرك الرئيسي (Package)
=============================================
المحرك المركزي الذي يربط كل موديولات النظام.

Split into sub-modules for maintainability:
- base.py: __init__, stubs, real init, properties, watchdog
- utils.py: utility methods (classify, security, heal, verify, call wrappers, status)
- context.py: _build_context with RAG collection routing
- generate.py: _generate, system prompts, tool registry, message construction
- tools.py: _execute_tool dispatcher + 14 handler methods
- chat.py: chat() processing cycle + sub-methods
"""

from adam.engine.chat import AdamPrismEngineChat as AdamPrismEngine

__all__ = ["AdamPrismEngine"]
