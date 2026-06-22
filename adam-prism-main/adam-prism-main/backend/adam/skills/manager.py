import builtins
import logging
from pathlib import Path

from .base import Skill

logger = logging.getLogger("adam_prism.skills")

class SkillManager:
    """مدير المهارات — يكتشف، يحمل، يشغل المهارات"""

    def __init__(self, engine=None):
        self.engine = engine
        self._skills: dict[str, Skill] = {}

        # مسار البحث: built-in + user
        self._builtin_dir = Path(__file__).parent / "builtin"
        self._user_dir = Path.home() / ".adam" / "skills"

    def discover(self) -> list[str]:
        """اكتشاف كل المهارات المتاحة (built-in + user)"""
        found = []

        # Built-in: .md files and .py subclasses
        if self._builtin_dir.exists():
            for f in sorted(self._builtin_dir.iterdir()):
                if f.suffix == ".md" or (f.suffix == ".py" and f.stem != "__init__"):
                    found.append(str(f.absolute()))

        # User skills
        if self._user_dir.exists():
            for f in sorted(self._user_dir.iterdir()):
                if f.suffix in (".md", ".py"):
                    found.append(str(f.absolute()))

        return found

    async def load(self, path: str) -> Skill | None:
        """تحميل مهارة من ملف"""
        p = Path(path)
        if not p.exists():
            return None

        try:
            if p.suffix == ".md":
                skill = Skill.from_markdown(str(p))
            elif p.suffix == ".py":
                skill = self._load_python_skill(p)
            else:
                return None

            await skill.on_load(self.engine)
            name = skill.name or p.stem
            self._skills[name] = skill
            logger.info(f"📘 Skill loaded: {name} — {skill.description[:60]}")
            return skill
        except Exception:
            logger.exception("⚠️ Failed to load skill {path}:")
            return None

    def _load_python_skill(self, path: Path) -> Skill:
        """تحميل مهارة من ملف بايثون"""
        import importlib.util
        spec = importlib.util.spec_from_file_location(path.stem, str(path))
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load {path}")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        for attr in dir(mod):
            obj = getattr(mod, attr)
            if isinstance(obj, type) and issubclass(obj, Skill) and obj is not Skill:
                return obj()

        raise ValueError(f"No Skill subclass found in {path}")

    async def load_all(self) -> int:
        """تحميل كل المهارات"""
        paths = self.discover()
        count = 0
        for p in paths:
            if await self.load(p):
                count += 1
        return count

    def get(self, name: str) -> Skill | None:
        return self._skills.get(name)

    def list(self) -> list[dict]:
        return [
            {"name": s.name, "description": s.description,
             "version": s.version, "triggers": s.triggers}
            for s in self._skills.values()
        ]

    def match(self, message: str) -> builtins.list[Skill]:
        """لاقي المهارات اللي triggers بتاعتها match الرسالة"""
        msg_lower = message.lower()
        matched = []
        for skill in self._skills.values():
            for trigger in skill.triggers:
                if trigger.lower() in msg_lower:
                    matched.append(skill)
                    break
        return matched

    async def unload(self, name: str) -> bool:
        skill = self._skills.pop(name, None)
        if skill:
            await skill.on_unload()
            return True
        return False

    async def clear(self):
        for skill in self._skills.values():
            await skill.on_unload()
        self._skills.clear()
