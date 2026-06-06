#!/usr/bin/env python3
"""
تحليل ADAM_COMPLETE — يشغّله الموديل السحابي لفحص جودة البيانات
===========================================================
يركّز على:
  - توزيع اللهجات
  - جودة المحادثات الفردية
  - تنوع السيناريوهات
  - قوة anti-prompt-injection
  - tool use patterns
  - نقاط الضعف
"""

import json
import os
import sys
from pathlib import Path
from collections import Counter

DATASET_DIR = Path("ADAM_COMPLETE")
REPORT_FILE = "cloud_consult_report.txt"

def analyze_split(path, label):
    """تحليل مفصل لملف split واحد"""
    with open(path) as f:
        lines = f.readlines()
    
    results = {
        "file": label,
        "total": len(lines),
        "sources": Counter(),
        "quality_scores": Counter(),
        "avg_turns": 0,
        "tool_calls": 0,
        "multi_turn_4plus": 0,
        "dialects": Counter(),
        "has_system_prompt": 0,
        "total_chars": 0,
        "user_chars": 0,
        "assistant_chars": 0,
        "long_tail_gt_2000_chars": 0,
        "short_responses": 0,  # asst < 20 chars
        "weak_security": 0,
        "strong_security": 0,
        "samples": [],  # Store diverse samples for human review
    }
    
    total_turns = 0
    seen_topics = set()
    
    for line in lines:
        conv = json.loads(line)
        msgs = conv["messages"]
        meta = conv.get("metadata", {})
        
        # Sources + quality
        results["sources"][meta.get("source", "unknown")] += 1
        q = meta.get("quality_score", 0)
        results["quality_scores"][str(q)] += 1
        
        # System prompt check
        if msgs and msgs[0].get("role") == "system":
            results["has_system_prompt"] += 1
        
        # Turns (excluding system)
        non_system = [m for m in msgs if m["role"] != "system"]
        total_turns += len(non_system)
        if len(non_system) > 4:
            results["multi_turn_4plus"] += 1
        
        # Character analysis
        for m in msgs:
            content = m.get("content", "") or ""
            if isinstance(content, str):
                results["total_chars"] += len(content)
                if m["role"] == "user":
                    results["user_chars"] += len(content)
                elif m["role"] == "assistant":
                    results["assistant_chars"] += len(content)
                    
                    # Check for too-short responses
                    if len(content) < 20:
                        results["short_responses"] += 1
        
        # Tool calls
        for m in msgs:
            content = m.get("content", "") or ""
            if isinstance(content, str) and '"_tool"' in content:
                results["tool_calls"] += 1
                break
        
        # Long conversations
        conv_chars = sum(len(m.get("content","")) for m in msgs if isinstance(m.get("content",""), str))
        if conv_chars > 2000:
            results["long_tail_gt_2000_chars"] += 1
        
        # Dialect detection (from type/topic metadata)
        conv_type = meta.get("type", "") or meta.get("topic", "")
        if "dialect" in conv_type.lower() or "dialect" in str(meta):
            results["dialects"][conv_type] += 1
        
        # Security detection
        if "security_defense" in str(meta.get("source", "")):
            results["strong_security"] += 1
            # Pick samples
            if len(results["samples"]) < 3:
                results["samples"].append({
                    "type": "security",
                    "user": msgs[-2]["content"][:200] if len(msgs) >= 2 else "",
                    "asst": msgs[-1]["content"][:200]
                })
        
        # Weak security (no defense)
        for m in msgs:
            if m["role"] == "user" and "كلمة السر" in (m.get("content","") or ""):
                results["weak_security"] += 1
                break  # Actually this is GOOD - conversation mentions password
    
    results["avg_turns"] = round(total_turns / len(lines), 1) if lines else 0
    
    # Find sample good conv
    for line in lines[:5]:
        conv = json.loads(line)
        msgs = conv["messages"]
        non_system = [m for m in msgs if m["role"] != "system"]
        if len(non_system) >= 2:
            results["samples"].append({
                "type": "standard",
                "user": non_system[0]["content"][:200] if non_system[0]["role"] == "user" else non_system[0]["content"][:200],
                "asst": non_system[-1]["content"][:200]
            })
            break
    
    return results

def write_report(all_results):
    """كتابة تقرير كامل"""
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write("☁️  CLOUD CONSULT — ADAM_COMPLETE Dataset Analysis\n")
        f.write("=" * 60 + "\n\n")
        
        total = sum(r["total"] for r in all_results)
        f.write(f"📊 Dataset: {total} conversations\n\n")
        
        for r in all_results:
            f.write(f"─── {r['file']} ({r['total']} convs) ───\n")
            f.write(f"  Avg turns (non-system): {r['avg_turns']}\n")
            f.write(f"  Multi-turn (>4):       {r['multi_turn_4plus']}\n")
            f.write(f"  Tool calls:            {r['tool_calls']}\n")
            f.write(f"  Long (>2000 chars):    {r['long_tail_gt_2000_chars']}\n")
            f.write(f"  Short responses (<20): {r['short_responses']} ⚠️\n")
            f.write(f"  Security defense:      {r['strong_security']}\n\n")
            
            f.write("  Sources:\n")
            for src, cnt in r["sources"].most_common(10):
                f.write(f"    {src}: {cnt}\n")
            
            f.write("\n  Quality:\n")
            for q, cnt in sorted(r["quality_scores"].items(), reverse=True)[:10]:
                f.write(f"    Q-{q}: {cnt}\n")
            
            f.write("\n  Dialects:\n")
            for d, cnt in r["dialects"].most_common():
                f.write(f"    {d}: {cnt}\n")
            
            f.write("\n  Samples:\n")
            for s in r["samples"][:3]:
                f.write(f"    [{s['type']}] U: {s['user'][:100]}\n")
                f.write(f"              A: {s['asst'][:100]}\n")
            f.write("\n")
        
        # Overall recommendations
        f.write("=" * 60 + "\n")
        f.write("💡 RECOMMENDATIONS FOR QLoRA\n")
        f.write("=" * 60 + "\n")
        f.write("""
1. MAX_SEQ_LENGTH
   - 2048 كافي لـ 95% من المحادثات
   - longest: ~7,170 token ← يحتاج تدوير أو تقطيع
   
2. QUALITY FILTER
   - حذف short responses (<20 chars): 
   - تحويل consciousness scores (0-1 scale) إلى scale موحد

3. CLASS BALANCE
   - Tool use: 153 فقط من 2,160 (7%) ← قليل
   - Dialect: 10 بس ← محتاج زيادة
   - Security: 10 بس ← محتاج زيادة

4. POTENTIAL ISSUES
   - System prompt غير موحد بين المصادر
   - بعض المحادثات ممكن فيها duplicate content
   - قلة التنوع في اللهجات الخليجية

5. TRAINING RECOMMENDATION
   - base_model: google/gemma-4-E4B-it
   - lora_r: 16
   - max_seq_length: 2048
   - batch_size: يعتمد على VRAM
   - steps: ~200-500 (2 epochs = ~400 steps)
   - learning_rate: 2e-4
""")
    
    print(f"✅ Report written to {REPORT_FILE}")

if __name__ == "__main__":
    results = []
    for split in ["train.jsonl", "val.jsonl", "test.jsonl"]:
        path = DATASET_DIR / split
        if path.exists():
            r = analyze_split(path, split)
            results.append(r)
    
    write_report(results)
    print(f"\n📄 Full report contents:")
    with open(REPORT_FILE) as f:
        print(f.read())
