"""أدوات المعرفة — Qdrant search + Preferences + Notebook"""

import json
import os
from datetime import datetime
from typing import Dict

from adam.core.permissions import classify_tool, log_permission


class KnowledgeMixin:
    """Mixin: knowledge search + preferences + notebook"""

    async def _tool_knowledge(self, params: Dict) -> Dict:
        query = params.get("query", "")
        top_k = params.get("top_k", 3)
        if not query:
            return {"success": False, "error": "مفيش query"}
        try:
            from urllib.parse import urlparse
            from qdrant_client import AsyncQdrantClient
            qdrant_url = self.config.get("qdrant_url", "http://localhost:6333")
            pu = urlparse(qdrant_url)
            ollama_base = self.config.get("ollama_base", "http://localhost:11434")

            if not hasattr(self, "_qdrant_client") or self._qdrant_client is None:
                self._qdrant_client = AsyncQdrantClient(
                    host=pu.hostname or "localhost", port=pu.port or 6333
                )
            client = self._qdrant_client

            hc = await self.shared_clients.get("ollama", ollama_base, timeout=10)
            o_resp = await hc.post("/api/embeddings", json={
                "model": "nomic-embed-text", "prompt": query
            })
            o_data = o_resp.json()
            query_vec = o_data.get("embedding")

            collected = []
            if query_vec and len(query_vec) == 768:
                cols = await client.get_collections()
                for col in cols.collections:
                    try:
                        sr = await client.query_points(collection_name=col.name, query=query_vec, limit=top_k)
                        for hit in sr.points:
                            text = (hit.payload or {}).get("text", "")
                            if text:
                                collected.append({"collection": col.name, "text": text, "score": hit.score})
                    except Exception:
                        pass
            if not collected:
                keywords = query.lower().split()
                cols = await client.get_collections()
                for col in cols.collections:
                    try:
                        points = await client.scroll(col.name, limit=200, with_payload=True, with_vectors=False)
                        for pt in points[0]:
                            text = (pt.payload or {}).get("text", "")
                            if text and any(kw in text.lower() for kw in keywords):
                                collected.append({"collection": col.name, "text": text, "score": 0.5})
                    except Exception:
                        pass
            collected.sort(key=lambda x: -x["score"])
            return {"success": True, "results": collected[:top_k], "count": min(len(collected), top_k)}
        except Exception as e:
            return {"success": False, "error": f"قاعدة المعرفة غير متصلة: {e}"}

    async def _tool_preferences(self, tool_name: str, params: Dict) -> Dict:
        if tool_name == "request_permission":
            action = params.get("action", params.get("tool", ""))
            reason = params.get("reason", "")
            level = params.get("level", "once")
            cat = classify_tool(action)
            self.permission.pending_request = {
                "category": cat, "tool": action, "reason": reason,
                "level": level, "tool_params": params.get("params", {}),
                "timestamp": datetime.now().isoformat(),
            }
            log_permission("requested", action, cat, reason, level, "pending")
            return {"success": True, "pending": True, "request_id": self.session_id,
                    "message": f"طلب صلاحية لفئة '{cat}'. المستخدم سيقرر.",
                    "category": cat, "action": action, "reason": reason, "level": level}

        if tool_name == "check_preferences":
            tool = params.get("tool", "")
            category = params.get("category", "")
            if category:
                pred = self.learner.predict(tool, category)
                summary = self.learner.get_summary()
                return {"success": True, "prediction": pred, "category": category,
                        "stats": summary.get(category, {}), "all_preferences": summary}
            return {"success": True, "prediction": "unknown", "all_preferences": self.learner.get_summary()}

        if tool_name == "notebook_update_profile":
            section = params.get("section", "")
            data = params.get("data", {})
            if not section:
                return {"success": False, "error": "مفيش section"}
            if not data:
                return {"success": False, "error": "مفيش بيانات"}
            try:
                notes_dir = self.config.get("notebook_dir", os.path.expanduser("~/.local/adam_notebook"))
                os.makedirs(notes_dir, exist_ok=True)
                profile_path = os.path.join(notes_dir, "user_profile.json")
                profile = {}
                if os.path.exists(profile_path):
                    with open(profile_path, "r") as f:
                        profile = json.load(f)
                if section not in profile:
                    profile[section] = {}
                profile[section].update(data)
                with open(profile_path, "w") as f:
                    json.dump(profile, f, ensure_ascii=False, indent=2)
                return {"success": True, "message": f"تم تحديث {section}"}
            except Exception as e:
                return {"success": False, "error": str(e)}

        return {"success": False, "error": "أداة تفضيلات غير معروفة"}
