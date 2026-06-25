"""Adam Prism Skill Curator — creates and manages executable skills.
Skills are markdown files with YAML frontmatter stored in ~/.adam/skills/"""

import os
import json
import yaml
from pathlib import Path
from datetime import datetime
from typing import Any


class SkillCurator:
    def __init__(self, skills_dir: str | None = None):
        self.skills_dir = Path(skills_dir or os.path.expanduser("~/.adam/skills"))
        self.skills_dir.mkdir(parents=True, exist_ok=True)
        self._index: dict[str, dict] = {}
        self._load_index()

    def _load_index(self):
        index_file = self.skills_dir / "index.json"
        if index_file.exists():
            try:
                self._index = json.loads(index_file.read_text())
            except Exception:
                self._index = {}
        # Scan for new skills
        for skill_file in self.skills_dir.glob("*.md"):
            name = skill_file.stem
            if name not in self._index:
                self._index[name] = {
                    "name": name,
                    "file": str(skill_file),
                    "created": datetime.now().isoformat(),
                    "version": 1,
                    "category": "auto",
                }
        self._save_index()

    def _save_index(self):
        (self.skills_dir / "index.json").write_text(json.dumps(self._index, indent=2, ensure_ascii=False))

    def get_skill_index(self) -> list[dict]:
        return list(self._index.values())

    def create_skill(self, name: str, content: str, category: str = "auto") -> dict:
        skill_file = self.skills_dir / f"{name}.md"
        skill_file.write_text(content)
        self._index[name] = {
            "name": name,
            "file": str(skill_file),
            "created": datetime.now().isoformat(),
            "version": 1,
            "category": category,
        }
        self._save_index()
        return self._index[name]

    def load_skill(self, name: str) -> str | None:
        skill_file = self.skills_dir / f"{name}.md"
        if skill_file.exists():
            return skill_file.read_text()
        return None

    def curate(self, conversation: str = "", **kwargs) -> list[dict]:
        """Generate skills from conversation patterns."""
        created = []
        triggers = {
            "security_scan": ["فحص", "scan", "security", "أمن"],
            "code_review": ["كود", "code", "review", "مراجعة"],
            "data_analysis": ["بيانات", "data", "analysis", "تحليل"],
            "system_check": ["نظام", "system", "check", "حالة", "مساحة"],
            "memory_ops": ["ذاكرة", "memory", "حفظ", "تذكر"],
        }

        conv_lower = conversation.lower()
        for skill_name, keywords in triggers.items():
            if any(kw in conv_lower for kw in keywords):
                if skill_name not in self._index:
                    content = _get_skill_template(skill_name)
                    skill = self.create_skill(skill_name, content, category=skill_name)
                    created.append(skill)
        return created


def _get_skill_template(name: str) -> str:
    templates = {
        "security_scan": """# Security Scanner
Description: Scan system for security vulnerabilities
Usage: Called automatically when user asks about security
Steps:
1. Check open ports with `ss -tlnp`
2. Check running services with `systemctl list-units --type=service`
3. Check failed login attempts with `journalctl -u ssh --since "24 hours ago" | grep Failed`
4. Generate summary report
""",
        "code_review": """# Code Reviewer
Description: Review code for bugs and improvements
Usage: Triggered when user shares code
Steps:
1. Parse code structure
2. Check for common vulnerabilities (SQL injection, XSS, etc.)
3. Suggest improvements
4. Generate review report
""",
        "data_analysis": """# Data Analyzer
Description: Analyze structured data from files
Usage: Triggered when user uploads data files
Steps:
1. Parse file format (JSON, CSV, YAML)
2. Extract key metrics and patterns
3. Generate visualization-ready summary
4. Recommend actions based on findings
""",
        "system_check": """# System Health Check
Description: Check system resources and health
Usage: Triggered when user asks about system status
Steps:
1. Check CPU usage
2. Check RAM usage
3. Check disk space
4. Check running services
5. Generate health report
""",
        "memory_ops": """# Memory Manager
Description: Store and retrieve persistent memories
Usage: Called when user wants to remember or recall information
Steps:
1. Store new information with priority and tags
2. Search existing memories by keyword
3. Retrieve specific memories by ID
4. Reflect on recent memories
""",
    }
    return templates.get(name, f"# {name}\nAuto-generated skill\n")
