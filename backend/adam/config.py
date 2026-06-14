"""
Adam Prism — Configuration
=============================
Backward-compatible config: engine accepts both dict and AdamConfig.
"""

import logging
import os
from dataclasses import dataclass, field

logger = logging.getLogger("adam_prism.config")

@dataclass
class AdamConfig:
    """Central configuration — partial coverage, dict fallback for rest."""
    inference_mode: str = "ollama"
    model_name: str = "adam-prism-v13:latest"
    ollama_base: str = "http://localhost:11434"
    qdrant_url: str = "http://localhost:6333"
    context_window: int = 4096
    token_budget: int = 4000
    max_conversation_history: int = 50
    embedding_model: str = "nomic-embed-text"
    lora_server_url: str = "http://localhost:8080"
    local_bin: str = os.path.expanduser("~/.local/bin")
    data_dir: str = os.path.expanduser("~/.local/share/adam")
    notebook_dir: str = os.path.expanduser("~/.local/adam_notebook")
    todo_file: str = os.path.expanduser("~/.local/share/adam/todo_list.json")
    playwright_browsers_path: str = os.path.expanduser("~/.local/ms-playwright")
    extra_disk_paths: list[str] = field(default_factory=list)
    plugins_dir: str = "data/plugins"
    max_tool_calls: int = 5
    tool_timeout: int = 30
    cycle_timeout: int = 120
    max_input_length: int = 8000
    temperature: float = 0.7

    def __post_init__(self):
        """[FIX] تحقق من صحة القيم الحرجة"""
        if self.context_window <= 0:
            raise ValueError(f"context_window يجب أن يكون موجباً، حصلت على {self.context_window}")
        if self.token_budget <= 0:
            raise ValueError(f"token_budget يجب أن يكون موجباً، حصلت على {self.token_budget}")
        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError(f"temperature يجب أن تكون بين 0.0 و 2.0، حصلت على {self.temperature}")
        if self.max_tool_calls < 0:
            raise ValueError(f"max_tool_calls لا يمكن أن يكون سالباً، حصلت على {self.max_tool_calls}")
        if self.max_conversation_history < 0:
            raise ValueError(f"max_conversation_history لا يمكن أن يكون سالباً، حصلت على {self.max_conversation_history}")
        for url_field in ("ollama_base", "qdrant_url", "lora_server_url"):
            url_val = getattr(self, url_field)
            if url_val and not url_val.startswith(("http://", "https://")):
                logger.warning(f"{url_field}='{url_val}' لا يبدو URL صالحاً")

    @classmethod
    def from_dict(cls, d: dict) -> "AdamConfig":
        known = {k for k in cls.__dataclass_fields__}
        kwargs = {k: v for k, v in d.items() if k in known}
        unknown = set(d.keys()) - known
        if unknown:
            logger.warning(f"AdamConfig: مفاتيح غير معروفة تم تجاهلها: {unknown}")
        return cls(**kwargs)

    def to_dict(self) -> dict:
        return {k: getattr(self, k) for k in self.__dataclass_fields__}
