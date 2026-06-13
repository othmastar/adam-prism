"""
محاكي القرارات الشخصي — Personal Decision Simulator
====================================================
وحدة محاكاة القرارات التي تتعلم من أسلوب المستخدم وتحاكي النتائج المحتملة.

الميزات:
- إنشاء سيناريوهات قرار مع بدائل
- محاكاة النتائج بناءً على الأنماط السابقة
- تقييم المخاطر والفرص
- توصيات مع درجات ثقة
- تعلم من الملاحظات (القرارات الفعلية مقابل المحاكاة)
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

logger = logging.getLogger("adam_prism.decision")


class RiskLevel(StrEnum):
    """مستوى المخاطرة"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DecisionDomain(StrEnum):
    """مجالات القرار"""
    CAREER = "career"
    FINANCIAL = "financial"
    TECHNICAL = "technical"
    PERSONAL = "personal"
    BUSINESS = "business"
    EDUCATION = "education"
    GENERAL = "general"


@dataclass
class DecisionScenario:
    """سيناريو قرار قابل للمحاكاة"""
    title: str
    description: str
    domain: DecisionDomain = DecisionDomain.GENERAL
    options: list[dict[str, Any]] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)
    constraints: list[str] = field(default_factory=list)
    deadline: str | None = None
    stakeholder_impact: list[str] = field(default_factory=list)


