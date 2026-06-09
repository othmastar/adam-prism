"""
Adam Prism Client — Typed response models
جميع نماذج البيانات مع Type Hints
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ─── Chat ────────────────────────────────────────────────────────

@dataclass
class ToolRecord:
    name: str
    params: Dict[str, Any] = field(default_factory=dict)
    success: bool = False
    error: Optional[str] = None


@dataclass
class ChatResponse:
    response: str
    mode: str = "communicator"
    intent: Optional[Dict[str, Any]] = None
    knowledge_used: int = 0
    tool_calls_made: int = 0
    tools_used: List[str] = field(default_factory=list)
    tool_records: List[ToolRecord] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    cycle: int = 0
    duration_ms: Optional[int] = None
    reason: Optional[str] = None
    audio_url: Optional[str] = None
    permission_pending: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dict(cls, data: dict) -> ChatResponse:
        records = [ToolRecord(**r) for r in data.pop("tool_records", [])]
        return cls(**data, tool_records=records)


# ─── Status ──────────────────────────────────────────────────────

@dataclass
class SystemStatus:
    status: str
    inference_mode: Optional[str] = None
    lora_server_url: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> SystemStatus:
        return cls(**data)


# ─── Knowledge ────────────────────────────────────────────────────

@dataclass
class KnowledgeResult:
    id: str
    score: float
    text: str
    source: Optional[str] = None
    collection: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> KnowledgeResult:
        return cls(**data)


@dataclass
class KnowledgeSearchResponse:
    results: List[KnowledgeResult] = field(default_factory=list)
    count: int = 0

    @classmethod
    def from_dict(cls, data: dict) -> KnowledgeSearchResponse:
        results = [KnowledgeResult.from_dict(r) for r in data.get("results", [])]
        return cls(results=results, count=data.get("count", len(results)))


@dataclass
class AddKnowledgeResponse:
    success: bool
    collection: str
    qdrant_collection: str
    id: int
    text_preview: str


@dataclass
class UploadKnowledgeResponse:
    success: bool
    filename: str
    collection: str
    qdrant_collection: str
    chunks: int
    ids: List[str]
    total_chars: int


@dataclass
class CollectionInfo:
    name: str
    points: int


@dataclass
class CollectionsResponse:
    collections: List[CollectionInfo] = field(default_factory=list)
    total: int = 0

    @classmethod
    def from_dict(cls, data: dict) -> CollectionsResponse:
        collections = [CollectionInfo(**c) for c in data.get("collections", [])]
        return cls(collections=collections, total=data.get("total", 0))


# ─── Sessions ─────────────────────────────────────────────────────

@dataclass
class Session:
    id: str
    title: str
    created_at: float
    updated_at: float
    messages: Optional[List[Dict[str, Any]]] = None


@dataclass
class SessionListResponse:
    sessions: List[Session] = field(default_factory=list)
    total: int = 0

    @classmethod
    def from_dict(cls, data: dict) -> SessionListResponse:
        sessions = [Session(**s) for s in data.get("sessions", [])]
        return cls(sessions=sessions, total=data.get("total", len(sessions)))


# ─── Chat History Search ──────────────────────────────────────────

@dataclass
class ChatSearchResult:
    id: str
    session_id: str
    role: str
    content: str
    mode: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: float = 0.0


@dataclass
class ChatSearchResponse:
    results: List[ChatSearchResult] = field(default_factory=list)
    count: int = 0

    @classmethod
    def from_dict(cls, data: dict) -> ChatSearchResponse:
        results = [ChatSearchResult(**r) for r in data.get("results", [])]
        return cls(results=results, count=data.get("count", len(results)))


# ─── Skills ───────────────────────────────────────────────────────

@dataclass
class SkillInfo:
    name: str
    description: str
    path: str


@dataclass
class SkillsResponse:
    skills: List[SkillInfo] = field(default_factory=list)
    error: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> SkillsResponse:
        skills = [SkillInfo(**s) for s in data.get("skills", [])]
        return cls(skills=skills, error=data.get("error"))


@dataclass
class LoadSkillResponse:
    success: bool
    name: str
    result: str


# ─── Plugins ──────────────────────────────────────────────────────

@dataclass
class PluginInfo:
    name: str
    version: str
    description: Optional[str] = None


@dataclass
class PluginsResponse:
    plugins: List[PluginInfo] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> PluginsResponse:
        plugins = [PluginInfo(**p) if isinstance(p, dict) else PluginInfo(name=p, version="") for p in data.get("plugins", [])]
        return cls(plugins=plugins)


@dataclass
class LoadPluginResponse:
    status: str
    plugins: List[PluginInfo] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> LoadPluginResponse:
        plugins = [PluginInfo(**p) if isinstance(p, dict) else PluginInfo(name=p, version="") for p in data.get("plugins", [])]
        return cls(status=data.get("status", ""), plugins=plugins)


# ─── Channels ─────────────────────────────────────────────────────

@dataclass
class ChannelStatus:
    name: str
    running: bool
    webhook: bool = False

    @classmethod
    def from_dict(cls, data: dict) -> ChannelStatus:
        return cls(**data)


@dataclass
class ChannelsResponse:
    channels: Dict[str, ChannelStatus] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> ChannelsResponse:
        chs = data.get("channels", {})
        channels = {k: ChannelStatus.from_dict(v) if isinstance(v, dict) else ChannelStatus(name=k, running=False) for k, v in chs.items()}
        return cls(channels=channels)


@dataclass
class ToggleChannelResponse:
    status: str
    running: bool


# ─── Health / Diagnostics ─────────────────────────────────────────

@dataclass
class HealthCheck:
    check: str
    status: str  # "pass" | "fail"


@dataclass
class HealthSummary:
    passed: int
    failed: int
    total: int


@dataclass
class DiagnosticsResponse:
    status: str
    timestamp: str
    checks: List[HealthCheck] = field(default_factory=list)
    summary: Optional[HealthSummary] = None

    @classmethod
    def from_dict(cls, data: dict) -> DiagnosticsResponse:
        checks = [HealthCheck(**c) for c in data.get("checks", [])]
        summary = HealthSummary(**data["summary"]) if data.get("summary") else None
        return cls(status=data["status"], timestamp=data["timestamp"], checks=checks, summary=summary)


@dataclass
class SystemHealth:
    api: str
    timestamp: str
    uptime_seconds: Optional[float] = None
    engine: Dict[str, Any] = field(default_factory=dict)
    system: Dict[str, Any] = field(default_factory=dict)
    ollama: Optional[Dict[str, Any]] = None
    qdrant: Optional[Dict[str, Any]] = None
    trace_recorder: Optional[Dict[str, Any]] = None


# ─── Metrics ──────────────────────────────────────────────────────

@dataclass
class Metrics:
    data: Dict[str, Any] = field(default_factory=dict)


# ─── Ollama ───────────────────────────────────────────────────────

@dataclass
class OllamaModelsResponse:
    models: List[str] = field(default_factory=list)
    error: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> OllamaModelsResponse:
        return cls(models=data.get("models", []), error=data.get("error"))


@dataclass
class SelectOllamaModelResponse:
    success: bool
    model: str


# ─── Voice ────────────────────────────────────────────────────────

@dataclass
class TranscriptionResponse:
    text: str
    duration: float

    @classmethod
    def from_dict(cls, data: dict) -> TranscriptionResponse:
        return cls(**data)


# ─── Scheduler ────────────────────────────────────────────────────

@dataclass
class ScheduledJob:
    id: str
    name: Optional[str] = None
    trigger: Optional[str] = None
    next_run: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> ScheduledJob:
        return cls(**data)


@dataclass
class ScheduledJobsResponse:
    jobs: List[ScheduledJob] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> ScheduledJobsResponse:
        jobs = [ScheduledJob.from_dict(j) if isinstance(j, dict) else ScheduledJob(id=str(j)) for j in data.get("jobs", [])]
        return cls(jobs=jobs)


# ─── Generic ──────────────────────────────────────────────────────

@dataclass
class GenericResponse:
    data: Dict[str, Any]
