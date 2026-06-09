"""
Adam Prism — Python SDK Client
===============================
عميل متكامل (sync + async) للتفاعل مع خادم Adam Prism API.

Examples:
    >>> from adam_prism_client import AdamPrismClient
    >>> client = AdamPrismClient("http://localhost:8000")
    >>> result = client.chat("ما اسمك؟")
    >>> print(result["response"])
"""

from .client import AdamPrismClient
from .errors import AdamPrismError, APIError, ConnectionError, NotFoundError, ServiceUnavailableError, TimeoutError
from .models import (
    AddKnowledgeResponse,
    ChannelStatus,
    ChatResponse,
    ChatSearchResponse,
    CollectionsResponse,
    DiagnosticsResponse,
    KnowledgeSearchResponse,
    LoadPluginResponse,
    LoadSkillResponse,
    Metrics,
    OllamaModelsResponse,
    PluginsResponse,
    ScheduledJobsResponse,
    SelectOllamaModelResponse,
    Session,
    SessionListResponse,
    SkillsResponse,
    SystemHealth,
    SystemStatus,
    ToggleChannelResponse,
    TranscriptionResponse,
    UploadKnowledgeResponse,
)

__all__ = [
    "AdamPrismClient",
    "AdamPrismError",
    "APIError",
    "ConnectionError",
    "NotFoundError",
    "ServiceUnavailableError",
    "TimeoutError",
    "AddKnowledgeResponse",
    "ChannelStatus",
    "ChatResponse",
    "ChatSearchResponse",
    "CollectionsResponse",
    "DiagnosticsResponse",
    "KnowledgeSearchResponse",
    "LoadPluginResponse",
    "LoadSkillResponse",
    "Metrics",
    "OllamaModelsResponse",
    "PluginsResponse",
    "ScheduledJobsResponse",
    "SelectOllamaModelResponse",
    "Session",
    "SessionListResponse",
    "SkillsResponse",
    "SystemHealth",
    "SystemStatus",
    "ToggleChannelResponse",
    "TranscriptionResponse",
    "UploadKnowledgeResponse",
]