@dataclass
class SimulationResult:
    """نتيجة محاكاة قرار"""
    scenario_title: str
    recommended_option: int  # مؤشر الخيار الموصى به
    confidence: float  # 0.0 - 1.0
    risk_level: RiskLevel
    outcomes: list[dict[str, Any]] = field(default_factory=list)
    reasoning: str = ""
    pros: list[str] = field(default_factory=list)
    cons: list[str] = field(default_factory=list)
    similar_past_decisions: list[dict[str, Any]] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class DecisionSimulator:
    """
    محاكي القرارات الشخصي

    يحاكي سيناريوهات القرار بناءً على:
    1. أنماط القرار السابقة للمستخدم
    2. تفضيلات الشخصية المُستفادة
    3. تحليل المخاطر السياقي
    4. مقارنة مع قرارات مشابهة سابقة
    """

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self.data_path = Path(self.config.get("decision_path", "./data/decisions"))
        self.data_path.mkdir(parents=True, exist_ok=True)

        # سجل القرارات السابقة
        self._decision_history: list[dict] = []
        self._user_patterns: dict[str, Any] = {}
        self._domain_preferences: dict[str, float] = {}

        # تحميل البيانات المحفوظة
        self._load()

    def _load(self):
        """تحميل بيانات القرارات السابقة"""
        history_path = self.data_path / "history.json"
        if history_path.exists():
            try:
                self._decision_history = json.loads(history_path.read_text(encoding="utf-8"))
            except Exception:
                logger.exception("تعذر تحميل سجل القرارات:")

        patterns_path = self.data_path / "patterns.json"
        if patterns_path.exists():
            try:
                self._user_patterns = json.loads(patterns_path.read_text(encoding="utf-8"))
            except Exception:
                logger.exception("تعذر تحميل أنماط القرار:")

    def _save_history(self):
        """حفظ سجل القرارات"""
        history_path = self.data_path / "history.json"
        # الاحتفاظ بآخر 500 قرار فقط
        data = self._decision_history[-500:]
        history_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

    def _save_patterns(self):
        """حفظ أنماط القرار"""
        patterns_path = self.data_path / "patterns.json"
        patterns_path.write_text(
            json.dumps(self._user_patterns, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

    async def simulate(self, scenario: DecisionScenario) -> SimulationResult:
        """
        محاكاة سيناريو قرار

        المراحل:
        1. تحليل السياق والخيارات
        2. البحث عن قرارات مشابهة سابقة
        3. تقييم المخاطر لكل خيار
        4. التوصية بناءً على الأنماط الشخصية
        5. تقديم المبررات مع درجة الثقة
        """
        # 1. تحليل السياق والخيارات — تحويل domain إلى enum لو كان string
        if isinstance(scenario.domain, str):
            try:
                scenario.domain = DecisionDomain(scenario.domain)
            except ValueError:
                scenario.domain = DecisionDomain.GENERAL

        # 2. البحث عن قرارات مشابهة
        similar = self._find_similar_decisions(scenario)

        # 2. تقييم كل خيار
        option_evaluations = []
        for _idx, option in enumerate(scenario.options):
            evaluation = self._evaluate_option(
                option, scenario, similar
            )
            option_evaluations.append(evaluation)

        # 3. اختيار الخيار الأفضل
        if not option_evaluations:
            return SimulationResult(
                scenario_title=scenario.title,
                recommended_option=0,
                confidence=0.0,
                risk_level=RiskLevel.MEDIUM,
                reasoning="لا توجد خيارات كافية للتقييم",
            )

        # ترتيب حسب الدرجة الإجمالية
        best_idx = max(range(len(option_evaluations)),
                       key=lambda i: option_evaluations[i]["score"])
        best_eval = option_evaluations[best_idx]

        # 4. تحديد مستوى المخاطرة
        risk = self._assess_risk(best_eval, scenario)

        # 5. بناء المبررات
        reasoning = self._build_reasoning(best_eval, scenario, similar)

        # 6. بناء المزايا والعيوب
        pros = best_eval.get("pros", [])
        cons = best_eval.get("cons", [])

        result = SimulationResult(
            scenario_title=scenario.title,
            recommended_option=best_idx,
            confidence=best_eval["confidence"],
            risk_level=risk,
            outcomes=option_evaluations,
            reasoning=reasoning,
            pros=pros,
            cons=cons,
            similar_past_decisions=similar[:3],
        )

        # تسجيل المحاكاة
        self._record_simulation(scenario, result)

        return result

    def _evaluate_option(
        self, option: dict[str, Any], scenario: DecisionScenario,
        similar: list[dict]
    ) -> dict[str, Any]:
        """تقييم خيار واحد بناءً على معايير متعددة"""
        score = 0.5  # درجة أساسية محايدة
        pros = []
        cons = []

        # 1. تقييم بناءً على الأنماط الشخصية
        domain = scenario.domain.value
        if domain in self._domain_preferences:
            domain_score = self._domain_preferences[domain]
            score = score * 0.7 + domain_score * 0.3

        # 2. تقييم بناءً على القرارات المشابهة
        if similar:
            success_rate = sum(
                1 for d in similar if d.get("outcome") == "positive"
            ) / len(similar)
            score = score * 0.6 + success_rate * 0.4
            pros.append(f"قرارات مشابهة سابقة: {len(similar)} قرار")

        # 3. تقييم المخاطر المذكورة في الخيار
        risk_level = option.get("risk", "medium")
        risk_scores = {"low": 0.9, "medium": 0.6, "high": 0.3, "critical": 0.1}
        risk_score = risk_scores.get(risk_level, 0.5)

        if risk_score > 0.7:
            pros.append(f"مخاطرة منخفضة ({risk_level})")
        elif risk_score < 0.4:
            cons.append(f"مخاطرة عالية ({risk_level})")

        score = score * 0.7 + risk_score * 0.3

        # 4. تقييم التكلفة/الفائدة إن وُجدت
        cost = option.get("cost", 0)
        benefit = option.get("benefit", 0)
        if benefit > 0 and cost > 0:
            roi = benefit / cost
            if roi > 2:
                pros.append(f"عائد مرتفع: {roi:.1f}x")
                score += 0.1
            elif roi < 0.5:
                cons.append(f"عائد منخفض: {roi:.1f}x")
                score -= 0.1

        # 5. بناء الإيجابيات والسلبيات من وصف الخيار
        option_pros = option.get("pros", [])
        option_cons = option.get("cons", [])
        pros.extend(option_pros[:3])
        cons.extend(option_cons[:3])

        return {
            "option": option.get("name", f"خيار {option}"),
            "score": max(0.0, min(1.0, score)),
            "confidence": max(0.1, min(0.95, abs(score - 0.5) * 2)),
            "risk_level": risk_level,
            "pros": pros[:5],
            "cons": cons[:5],
        }

    def _assess_risk(self, evaluation: dict, scenario: DecisionScenario) -> RiskLevel:
        """تقييم مستوى المخاطرة الإجمالي"""
        score = evaluation["score"]
        risk_level_str = evaluation.get("risk_level", "medium")

        if score >= 0.8 and risk_level_str == "low":
            return RiskLevel.LOW
        elif score >= 0.6:
            return RiskLevel.MEDIUM
        elif score >= 0.4:
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL

    def _find_similar_decisions(self, scenario: DecisionScenario) -> list[dict]:
        """البحث عن قرارات مشابهة في السجل"""
        similar = []
        domain = scenario.domain.value

        for past in self._decision_history:
            # مطابقة المجال
            if past.get("domain") == domain or any(
                word in past.get("title", "").lower()
                for word in scenario.title.lower().split()
                if len(word) > 3
            ):
                similar.append(past)

        return similar[-10:]  # آخر 10 قرارات مشابهة

    def _build_reasoning(
        self, evaluation: dict, scenario: DecisionScenario,
        similar: list[dict]
    ) -> str:
        """بناء مبررات التوصية"""
        parts = []

        # 1. التوصية الأساسية
        parts.append(
            f"بناءً على التحليل، الخيار الموصى به هو: {evaluation['option']} "
            f"بدرجة ثقة {evaluation['confidence']:.0%}"
        )

        # 2. المرجعية من القرارات السابقة
        if similar:
            positive = sum(1 for d in similar if d.get("outcome") == "positive")
            parts.append(
                f"يوجد {len(similar)} قرار مشابه سابق، "
                f"منها {positive} قرار بنتيجة إيجابية"
            )
        else:
            parts.append("لا توجد قرارات مشابهة سابقة — التوصية مبنية على التحليل العام")

        # 3. المخاطر
        if evaluation.get("cons"):
            parts.append(f"المخاطر الرئيسية: {', '.join(evaluation['cons'][:3])}")

        return ". ".join(parts)

    def _record_simulation(self, scenario: DecisionScenario, result: SimulationResult):
        """تسجيل محاكاة قرار"""
        record = {
            "title": scenario.title,
            "domain": scenario.domain.value,
            "options_count": len(scenario.options),
            "recommended": result.recommended_option,
            "confidence": result.confidence,
            "risk_level": result.risk_level.value,
            "timestamp": result.timestamp,
            "outcome": None,  # سيتم تحديثه لاحقاً
        }
        self._decision_history.append(record)
        self._save_history()

    async def record_outcome(self, decision_title: str, outcome: str, notes: str = ""):
        """تسجيل نتيجة قرار فعلي — يُحسّن المحاكاة المستقبلية"""
        for record in reversed(self._decision_history):
            if record["title"] == decision_title and record["outcome"] is None:
                record["outcome"] = outcome
                record["notes"] = notes
                break

        # تحديث أنماط المجال
        self._update_domain_patterns(outcome)
        self._save_history()
        self._save_patterns()

        logger.info(f"📝 تم تسجيل نتيجة قرار: {decision_title} → {outcome}")

    def _update_domain_patterns(self, outcome: str):
        """تحديث أنماط المجال بناءً على النتيجة"""
        outcome_score = 1.0 if outcome == "positive" else 0.0
        for domain in self._domain_preferences:
            current = self._domain_preferences[domain]
            # متوسط متحرك
            self._domain_preferences[domain] = current * 0.9 + outcome_score * 0.1

    def get_stats(self) -> dict[str, Any]:
        """إحصائيات محاكي القرارات"""
        total = len(self._decision_history)
        with_outcome = [d for d in self._decision_history if d.get("outcome")]
        positive = sum(1 for d in with_outcome if d["outcome"] == "positive")

        return {
            "total_simulations": total,
            "decisions_with_outcome": len(with_outcome),
            "positive_outcomes": positive,
            "negative_outcomes": len(with_outcome) - positive,
            "accuracy": round(positive / max(len(with_outcome), 1), 2),
            "domains_tracked": list(self._domain_preferences.keys()),
        }
