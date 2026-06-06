"""
Adam Prism - نظام الأمن
========================
5 طبقات أمنية: Auth → Behavior → Confirmation → Ethics → Sandbox
"""

import json
import time
import hashlib
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

logger = logging.getLogger("adam_prism.security")


class SecurityCoordinator:
    """
    المنسق الأمني لآدم بريزم.
    
    الطبقات الخمس:
    1. المصادقة (Auth) - من أنت؟
    2. السلوك (Behavior) - ماذا تفعل؟
    3. التأكيد (Confirmation) - هل أنت متأكد؟
    4. الأخلاق (Ethics) - هل هذا صحيح؟
    5. الحماية (Sandbox) - تنفيذ آمن
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.authorized_users = config.get("authorized_users", ["owner"])
        self.rate_limits = config.get("rate_limits", {"max_per_minute": 30, "max_per_hour": 500})
        self.suspicious_patterns = self._load_suspicious_patterns()
        self.confirmation_required_actions = [
            "delete_data", "modify_ethics",
            "execute_code",
        ]
        
        # تتبع الاستخدام
        self.request_log: List[Dict] = []
        self.blocked_actions: List[Dict] = []

    def _load_suspicious_patterns(self) -> List[Dict]:
        """أنماط مشبوهة للكشف عنها"""
        return [
            {"pattern": "ignore previous", "risk": "high", "action": "flag"},
            {"pattern": "system prompt", "risk": "medium", "action": "log"},
            {"pattern": "jailbreak", "risk": "critical", "action": "block"},
            {"pattern": "bypass ethics", "risk": "critical", "action": "block"},
            {"pattern": "pretend you are", "risk": "low", "action": "log"},
            {"pattern": "act as if", "risk": "low", "action": "log"},
        ]

    async def check(self, user_input: str, user_id: str = "owner") -> Dict[str, Any]:
        """
        فحص أمني شامل عبر الطبقات الخمس.
        
        Returns:
            {"allowed": bool, "layer": str, "reason": str, "requires_confirmation": bool}
        """
        # الطبقة 1: المصادقة
        auth_result = self._layer_auth(user_id)
        if not auth_result["allowed"]:
            return auth_result

        # الطبقة 2: السلوك
        behavior_result = self._layer_behavior(user_input)
        if not behavior_result["allowed"]:
            return behavior_result

        # الطبقة 3: التأكيد
        confirm_result = self._layer_confirmation(user_input)
        if confirm_result["requires_confirmation"]:
            return confirm_result

        # الطبقة 4: الأخلاق (مدمجة مع ethics_gate)
        # هذه الطبقة تُفعّل عبر المحرك الرئيسي

        # الطبقة 5: Sandbox
        sandbox_result = self._layer_sandbox(user_input)
        if not sandbox_result["allowed"]:
            return sandbox_result

        # تسجيل الطلب
        self.request_log.append({
            "user_id": user_id,
            "input_hash": hashlib.sha256(user_input.encode()).hexdigest()[:16],
            "timestamp": datetime.now().isoformat(),
            "allowed": True
        })

        return {"allowed": True, "layer": "all", "reason": "تم اجتياز كل الطبقات"}

    def _layer_auth(self, user_id: str) -> Dict[str, Any]:
        """الطبقة 1: المصادقة"""
        if user_id not in self.authorized_users:
            return {
                "allowed": False,
                "layer": "auth",
                "reason": f"مستخدم غير مصرح: {user_id}"
            }
        return {"allowed": True, "layer": "auth"}

    def _layer_behavior(self, user_input: str) -> Dict[str, Any]:
        """الطبقة 2: فحص السلوك"""
        input_lower = user_input.lower()
        
        for pattern_info in self.suspicious_patterns:
            if pattern_info["pattern"] in input_lower:
                if pattern_info["action"] == "block":
                    self.blocked_actions.append({
                        "pattern": pattern_info["pattern"],
                        "input_hash": hashlib.sha256(user_input.encode()).hexdigest()[:16],
                        "timestamp": datetime.now().isoformat()
                    })
                    return {
                        "allowed": False,
                        "layer": "behavior",
                        "reason": f"نمط مشبوه: {pattern_info['pattern']}"
                    }
                elif pattern_info["action"] == "flag":
                    logger.warning(f"سلوك مشبوه: {pattern_info['pattern']}")
        
        # فحص معدل الطلبات
        recent = [r for r in self.request_log 
                  if (datetime.now() - datetime.fromisoformat(r["timestamp"])).seconds < 60]
        if len(recent) >= self.rate_limits["max_per_minute"]:
            return {
                "allowed": False,
                "layer": "behavior",
                "reason": "تجاوز معدل الطلبات"
            }
        
        return {"allowed": True, "layer": "behavior"}

    def _layer_confirmation(self, user_input: str) -> Dict[str, Any]:
        """الطبقة 3: طلب تأكيد للأعمال الحساسة"""
        for action in self.confirmation_required_actions:
            if action in user_input.lower():
                return {
                    "allowed": False,
                    "layer": "confirmation",
                    "reason": f"يتطلب تأكيد المستخدم: {action}",
                    "requires_confirmation": True,
                    "action": action
                }
        return {"allowed": True, "layer": "confirmation", "requires_confirmation": False}

    def _layer_sandbox(self, user_input: str) -> Dict[str, Any]:
        """الطبقة 5: فحص بيئة التنفيذ"""
        # التأكد من عدم طلب وصول لنظام التشغيل مباشرة
        dangerous_commands = ["rm -rf", "format", "del /", "sudo rm", "mkfs"]
        for cmd in dangerous_commands:
            if cmd in user_input.lower():
                return {
                    "allowed": False,
                    "layer": "sandbox",
                    "reason": f"أمر خطير محظور: {cmd}"
                }
        return {"allowed": True, "layer": "sandbox"}

    def authorize_user(self, user_id: str, token: str) -> bool:
        """إضافة مستخدم مصرح"""
        if user_id not in self.authorized_users:
            self.authorized_users.append(user_id)
            logger.info(f"تمت مصادقة مستخدم: {user_id}")
            return True
        return False

    def get_security_stats(self) -> Dict:
        """إحصائيات أمنية"""
        return {
            "total_requests": len(self.request_log),
            "blocked_actions": len(self.blocked_actions),
            "authorized_users": len(self.authorized_users),
            "last_blocked": self.blocked_actions[-1] if self.blocked_actions else None
        }
