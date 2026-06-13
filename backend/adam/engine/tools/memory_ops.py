"""أدوات الذاكرة — store / recall / reflect"""


from core import memory_store


class MemoryToolsMixin:
    """Mixin: memory tools — store, recall, reflect"""

    async def _tool_memory(self, tool_name: str, params: dict) -> dict:
        try:
            if tool_name == "memory_store":
                content = params.get("content", "")
                tags = params.get("tags", "")
                priority_raw = params.get("priority", 3)
                if isinstance(priority_raw, str):
                    priority_map = {"high": 5, "medium": 3, "low": 1, "critical": 5, "urgent": 5}
                    priority = priority_map.get(priority_raw.strip().lower(), 3)
                else:
                    priority = int(priority_raw)
                priority = min(max(priority, 1), 5)
                if not content:
                    return {"success": False, "error": "مفيش محتوى للحفظ"}
                mem_id = memory_store.store(content, tags, priority)
                return {"success": True, "memory_id": mem_id, "message": "تم الحفظ"}

            elif tool_name == "memory_recall":
                query = params.get("query", "")
                limit = min(max(int(params.get("limit", 10)), 1), 50)
                if not query:
                    return {"success": False, "error": "مفيش استعلام بحث"}
                memories = memory_store.search(query, limit)
                return {"success": True, "count": len(memories), "memories": memories}

            elif tool_name == "memory_reflect":
                days = int(params.get("days", 1))
                reflection = memory_store.reflect(min(max(days, 1), 30))
                return {"success": True, "reflection": reflection, "stats": memory_store.stats()}
        except Exception as e:
            return {"success": False, "error": str(e)}
