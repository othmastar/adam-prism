#!/usr/bin/env python3
"""
Rewrite conversations to v2 quality using local Ollama models.
الإصدار 2: معالجة ANSI codes + thinking text + prompt محسّن
"""

import json
import re
import subprocess
from pathlib import Path

SPLITS_DIR = Path("data/training/splits")
OUT_DIR = Path("data/training/rewrite_sample")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Regex to strip ANSI escape codes
ANSI_RE = re.compile(r'\x1b\[[\d;]*[a-zA-Z]')
# Regex to strip thinking blocks
THINKING_RE = re.compile(r'^(Thinking|Hmm|Let me|I need to|Okay|Alright|Here\'s|I will|First|I should).*?\n', re.IGNORECASE | re.MULTILINE)


def clean_output(text: str) -> str:
    """Clean model output: remove ANSI codes, thinking text, artifacts."""
    text = ANSI_RE.sub('', text)
    text = THINKING_RE.sub('', text)
    # Remove markdown code blocks
    text = re.sub(r'```[\w]*\n?', '', text)
    # Remove leading numbers/dashes/bullets
    text = re.sub(r'^[\s]*[\d\.\-\)\*>#]+[\s]*', '', text, flags=re.MULTILINE)
    # Remove bracket template artifacts like "[Short question/setup]" "[Detailed..."
    text = re.sub(r'\[(?:Short|Detailed|Very short|Natural|Deeper|Technical|Specific|General)\s+\w+[^\]]*\]', '', text, flags=re.IGNORECASE)
    # Remove English instruction artifacts
    text = re.sub(r'\b(?:provides|replies in|holds all|must hold|based on)\s+\w+.*', '', text, flags=re.IGNORECASE)
    # Remove leading/trailing whitespace per line
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    # Remove lines that look like meta-commentary or instructions
    skip_patterns = [
        r'^(Here\'s|This is|The rewritten|I notice|I see|I think|I\'ll|Let me|The key|Note:)',
        r'^(user|assistant)\s*(makes|replies|provides|gives|holds)',
        r'^\w+\s+builds on',
        r'^\[.*?\]$',
    ]
    lines = [l for l in lines if not any(re.match(sp, l, re.IGNORECASE) for sp in skip_patterns)]
    return '\n'.join(lines)


def is_real_arabic(text: str) -> bool:
    """Check if text is a real Arabic conversation message (not instruction/artifact)."""
    if not text or len(text) < 8:
        return False
    # Must start with Arabic or common Arabic punctuation
    if not re.match(r'^[\u0600-\u06FF\u0750-\u077F\uFE70-\uFEFF"«»\-]', text.strip()):
        return False
    # Must have substantial Arabic content (at least 30% Arabic chars)
    arabic_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
    if arabic_chars / max(len(text), 1) < 0.2:
        return False
    # Must not be instruction text
    instruction_words = ['must', 'goal', 'constraint', 'analyze', 'rewrite', 'the user', 'the assistant',
                         'constraint 1', 'constraint 2', '##', '**', 'based on']
    if any(iw in text.lower() for iw in instruction_words):
        return False
    return True


