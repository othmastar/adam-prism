"""
Adam Prism - نظام الأخلاق — HARDENED v3
=========================================
البوابة الأخلاقية: تقييم كل رد حسب القوانين الأربعة
العدالة (40%) > التعلم (30%) > البقاء (20%) > الإبداع (10%)

[FIX v3]
1. إصلاح استيراد TTLCache
2. [CRITICAL FIX] استبدال 'client' in dir() بـ 'client' in locals()
   - dir() يرجع أسماء كل الخصائص والطرق، مش المتغيرات المحلية فقط
   - هذا كان يسبب إن client دائماً يُعتبر موجود حتى لو مش موجود
   - locals() يرجع المتغيرات المحلية الفعلية فقط
"""

import json
import logging
from typing import Dict, Any, Optional

import httpx

from adam.infrastructure import TTLCache

logger = logging.getLogger("adam_prism.ethics")


class EthicsGate:
    """
    البوابة الأخلاقية لآدم بريزم.
    
    القوانين بالأولوية:
    1. العدالة (40%) - الإنصاف، الحقيقة، عدم التحيز
    2. التعلم (30%) - نمو المستخدم والنظام
    3. البقاء (20%) - حماية المستخدم والنظام
    4. الإبداع (10%) - الابتكار وحل المشكلات
    
    كل رد يُمر عبر التقييم قبل الإرسال.
    """

    def __init__(self, config: Dict[str, Any], shared_clients=None):
        self.config = config
        self.shared_clients = shared_clients
        self.ollama_base = config.get("ollama_base", "http://localhost:11434")
        self.model_name = config.get("model_name", "gemma3:4b")
        self._eval_cache = TTLCache(default_ttl=300.0, max_size=100)
        
        # أوزان القوانين — تدعم override من config
        self.law_weights = {
            "fairness": 0.40,    # العدالة
            "learning": 0.30,    # التعلم
            "survival": 0.20,    # البقاء
            "creativity": 0.10   # الإبداع
        }
        config_weights = config.get("law_weights", {})
        if config_weights:
            self.law_weights = config_weights
        
        # المحرمات المطلقة
        self.absolute_prohibitions = [
            "إيذاء جسدي أو نفسي",
            "انتهاك خصوصية الغير",
            "تزوير معلومات أو أدلة",
            "التلاعب بقرارات المستخدم",
            "إخفاء معلومات مهمة عمداً"
        ]

    async def evaluate(self, response: str, original_query: str = "") -> Dict[str, Any]:
        """
        تقييم الرد أخلاقياً.
        
        Returns:
            {
                "approved": bool,
                "scores": {"fairness": 0-1, "learning": 0-1, ...},
                "weighted_score": 0-1,
                "issues": [...],
                "modified_response": str (if modified)
            }
        """
        # 1. فحص المحرمات المطلقة
        violations = self._check_absolute_prohibitions(response)
        if violations:
            return {
                "approved": False,
                "scores": {},
                "weighted_score": 0.0,
                "issues": violations,
                "modified_response": "⚠️ تم رفض الرد لانتهاكه قاعدة أخلاقية أساسية."
            }

        # 2. تقييم بالأوزان عبر النموذج
        scores = await self._evaluate_with_model(response, original_query)
        
        # 3. حساب المجموع المرجح
        weighted_score = sum(
            scores.get(law, 0.5) * weight 
            for law, weight in self.law_weights.items()
        )

        # 4. قرار القبول — عتبة 0.55 (مخففة من 0.3 لمنع الختم المطاطي)
        # الحد الأدنى: عدالة >= 0.3 وبقاء >= 0.2 + مجموع مرجح >= 0.55
        min_fairness = scores.get("fairness", 0.5)
        min_survival = scores.get("survival", 0.5)
        approved = weighted_score >= 0.55 and min_fairness >= 0.3 and min_survival >= 0.2
        
        result = {
            "approved": approved,
            "scores": scores,
            "weighted_score": round(weighted_score, 3),
            "issues": []
        }

        # 5. لو الرد ضعيف جداً في العدالة، حاول تصحيحه
        if scores.get("fairness", 1.0) < 0.3:
            corrected = await self._correct_response(response, "fairness")
            result["modified_response"] = corrected
            result["issues"].append("تم تعديل الرد لتحسين العدالة")

        return result

    def _check_absolute_prohibitions(self, text: str) -> list:
        """فحص المحرمات المطلقة (بدون نموذج)"""
        violations = []
        text_lower = text.lower()
        
        # كلمات مفتاحية خطيرة (قابلة للتوسيع) — شاملة للمرادفات والتشكيل
        danger_keywords = {
            "إيذاء": ["أذى", "ألم", "ضرر", "اذى", "إيذاء", "آذى", "ايذاء", "إيذاء جسدي", "إيذاء نفسي", "harm", "hurt", "injure", "damage", "kill", "murder", "assault"],
            "انتهاك خصوصية": ["تجسس", "اختراق", "مراقبة بدون إذن", "spy", "surveil", "stalk", "snoop", "تنصت", "رصد غير مصرح"],
            "تزوير": ["تزوير", "تزييف", "معلومات كاذبة", "forge", "fake", "fabricate", "falsify", "مزور", "مزيف"],
            "تلاعب": ["تلاعب", "خداع", "غش", "manipulate", "deceive", "trick", "coerce", "إكراه", "إجبار"],
            "إخفاء معلومات": ["إخفاء", "كتمان", "حجب معلومات", "conceal", "hide information", "withhold facts"]
        }
        
        for category, keywords in danger_keywords.items():
            for kw in keywords:
                if kw in text_lower:
                    violations.append(f"محتوى مشبوه: {category}")
                    break
        
        return violations

    async def _evaluate_with_model(self, response: str, query: str = "") -> Dict[str, float]:
        """تقييم الرد بالأوزان الأربعة عبر النموذج"""
        prompt = f"""قيّم الرد التالي حسب القوانين الأربعة من 0 إلى 1:

1. العدالة (fairness): هل الرد منصف وصادق وغير متحيز؟
2. التعلم (learning): هل الرد يساعد المستخدم على التعلم والنمو؟
3. البقاء (survival): هل الرد يحافظ على أمان المستخدم والنظام؟
4. الإبداع (creativity): هل الرد مبتكر ويحل المشكلة فعلاً؟

السؤال الأصلي: {query}
الرد: {response}

أجب بـ JSON فقط:
{{"fairness": 0.0-1.0, "learning": 0.0-1.0, "survival": 0.0-1.0, "creativity": 0.0-1.0}}"""

        client = None  # [M4] Initialize before try to avoid scope issues
        try:
            cache_key = self._eval_cache._key(response[:200], query[:100])
            cached = self._eval_cache.get(cache_key)
            if cached is not None:
                return cached

            if self.shared_clients:
                client = await self.shared_clients.get("ollama", self.ollama_base, 60.0)
            else:
                client = httpx.AsyncClient(timeout=60.0)

            result = await client.post(
                "/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.1}
                }
            )
            text = result.json().get("response", "")
            parsed = json.loads(text.strip().replace("```json", "").replace("```", ""))
            
            scores = {
                "fairness": max(0, min(1, parsed.get("fairness", 0.5))),
                "learning": max(0, min(1, parsed.get("learning", 0.5))),
                "survival": max(0, min(1, parsed.get("survival", 0.5))),
                "creativity": max(0, min(1, parsed.get("creativity", 0.5)))
            }
            self._eval_cache.set(cache_key, scores, ttl=300.0)
            return scores
        except Exception as e:
            logger.warning(f"فشل التقييم الأخلاقي: {e}")
            return {"fairness": 0.5, "learning": 0.5, "survival": 0.5, "creativity": 0.5}
        finally:
            # [M4] Use client is not None instead of 'client' in locals()
            if not self.shared_clients and client is not None:
                await client.aclose()

    async def _correct_response(self, response: str, law: str) -> str:
        """محاولة تصحيح الرد لو فيه مشكلة"""
        law_names = {
            "fairness": "العدالة",
            "learning": "تعلم المستخدم",
            "survival": "الأمان والحماية",
            "creativity": "الإبداع"
        }
        
        prompt = f"""الرد التالي ضعيف في جانب {law_names.get(law, law)}.
أعد صياغته لتحسين هذا الجانب مع الحفاظ على المعنى:

الرد: {response}

أعطني الرد المصحح فقط."""

        client = None  # [M4] Initialize before try to avoid scope issues
        try:
            if self.shared_clients:
                client = await self.shared_clients.get("ollama", self.ollama_base, 60.0)
            else:
                client = httpx.AsyncClient(timeout=60.0)

            result = await client.post(
                "/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.3}
                }
            )
            return result.json().get("response", response)
        except Exception:
            return response
        finally:
            # [M4] Use client is not None instead of 'client' in locals()
            if not self.shared_clients and client is not None:
                await client.aclose()
