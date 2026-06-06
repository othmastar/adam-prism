"""
Transform ALL conversations to the 95 teaching pattern:
  system → assistant(scenario) → user(analysis?) → assistant(mistakes) → user(solution?) → assistant(practical)

Preserves ALL existing content — just restructures and adds framing where needed.
"""

import json
import re
from pathlib import Path

SPLITS = Path("/mnt/Workspace/Adam_Prism_Complete_v2/data/training/splits")

def extract_scenario(assistant_text: str) -> str:
    """Extract a scenario from the assistant's content for the first turn."""
    lines = assistant_text.strip().split("\n")
    topic_lines = []
    for line in lines:
        clean = line.replace("**", "").strip()
        if clean and clean not in ("الاكتشاف:", "Discover:", "الشرح:", "Explain:",
                                    "التطبيق:", "Apply:", "الخطأ:", "Error:",
                                    "المصدر:", "Source:"):
            topic_lines.append(clean)
            if len(topic_lines) >= 3:
                break
    scenario = " ".join(topic_lines)[:300]
    if not scenario:
        scenario = assistant_text[:200]
    return scenario

def extract_mistakes(assistant_text: str) -> str:
    """Extract or build the 'common mistakes' analysis."""
    lines = assistant_text.strip().split("\n")
    discovered = []
    explained = []
    current_section = None
    for line in lines:
        clean = line.replace("**", "").strip()
        if clean in ("الاكتشاف:", "Discover:"):
            current_section = "discover"
            continue
        elif clean in ("الشرح:", "Explain:"):
            current_section = "explain"
            continue
        elif clean in ("الخطأ:", "Error:"):
            current_section = "error"
            continue
        elif clean in ("التطبيق:", "Apply:", "Practice:"):
            current_section = "practice"
            continue

        if current_section in ("discover", "explain", "error") and clean:
            discovered.append(clean)

    if discovered:
        result = "\n".join(discovered[:8])
    else:
        mid = len(assistant_text) // 2
        result = assistant_text[:mid].strip()[:600]

    return f"التحليل:\n{result}" if len(result) > 20 else assistant_text[:400]

def extract_practice(assistant_text: str) -> str:
    """Extract practical steps/solution."""
    lines = assistant_text.strip().split("\n")
    practice = []
    in_practice = False
    for line in lines:
        clean = line.replace("**", "").strip()
        if clean in ("التطبيق:", "Apply:", "Practice:"):
            in_practice = True
            continue
        if in_practice and clean:
            practice.append(line)

    if practice:
        result = "\n".join(practice)
    else:
        mid = len(assistant_text) // 2
        result = assistant_text[mid:].strip()

    return result[:1500] if len(result) > 50 else assistant_text[-500:]


def transform_to_95_pattern(rec: dict) -> dict:
    """Transform any conversation to the 95 teaching pattern."""
    messages = rec["messages"]
    system = messages[0]

    if len(messages) >= 6:
        return rec

    assistant_msgs = [m for m in messages if m["role"] == "assistant"]
    user_msgs = [m for m in messages if m["role"] == "user"]

    if not assistant_msgs:
        return rec

    combined_assistant = "\n\n".join(m["content"] for m in assistant_msgs)

    first_user = user_msgs[0]["content"] if user_msgs else "عاوز تحليل متعمق لهذه المسألة."

    scenario = extract_scenario(combined_assistant)
    mistakes = extract_mistakes(combined_assistant)
    practice = extract_practice(combined_assistant)

    is_eg = rec.get("dialect") == "eg"

    if is_eg:
        q_analysis = "إيه التحليل المنطقي للموضوع ده؟ إيه الأخطاء الشائعة اللي بنقع فيها؟"
        q_solution = "طيب إيه الخطوات العملية؟ عاوز حل تطبيقي."
    else:
        q_analysis = "ما هو التحليل المنطقي لهذه المسألة؟ وما الأخطاء الشائعة التي نقع فيها؟"
        q_solution = "حسنًا، ما هي الخطوات العملية؟ أريد حلاً تطبيقيًا."

    new_messages = [
        system,
        {"role": "assistant", "content": f"سيناريو: {scenario}"},
        {"role": "user", "content": q_analysis},
        {"role": "assistant", "content": mistakes},
        {"role": "user", "content": q_solution},
        {"role": "assistant", "content": practice},
    ]

    rec["messages"] = new_messages
    rec["metadata"] = rec.get("metadata", {})
    rec["metadata"]["is_multi_turn"] = True
    rec["metadata"]["transformed_to_95"] = True
    return rec


# Process all splits
total = 0
transformed = 0
for split in ["train", "val", "test"]:
    path = SPLITS / f"{split}.jsonl"
    records = [json.loads(line) for line in open(path) if line.strip()]

    out = []
    for rec in records:
        total += 1
        msgs = rec["messages"]
        if len(msgs) < 6:
            out.append(transform_to_95_pattern(rec))
            transformed += 1
        else:
            out.append(rec)

    with open(path, "w") as f:
        for rec in out:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"{split}: {len(records)} → {len(out)} ({len(out)-len(records)} transformed)")

print(f"\nTotal: {total}, Transformed to 95-pattern: {transformed}")
