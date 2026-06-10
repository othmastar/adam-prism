"""
Adam Prism — Skills System
===========================
مهارات آدم: قطع معرفية قابلة لإعادة الاستخدام.
Skill = instructions + optional code that آدم can load and use dynamically.
"""

from .base import Skill
from .manager import SkillManager

__all__ = ["Skill", "SkillManager"]
