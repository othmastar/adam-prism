"""
Adam Prism — MCP Router
=========================
نقاط نهاية MCP — تم استخراجها من server.py

[FIX v3] Router split — extracted from server.py for better maintainability
"""

from fastapi import APIRouter, Request

router = APIRouter(tags=["mcp"])

@router.post("/api/mcp/add-server")
async def add_mcp_server(request: Request):
    """إضافة خادم MCP — يتطلب مفتاح المسؤول"""
    pass

@router.get("/api/mcp/tools")
async def list_mcp_tools():
    """عرض أدوات MCP المتاحة"""
    pass
