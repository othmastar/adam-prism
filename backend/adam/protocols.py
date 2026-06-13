"""
Adam Prism — Protocol definitions for subsystem interfaces.
Typing-only: no runtime impact.
"""

from typing import Dict, List, Optional, Protocol, runtime_checkable


@runtime_checkable
class MemorySystem(Protocol):
    async def search(self, query: str, collection: str = "knowledge",
                     top_k: int = 5, score_threshold: float = 0.5) -> List[Dict]: ...
    async def store(self, collection: str, text: str, metadata: Dict,
                    point_id: Optional[str] = None) -> bool: ...
    async def retrieve(self, query: str, top_k: int = 5) -> List[Dict]: ...


@runtime_checkable
class EthicsGate(Protocol):
    # [M16] Fixed to match the actual implementation in ethics/gate.py
    # evaluate() takes (response, original_query) not (query, response)
    # correct() is actually _correct_response() — not a public method
    async def evaluate(self, response: str, original_query: str = "") -> Dict: ...


@runtime_checkable
class SecurityGuard(Protocol):
    async def check_input(self, text: str) -> Dict: ...
    async def check_output(self, text: str) -> Dict: ...
    async def check_tool_call(self, tool: str, params: Dict) -> Dict: ...


@runtime_checkable
class NotebookSystem(Protocol):
    def read_section(self, section: str) -> str: ...
    def write_section(self, section: str, content: str) -> None: ...


@runtime_checkable
class Eyes(Protocol):
    async def initialize(self) -> bool: ...
    async def is_healthy(self) -> bool: ...
    async def restart(self) -> bool: ...


@runtime_checkable
class ToolManager(Protocol):
    async def execute(self, tool: str, params: Dict) -> Dict: ...
    def get_action_log(self, limit: int = 50) -> List[Dict]: ...


@runtime_checkable
class PipelineChannels(Protocol):
    async def broadcast(self, message: str, source: str = "") -> None: ...
