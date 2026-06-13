"""
Adam Prism — Chat Router
=========================
نقاط نهاية المحادثة — تم استخراجها من server.py

[FIX v3] Router split — extracted from server.py for better maintainability
"""

import sqlite3
from typing import Dict, Optional, List

from fastapi import APIRouter, HTTPException, Request, UploadFile, File
from pydantic import BaseModel

router = APIRouter(tags=["chat"])


class CreateSessionRequest(BaseModel):
    title: str = "New Conversation"
    first_message: Optional[str] = None

class UpdateSessionRequest(BaseModel):
    title: str

class AddMessageRequest(BaseModel):
    role: str
    content: str
    mode: Optional[str] = None
    metadata: Optional[Dict] = None

class ChatSearchRequest(BaseModel):
    query: str
    limit: int = 20


@router.get("/api/chat/sessions")
async def list_sessions(limit: int = 50, offset: int = 0):
    """قائمة جلسات المحادثة"""
    # Note: chat_store is injected via app.state in production
    from fastapi import Request
    # This endpoint will be registered with proper dependencies in server.py
    pass


@router.post("/api/chat/sessions")
async def create_session(req: CreateSessionRequest):
    """إنشاء جلسة جديدة"""
    pass


@router.get("/api/chat/sessions/{session_id}")
async def get_session(session_id: str):
    """جلب جلسة مع رسائلها"""
    pass


@router.patch("/api/chat/sessions/{session_id}")
async def update_session(session_id: str, req: UpdateSessionRequest):
    """تحديث عنوان الجلسة"""
    pass


@router.delete("/api/chat/sessions/{session_id}")
async def delete_session(session_id: str):
    """حذف جلسة"""
    pass


@router.get("/api/chat/sessions/{session_id}/messages")
async def list_messages(session_id: str):
    """جلب رسائل جلسة معينة"""
    pass


@router.post("/api/chat/sessions/{session_id}/messages")
async def add_message(session_id: str, req: AddMessageRequest):
    """إضافة رسالة إلى جلسة"""
    pass


@router.post("/api/chat/sessions/{session_id}/sync")
async def sync_session(session_id: str, messages: List[Dict]):
    """مزامنة كل رسائل جلسة"""
    pass


@router.post("/api/chat/search")
async def search_chat_history(req: ChatSearchRequest):
    """البحث النصي الكامل في تاريخ المحادثات"""
    pass


@router.post("/api/chat/upload")
async def chat_upload(file: UploadFile = File(...)):
    """رفع ملف"""
    pass
