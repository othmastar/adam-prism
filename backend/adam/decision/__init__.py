"""
محاكي القرارات الشخصي — Personal Decision Simulator
====================================================
يحاكي سيناريوهات القرار بناءً على بيانات المستخدم الشخصية وأسلوبه في التفكير.
يتعلم من القرارات السابقة ويقدم توقعات مع درجات ثقة.
"""

from adam.decision.simulator import DecisionSimulator, DecisionScenario, SimulationResult

__all__ = ["DecisionSimulator", "DecisionScenario", "SimulationResult"]
