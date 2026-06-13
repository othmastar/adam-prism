"""
Adam Prism - Meta Learner
=========================
Background extraction of reasoning patterns from conversation traces.
Always fire-and-forget: never awaited in the main pipeline path.
All patterns stored in English (semantic meaning, not literal).
No Ollama calls - uses lightweight heuristics only.
"""

import logging

from adam.core.trace_recorder import ConversationTrace

logger = logging.getLogger("adam_prism.meta_learner")

PATTERN_TYPES = {
    "tool_sequence": "Pattern of tool usage order for specific intent types",
    "tool_selection": "Which tool to use for which type of task",
    "tool_failure": "Which tools fail in which contexts",
    "planning_depth": "How many tools needed for complex tasks",
    "correction_signal": "User corrections that changed the approach",
    "reasoning_path": "Chain of reasoning steps for problem types",
}


def _extract_tool_sequence(trace: ConversationTrace) -> dict | None:
    if not trace.tool_calls:
        return None
    tool_names = [t["name"] for t in trace.tool_calls]
    return {
        "type": "tool_sequence",
        "pattern": " → ".join(tool_names),
        "tool_count": len(tool_names),
        "intent": trace.intent.get("intent_type", "general"),
        "mode": trace.mode,
        "outcome": trace.outcome,
        "success": trace.outcome == "success",
    }


def _extract_tool_selections(trace: ConversationTrace) -> list[dict]:
    patterns = []
    for tc in trace.tool_calls:
        if tc.get("success"):
            patterns.append({
                "type": "tool_selection",
                "pattern": (
                    f"When intent is '{trace.intent.get('intent_type', 'general')}' "
                    f"in mode '{trace.mode}', use {tc['name']}"
                ),
                "intent": trace.intent.get("intent_type"),
                "mode": trace.mode,
                "tool": tc["name"],
                "outcome": trace.outcome,
            })
        else:
            patterns.append({
                "type": "tool_failure",
                "pattern": (
                    f"{tc['name']} failed for '{trace.intent.get('intent_type')}' "
                    f"task: {tc.get('error', 'unknown error')}"
                ),
                "intent": trace.intent.get("intent_type"),
                "tool": tc["name"],
                "error": tc.get("error", "unknown"),
            })
    return patterns


def _extract_planning_depth(trace: ConversationTrace) -> dict | None:
    if trace.tool_call_count < 2:
        return None
    return {
        "type": "planning_depth",
        "pattern": (
            f"Multi-step task in mode '{trace.mode}': "
            f"{trace.tool_call_count} tools used in sequence"
        ),
        "tool_count": trace.tool_call_count,
        "intent": trace.intent.get("intent_type"),
        "mode": trace.mode,
        "outcome": trace.outcome,
    }


class MetaLearner:
    def __init__(self, memory):
        self.memory = memory

    async def process_trace(self, trace: ConversationTrace):
        try:
            patterns = []

            seq = _extract_tool_sequence(trace)
            if seq:
                patterns.append(seq)

            patterns.extend(_extract_tool_selections(trace))

            depth = _extract_planning_depth(trace)
            if depth:
                patterns.append(depth)

            for p in patterns:
                text = p.pop("pattern")
                metadata = {
                    "pattern_type": p["type"],
                    "trace": p,
                }
                await self.memory.store_pattern(text, p["type"], metadata)

            if patterns:
                logger.debug(f"Stored {len(patterns)} patterns from cycle {trace.cycle}")

        except Exception:
            logger.exception("Meta-learner background extraction failed:")
