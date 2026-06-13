"""
محاكي القرارات الشخصي — Personal Decision Simulator
====================================================
يحاكي سيناريوهات القرار بناءً على بيانات المستخدم الشخصية وأسلوبه في التفكير.
يتعلم من القرارات السابقة ويقدم توقعات مع درجات ثقة.
"""

from adam.decision.simulator import DecisionScenario, DecisionSimulator, SimulationResult

__all__ = ["DecisionScenario", "DecisionSimulator", "SimulationResult"]
