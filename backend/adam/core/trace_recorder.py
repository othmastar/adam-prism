"""
Adam Prism - Trace Recorder
===========================
In-memory conversation trace recording.
No I/O, no blocking, O(1) append. Zero impact on main pipeline.
"""

import logging
from collections import deque
from datetime import datetime

logger = logging.getLogger("adam_prism.trace")


class ConversationTrace:
    __slots__ = (
        "cycle",
        "duration_ms",
        "intent",
        "mode",
        "outcome",
        "query",
        "response_length",
        "timestamp",
        "tool_call_count",
        "tool_calls"
    )

    def __init__(
        self,
        query: str,
        intent: dict,
        mode: str,
        tool_calls: list[dict],
        outcome: str,
        response_length: int,
        tool_call_count: int,
        cycle: int,
        duration_ms: int,
    ):
        self.query = query
        self.intent = intent
        self.mode = mode
        self.tool_calls = tool_calls
        self.outcome = outcome
        self.response_length = response_length
        self.tool_call_count = tool_call_count
        self.cycle = cycle
        self.duration_ms = duration_ms
        self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return {s: getattr(self, s) for s in self.__slots__}


class TraceRecorder:
    def __init__(self, max_traces: int = 200):
        self.traces: deque = deque(maxlen=max_traces)

    def record(self, trace: ConversationTrace):
        self.traces.append(trace)

    def get_recent(self, n: int = 10) -> list[dict]:
        return [t.to_dict() for t in list(self.traces)[-n:]]

    def get_traces_for_intent(self, intent_type: str, max_results: int = 3) -> list[dict]:
        matching = [t for t in self.traces if t.intent.get("intent_type") == intent_type]
        return [t.to_dict() for t in matching[-max_results:]]

    def get_patterns_for_query(self, query: str, intent_type: str, max_results: int = 3) -> list[str]:
        traces = self.get_traces_for_intent(intent_type, max_results)
        patterns = []
        for t in traces:
            if t["tool_call_count"] > 0:
                tool_names = [tc["name"] for tc in t["tool_calls"]]
                seq = " → ".join(tool_names)
                patterns.append(
                    f"[{t['mode']}] When handling '{intent_type}' queries, used: {seq} (outcome: {t['outcome']})"
                )
            if t["outcome"] == "failure":
                patterns.append(
                    f"[{t['mode']}] Failed attempt for '{intent_type}' - {t['tool_call_count']} tools tried"
                )
        return patterns[:max_results]

    def get_stats(self) -> dict:
        total = len(self.traces)
        with_tools = sum(1 for t in self.traces if t.tool_call_count > 0)
        successful = sum(1 for t in self.traces if t.outcome == "success")
        return {
            "total_traces": total,
            "with_tool_calls": with_tools,
            "successful": successful,
            "failed": total - successful
        }
