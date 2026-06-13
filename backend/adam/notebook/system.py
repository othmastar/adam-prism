"""
Adam Prism - النوته الدائمة (Always-On Notebook)
=================================================
دفتر ملاحظات آدم الذي لا يفارقه أبداً.
يسجّل كل شئ: ملاحظات، روابط، أسئلة، إحصائيات، ملخصات.
"""

import json
import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger("adam_prism.notebook")


class AdamNotebook:
    """
    دفتر ملاحظات آدم الدائم.
    
    البنية:
    - daily/         → ملاحظات يومية
    - connections/   → روابط بين الأفكار  
    - pending/       → أسئلة ونقاط معلقة
    - summaries/     → ملخصات ما تعلمه
    - user_profile/  → ملف تعلم شخصية المستخدم (للتدريب المستقبلي)
    - index.json     → فهرس قابل للبحث
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_path = Path(config.get("notebook_path", "./notebook"))
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # إنشاء المجلدات
        (self.base_path / "daily").mkdir(exist_ok=True)
        (self.base_path / "connections").mkdir(exist_ok=True)
        (self.base_path / "pending").mkdir(exist_ok=True)
        (self.base_path / "summaries").mkdir(exist_ok=True)
        (self.base_path / "user_profile").mkdir(exist_ok=True)
        
        # الفهرس
        self.index_path = self.base_path / "index.json"
        self.index = self._load_index()
        
        # الإحصائيات اليومية
        self.daily_stats = {
            "pages_read": 0,
            "ideas_extracted": 0,
            "connections_made": 0,
            "questions_asked": 0,
            "summaries_written": 0,
            "profile_updates": 0
        }

    def _load_index(self) -> Dict:
        """تحميل الفهرس"""
        if self.index_path.exists():
            with open(self.index_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"entries": [], "last_updated": datetime.now().isoformat()}

    def _save_index(self):
        """حفظ الفهرس"""
        self.index["last_updated"] = datetime.now().isoformat()
        with open(self.index_path, "w", encoding="utf-8") as f:
            json.dump(self.index, f, ensure_ascii=False, indent=2)

    async def record(self, entry: Dict[str, Any]):
        """تسجيل مدخل في الدفتر"""
        timestamp = datetime.now()
        date_str = timestamp.strftime("%Y-%m-%d")
        time_str = timestamp.strftime("%H:%M:%S")
        
        # 1. إضافة لليومية
        daily_file = self.base_path / "daily" / f"{date_str}.md"
        entry_text = self._format_entry(entry, time_str)
        
        with open(daily_file, "a", encoding="utf-8") as f:
            f.write(entry_text + "\n---\n")
        
        # 2. تحديث الفهرس
        self.index["entries"].append({
            "date": date_str,
            "time": time_str,
            "type": entry.get("intent", {}).get("intent_type", "general"),
            "mode": entry.get("mode", "communicator"),
            "cycle": entry.get("cycle", 0),
            "summary": str(entry.get("input", ""))[:100]
        })
        
        # حفظ آخر 1000 مدخل فقط في الفهرس
        if len(self.index["entries"]) > 1000:
            self.index["entries"] = self.index["entries"][-1000:]
        self._save_index()
        
        # 3. تحديث الإحصائيات
        self.daily_stats["summaries_written"] += 1

    async def add_connection(self, idea_a: str, idea_b: str, connection_type: str, evidence: str = ""):
        """إضافة ربط بين فكرتين"""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        conn_file = self.base_path / "connections" / f"link_{timestamp}.json"
        
        connection = {
            "idea_a": idea_a,
            "idea_b": idea_b,
            "type": connection_type,
            "evidence": evidence,
            "timestamp": datetime.now().isoformat()
        }
        
        with open(conn_file, "w", encoding="utf-8") as f:
            json.dump(connection, f, ensure_ascii=False, indent=2)
        
        self.daily_stats["connections_made"] += 1
        logger.info(f"🔗 ربط جديد: {idea_a[:30]} ↔ {idea_b[:30]}")

    async def add_pending_question(self, question: str, context: str = ""):
        """إضافة سؤال معلق للعودة إليه لاحقاً"""
        pending_file = self.base_path / "pending" / "questions.md"
        
        with open(pending_file, "a", encoding="utf-8") as f:
            f.write(f"\n## [{datetime.now().strftime('%Y-%m-%d %H:%M')}]\n")
            f.write(f"**السؤال**: {question}\n")
            if context:
                f.write(f"**السياق**: {context}\n")
            f.write("**الحالة**: ⏳ معلق\n")
        
        self.daily_stats["questions_asked"] += 1

    async def update_user_profile(self, section: str, data: Dict[str, Any]):
        """تحديث ملف تعلم شخصية المستخدم (يكتب أو يدمج في ملف JSON)"""
        profile_dir = self.base_path / "user_profile"
        profile_dir.mkdir(exist_ok=True)
        profile_file = profile_dir / f"{section}.json"
        
        existing = {}
        if profile_file.exists():
            with open(profile_file, "r", encoding="utf-8") as f:
                try:
                    existing = json.load(f)
                except json.JSONDecodeError:
                    existing = {}
        
        # دمج البيانات الجديدة (البيانات الجديدة تكسب)
        existing.update(data)
        existing["_updated"] = datetime.now().isoformat()
        
        with open(profile_file, "w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
        
        self.daily_stats["profile_updates"] = (self.daily_stats.get("profile_updates", 0) + 1)
        logger.info(f"📝 تم تحديث ملف تعلم المستخدم: {section}")

    async def load_user_profile(self) -> Dict[str, Any]:
        """تحميل كل ملفات تعلم المستخدم — ترجع dict موحد للسياق"""
        profile_dir = self.base_path / "user_profile"
        profile_dir.mkdir(exist_ok=True)
        
        profile = {}
        for f in sorted(profile_dir.glob("*.json")):
            section = f.stem
            try:
                with open(f, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                    profile[section] = data
            except (json.JSONDecodeError, Exception) as e:
                logger.warning(f"تعذر قراءة {f}: {e}")
        
        return profile

    async def add_summary(self, title: str, summary: str, source: str, key_topics: List[str] = None):
        """إضافة ملخص"""
        safe_title = "".join(c for c in title if c.isalnum() or c in " _-")[:50]
        summary_file = self.base_path / "summaries" / f"{safe_title}.md"
        
        with open(summary_file, "w", encoding="utf-8") as f:
            f.write(f"# {title}\n\n")
            f.write(f"**المصدر**: {source}\n")
            f.write(f"**التاريخ**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
            f.write(f"## الملخص\n{summary}\n\n")
            if key_topics:
                f.write(f"## المواضيع الرئيسية\n")
                for topic in key_topics:
                    f.write(f"- {topic}\n")
        
        self.daily_stats["summaries_written"] += 1

    async def get_daily_note(self, date: Optional[str] = None) -> str:
        """قراءة ملاحظات يوم معين"""
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        daily_file = self.base_path / "daily" / f"{date}.md"
        if daily_file.exists():
            with open(daily_file, "r", encoding="utf-8") as f:
                return f.read()
        return f"لا توجد ملاحظات ليوم {date}"

    async def get_pending_questions(self) -> List[Dict]:
        """استرجاع الأسئلة المعلقة"""
        pending_file = self.base_path / "pending" / "questions.md"
        if pending_file.exists():
            with open(pending_file, "r", encoding="utf-8") as f:
                return [{"content": f.read()}]
        return []

    def get_stats(self) -> Dict:
        """إحصائيات الدفتر"""
        return {
            "total_entries": len(self.index.get("entries", [])),
            "daily_stats": self.daily_stats,
            "index_last_updated": self.index.get("last_updated", "")
        }

    def _format_entry(self, entry: Dict, time_str: str) -> str:
        """تنسيق المدخل للكتابة"""
        lines = [
            f"### [{time_str}] دورة #{entry.get('cycle', '?')}",
            f"**الوضع**: {entry.get('mode', '?')} | **القصد**: {entry.get('intent', {}).get('intent_type', '?')}",
            f"**المدخل**: {str(entry.get('input', ''))[:200]}",
            f"**الرد**: {str(entry.get('response', ''))[:200]}",
            f"**المعرفة المستخدمة**: {entry.get('knowledge_used', 0)} عنصر"
        ]
        return "\n".join(lines)
