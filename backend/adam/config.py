"""
Adam Prism — Pydantic Configuration
=====================================
Backward-compatible config: engine accepts both dict and AdamConfig.
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional


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
    extra_disk_paths: List[str] = field(default_factory=list)
    plugins_dir: str = "data/plugins"
    max_tool_calls: int = 5
    tool_timeout: int = 30
    cycle_timeout: int = 120
    max_input_length: int = 8000
    temperature: float = 0.7

    @classmethod
    def from_dict(cls, d: Dict) -> "AdamConfig":
        known = {k for k in cls.__dataclass_fields__}
        kwargs = {k: v for k, v in d.items() if k in known}
        return cls(**kwargs)

    def to_dict(self) -> Dict:
        return {k: getattr(self, k) for k in self.__dataclass_fields__}
