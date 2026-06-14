"""
Adam Prism — Skills System
===========================
مهارات آدم: قطع معرفية قابلة لإعادة الاستخدام.
Skill = instructions + optional code that آدم can load and use dynamically.
+ Curator (دورة حياة المهارات: active → stale → archived)
+ Progressive Disclosure (فهرس فقط في prompt)
"""

from .base import Skill
from .manager import SkillManager
from .curator import SkillCurator

__all__ = ["Skill", "SkillCurator", "SkillManager"]
