#!/usr/bin/env python3
"""
Example 04: Skill Creation - إنشاء Skill مخصص
==============================================
هذا المثال يوضح كيفية إنشاء skill جديدة لتوسيع قدرات آدم
دون تعديل الكود الأساسي. الـ Skills تُخزن كملفات Markdown
مع frontmatter JSON.
"""

import os
import json
from pathlib import Path


def create_skill_file():
    """إنشاء ملف skill في المجلد الصحيح"""
    
    # مجلد الـ skills المحلي
    skills_dir = Path.home() / ".adam" / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)
    
    skill_content = '''---
name: "code-review"
description: "مراجعة كود شاملة مع اقتراحات تحسين"
triggers: ["راجع الكود", "code review", "افحص الكود", "تحسين الكود"]
category: "development"
---

When to Use
عندما يطلب المستخدم مراجعة كود أو تحسينه - سواء كان كود جديد أو كود موجود.

Procedure
1. اطلب من المستخدم مشاركة الكود (ملف، رابط، أو لصق مباشر)
2. حدد اللغة والإطار المستخدم
3. افحص الجوانب التالية:
   - **الأمان**: ثغرات واضحة، SQL injection، XSS، hardcoded secrets
   - **الأداء**: تعقيد خوارزمي، استعلامات N+1، memory leaks
   - **النظافة**: تسمية، تكرار، تعقيد دالة، التعليقات
   - **الاختبارات**: هل يوجد اختبارات؟ تغطية الحالات الحرجة؟
   - **التوثيق**: docstrings، README، type hints
4. قدم الملخص: نقاط القوة، المشاكل الحرجة، اقتراحات التحسين
5. اكتب الكود المحسن إذا طُلب

Examples
المستخدم: "راجع هذا الكود: [كود Python]"
آدم: يفحص ويقدم تقرير منظم مع كود محسن

المستخدم: "افحص أمان هذا API endpoint"
آدم: يركز على authentication، authorization، input validation، rate limiting
'''

    skill_path = skills_dir / "code-review.md"
    skill_path.write_text(skill_content, encoding="utf-8")
    print(f"✅ تم إنشاء skill: {skill_path}")


def create_skill_via_api():
    """مثال: إنشاء skill عبر API (للتكامل البرمجي)"""
    
    skill_data = {
        "name": "security-audit",
        "description": "فحص أمني للمشاريع والكود",
        "triggers": ["فحص أمني", "security audit", "ثغرات", "vulnerability scan"],
        "category": "security",
        "content": """---
When to Use
عند طلب فحص أمني لمشروع، كود، أو بنية تحتية.

Procedure
1. حدد النطاق: تطبيق ويب، API، Infrastruktur، كود مصدر
2. افحص حسب OWASP Top 10:
   - Injection (SQL, NoSQL, Command, LDAP)
   - Broken Authentication
   - Sensitive Data Exposure
   - XML External Entities (XXE)
   - Broken Access Control
   - Security Misconfiguration
   - Cross-Site Scripting (XSS)
   - Insecure Deserialization
   - Using Components with Known Vulnerabilities
   - Insufficient Logging & Monitoring
3. أدوات مقترحة: bandit, safety, semgrep, trivy
4. قدم تقرير: خطورة، تأثير، إصلاح مقترح
"""
    }
    
    # يمكن حفظها كملف JSON للاستيراد
    import json
    skills_dir = Path.home() / ".adam" / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)
    
    (skills_dir / "security-audit.json").write_text(
        json.dumps(skill_data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"✅ تم إنشاء skill JSON: {skills_dir / 'security-audit.json'}")


async def main():
    print("🛠️ Adam Prism - Skill Creation Example")
    print("=" * 50)
    
    create_skill_file()
    create_skill_via_api()
    
    print()
    print("📁 مواقع تخزين الـ Skills:")
    print(f"   - محلي: ~/.adam/skills/")
    print(f"   - مشروع: ./data/skills/ (للـ version control)")
    print()
    print("💡 هيكل الـ Skill (Markdown مع Frontmatter):")
    print("   ---")
    print("   name: 'skill-name'")
    print("   description: 'وصف مختصر'")
    print("   triggers: ['كلمة محفزة 1', 'كلمة محفزة 2']")
    print("   category: 'development|security|analysis|...'")
    print("   ---")
    print()
    print("   When to Use")
    print("   متى تستخدم الـ skill")
    print()
    print("   Procedure")
    print("   1. خطوة أولى")
    print("   2. خطوة ثانية")
    print()
    print("   Examples")
    print("   أمثلة للاستخدام")
    print()
    print("🔄 لإعادة تحميل الـ skills:")
    print("   - إعادة تشغيل السيرفر")
    print("   - أو POST /api/skills/reload")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())