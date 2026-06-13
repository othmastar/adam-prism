

class Skill:
    """قاعدة المهارات — skill = معرفة + optional code"""

    name: str = ""
    description: str = ""
    version: str = "1.0.0"
    triggers: list[str] = []
    instructions: str = ""
    author: str = "adam"
    engine = None

    async def on_load(self, engine):
        self.engine = engine

    async def on_unload(self):
        pass

    async def on_trigger(self, message: str, context: dict) -> str | None:
        """لما skill يتفعل. يرجع instructions مخصصة أو None"""
        return self.instructions

    @classmethod
    def from_markdown(cls, path: str) -> "Skill":
        """Load skill from a Markdown file with JSON frontmatter"""
        import json
        with open(path, encoding="utf-8") as f:
            content = f.read()

        meta = {}
        instructions = content

        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                try:
                    meta = json.loads(parts[1])
                except json.JSONDecodeError:
                    meta = {}
                instructions = parts[2].strip()

        skill = cls()
        skill.name = meta.get("name", "")
        skill.description = meta.get("description", "")
        skill.version = str(meta.get("version", "1.0.0"))
        skill.triggers = meta.get("triggers", [])
        skill.author = meta.get("author", "unknown")
        skill.instructions = instructions
        return skill