def parse_conversation(text: str) -> list[dict] | None:
    """Parse LLM output into structured conversation, removing instruction artifacts."""
    text = clean_output(text)

    # Parse all role-tagged lines
    raw_msgs = []
    lines = text.strip().split('\n')
    for line in lines:
        line = line.strip()
        if not line or len(line) < 3:
            continue
        m = re.match(
            r'^(?:\[?\d*\]?[\s\)\.\:-]*)?'
            r'(user|assistant|system|u:|a:|s:)'
            r'(?:[\s\)\.\:>-]+)?\s*(.+)',
            line, re.IGNORECASE
        )
        if m:
            role_raw = m.group(1).lower()
            content = m.group(2).strip()
            role_map = {'u:': 'user', 'a:': 'assistant', 's:': 'system'}
            role = role_map.get(role_raw, role_raw)
            content = re.sub(r'^["\']|["\']$', '', content)
            content = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', content)
            content = ' '.join(content.split())
            if content and len(content) > 3:
                raw_msgs.append({"role": role, "content": content})

    if len(raw_msgs) < 3:
        return None

    # Find first real Arabic user message
    start_idx = -1
    for i, m in enumerate(raw_msgs):
        if m['role'] == 'user' and is_real_arabic(m['content']):
            start_idx = i
            break

    if start_idx < 0:
        return None

    msgs = raw_msgs[start_idx:]

    # Keep only real Arabic messages, filter English artifacts
    clean = []
    for m in msgs:
        if m['role'] == 'system' and not is_real_arabic(m['content']):
            continue
        if not is_real_arabic(m['content']) and m['role'] != 'system':
            # Allow short Arabic responses from assistant
            if m['role'] == 'assistant' and len(m['content']) < 5:
                continue
            if m['role'] == 'user':
                continue  # Skip instruction-like user messages
        clean.append(m)

    if len(clean) < 3:
        return None

    # Ensure first is user
    if clean[0]['role'] != 'user':
        # Try to find first user
        for i, m in enumerate(clean):
            if m['role'] == 'user':
                clean = clean[i:]
                break
        else:
            return None

    if len(clean) < 3:
        return None

    # Shorten long assistant responses
    for m in clean:
        if m['role'] == 'assistant' and len(m['content']) > 500:
            m['content'] = m['content'][:500]

    return clean


def format_original(msgs: list) -> str:
    """Format conversation for LLM prompt."""
    parts = []
    for m in msgs:
        if m['role'] == 'system':
            continue
        parts.append(f"{m['role']}: {m['content']}")
    return '\n\n'.join(parts)


def build_prompt(original_msgs: list) -> str:
    """Build optimized rewrite prompt."""
    original_text = format_original(original_msgs)

    return f"""أعد كتابة المحادثة التالية لتصبح حواراً تقنياً طبيعياً بالعربية.

القواعد الصارمة:
1. المستخدم يشرح المشكلة أو السياق بتفصيل (يحمل كل المعلومات)
2. المساعد يرد بجمل قصيرة فقط (10-30 كلمة، أقل من 150 حرف)
3. الحوار يتعمق: كل دور يبني على اللي قبله
4. كل المعلومات التقنية تفضل محفوظة لكن في كلام المستخدم مش المساعد
5. استخدم لهجة عربية طبيعية (ليست رسمية جداً)

النمط المطلوب بالضبط:
user: [سؤال أو موقف قصير]
user: [شرح تفصيلي للمشكلة مع كل المعلومات التقنية]
assistant: [رد طبيعي قصير جداً - 10-20 كلمة]
user: [سؤال متابعة طبيعي يبني على الإجابة]
assistant: [رد طبيعي قصير]
user: [استفسار أعمق]
assistant: [رد طبيعي قصير]

المحادثة الأصلية:
---
{original_text}
---

أعد كتابتها الآن بالضبط على النمط المطلوب (بدون مقدمة أو شرح):"""


def call_ollama(prompt: str, model: str = "gemma4:e4b", timeout: int = 120) -> str:
    """Call Ollama model with clean output."""
    try:
        result = subprocess.run(
            ["ollama", "run", model],
            input=prompt.encode('utf-8'),
            capture_output=True,
            timeout=timeout,
            cwd="/tmp"
        )
        output = result.stdout.decode('utf-8', errors='replace')
        error = result.stderr.decode('utf-8', errors='replace')
        if error and "error" in error.lower():
            return f"ERROR: {error}"
        return output.strip()
    except subprocess.TimeoutExpired:
        return "ERROR: Timeout"
    except Exception as e:
        return f"ERROR: {str(e)}"


def show_conv(msgs: list, label: str):
    """Pretty print conversation."""
    print(f"\n  --- {label} ({len(msgs)} msgs) ---")
    for i, m in enumerate(msgs):
        c = m['content'][:100] + '...' if len(m['content']) > 100 else m['content']
        print(f"  [{i}] {m['role'][0].upper()}: {c}")


