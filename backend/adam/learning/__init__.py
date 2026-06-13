"""
Adam Prism — Continuous Learning System
=========================================
آدم يتعلم من كل تفاعل: reflection, knowledge extraction, skill generation.
+ Closed Learning Loop: MemoryNudge + SkillCreator + SkillImprover
"""

from .learner import ContinuousLearner
from .closed_loop import ClosedLearningLoop, MemoryNudge, SkillCreator, SkillImprover

__all__ = ["ContinuousLearner", "ClosedLearningLoop", "MemoryNudge", "SkillCreator", "SkillImprover"]
