"""
Adam Prism — Engine Router
============================
نقاط نهاية المحرك — Ollama model management
"""

from fastapi import APIRouter

router = APIRouter(tags=["engine"])


@router.get("/api/ollama/models")
async def ollama_models():
    """قائمة نماذج Ollama"""
    pass


@router.post("/api/ollama/select")
async def ollama_select(req: dict):
    """اختيار نموذج Ollama"""
    pass