def analyze_quality(msgs: list) -> dict:
    """Analyze rewritten conversation quality."""
    if not msgs:
        return {"error": "empty"}

    user_msgs = [m for m in msgs if m['role'] == 'user']
    asst_msgs = [m for m in msgs if m['role'] == 'assistant']

    avg_user_len = sum(len(m['content']) for m in user_msgs) / len(user_msgs) if user_msgs else 0
    avg_asst_len = sum(len(m['content']) for m in asst_msgs) / len(asst_msgs) if asst_msgs else 0
    short_asst = sum(1 for m in asst_msgs if len(m['content']) < 150)
    generic_user = sum(1 for m in user_msgs if any(
        gp in m['content'] for gp in
        ['ما هو التحليل', 'ما هي الخطوات', 'أريد حلاً', 'الخطوات العملية',
         'أحسنت', 'ممتاز', 'تمام']
    ))

    return {
        "turns": len(msgs),
        "user_count": len(user_msgs),
        "asst_count": len(asst_msgs),
        "avg_user_len": round(avg_user_len),
        "avg_asst_len": round(avg_asst_len),
        "short_asst_pct": round(100 * short_asst / len(asst_msgs)) if asst_msgs else 0,
        "generic_user": generic_user,
        "user_carries_context": avg_user_len > avg_asst_len,
        "v2_match_score": round(
            (avg_user_len > avg_asst_len) * 40 +  # 40% weight
            (short_asst / max(len(asst_msgs), 1) > 0.5) * 30 +  # 30% weight
            (len(msgs) >= 6) * 30  # 30% weight
        )
    }


def main():
    # Load
    path = SPLITS_DIR / "train.jsonl"
    with open(path) as f:
        all_convos = [json.loads(line) for line in f]

    MODEL = "gemma4:e4b"  # Try Gemma 4 E4B locally
    print(f"Model: {MODEL}")
    print(f"Available: {len(all_convos)} conversations")

    # Test on 5 samples
    samples = all_convos[:5]
    results = []

    for idx, conv in enumerate(samples):
        original = conv['messages']
        print(f"\n{'='*60}")
        print(f"Sample {idx+1}/5")
        show_conv(original, "BEFORE")
        orig_quality = analyze_quality(original)
        print(f"  Quality: {json.dumps(orig_quality, ensure_ascii=False)}")

        prompt = build_prompt(original)
        print(f"  → Rewriting (up to 2 min)...")
        response = call_ollama(prompt, model=MODEL, timeout=120)

        if response.startswith("ERROR:"):
            print(f"  ✗ {response}")
            results.append({"original": original, "rewritten": None, "error": response, "quality": orig_quality})
            continue

        rewritten = parse_conversation(response)

        if rewritten:
            show_conv(rewritten, "AFTER")
            new_quality = analyze_quality(rewritten)
            print(f"  Quality: {json.dumps(new_quality, ensure_ascii=False)}")
            results.append({
                "original": original,
                "rewritten": rewritten,
                "error": None,
                "quality_before": orig_quality,
                "quality_after": new_quality
            })
        else:
            print(f"  ✗ Parse failed. Cleaned sample:")
            print(f"  {clean_output(response)[:600]}")
            results.append({
                "original": original,
                "rewritten": None,
                "error": "parse_failed",
                "quality": orig_quality,
                "raw_cleaned": clean_output(response)[:600]
            })

    # Save
    out_path = OUT_DIR / "rewrite_v2_results.json"
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump({"model": MODEL, "samples": results}, f, ensure_ascii=False, indent=2)

    # Summary
    success = sum(1 for r in results if r['rewritten'] is not None)
    failed = sum(1 for r in results if r['rewritten'] is None)
    improved = sum(1 for r in results if r.get('rewritten') and r.get('quality_after', {}).get('v2_match_score', 0) > r.get('quality_before', {}).get('v2_match_score', 0))

    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"  Success: {success}/5")
    print(f"  Failed: {failed}/5")
    print(f"  Quality improved: {improved}/{success}")
    if success > 0:
        avg_before = sum(r['quality_before']['v2_match_score'] for r in results if r.get('quality_before'))
        avg_after = sum(r['quality_after']['v2_match_score'] for r in results if r.get('quality_after'))
        print(f"  Avg v2_match_score: {avg_before/5:.0f} → {avg_after/success:.0f}")


if __name__ == '__main__':
    main()
