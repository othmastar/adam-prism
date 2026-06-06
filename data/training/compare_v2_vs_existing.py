#!/usr/bin/env python3
"""
Quality comparison: v2 (standard) vs existing data
المقارنة من 7 أبعاد مع أمثلة حية
"""

import json
import re
import math
from pathlib import Path

V2_DIR = Path("data/training/raw_training_v2")
SPLITS_DIR = Path("data/training/splits")


def load_v2():
    """Load raw v2 as list of message lists."""
    convos = []
    for split in ['train', 'val', 'test']:
        path = V2_DIR / f"{split}.jsonl"
        with open(path) as f:
            for line in f:
                raw = json.loads(line)
                convos.append(raw)
    return convos


def load_existing():
    """Load existing splits."""
    convos = []
    for split in ['train', 'val', 'test']:
        path = SPLITS_DIR / f"{split}.jsonl"
        with open(path) as f:
            for line in f:
                convos.append(json.loads(line))
    return convos


def analyze_conv(msgs, label=""):
    """Analyze a single conversation."""
    user_msgs = [m for m in msgs if m['role'] == 'user']
    asst_msgs = [m for m in msgs if m['role'] == 'assistant']
    sys_msgs = [m for m in msgs if m['role'] == 'system']

    user_lens = [len(m['content']) for m in user_msgs]
    asst_lens = [len(m['content']) for m in asst_msgs]

    return {
        'turns': len(msgs),
        'user_count': len(user_msgs),
        'asst_count': len(asst_msgs),
        'sys_count': len(sys_msgs),
        'avg_user_len': sum(user_lens) / len(user_lens) if user_lens else 0,
        'avg_asst_len': sum(asst_lens) / len(asst_lens) if asst_lens else 0,
        'max_user_len': max(user_lens) if user_lens else 0,
        'max_asst_len': max(asst_lens) if asst_lens else 0,
        'total_chars': sum(len(m['content']) for m in msgs),
        'user_lens': user_lens,
        'asst_lens': asst_lens,
    }


def detect_generic(text):
    """Check if user message is a generic template."""
    patterns = [
        'ما هو التحليل المنطقي', 'ما هي الخطوات العملية',
        'أريد حلاً تطبيقياً', 'الخطوات العملية', 'أحسنت', 'ممتاز',
        'تمام', 'حسنًا', 'هذا رائع', 'فهمت. هل يمكن توضيح أكثر',
        'ماذا عن التفاصيل الأخرى'
    ]
    for p in patterns:
        if p in text:
            return True
    return False


def count_unique_tokens(texts):
    """Approximate lexical diversity."""
    all_words = set()
    for t in texts:
        for w in t.split():
            all_words.add(w)
    return len(all_words)


def main():
    v2_raw = load_v2()
    existing_raw = load_existing()

    # Analyze v2
    v2_stats = [analyze_conv(c) for c in v2_raw]
    # Analyze existing (use .messages key)
    existing_stats = [analyze_conv(c['messages']) for c in existing_raw]

    # ─── DIMENSION 1: Turn Count ───
    print("=" * 65)
    print("المقارنة: v2 (المعيار) vs البيانات الحالية")
    print("=" * 65)

    print("\n1️⃣  عدد الأدوار (Turns)")
    print("-" * 40)
    for name, stats in [("v2", v2_stats), ("الحالية", existing_stats)]:
        turns = [s['turns'] for s in stats]
        avg = sum(turns) / len(turns)
        print(f"  {name}: avg={avg:.1f}, min={min(turns)}, max={max(turns)}, "
              f"med={sorted(turns)[len(turns)//2]}")
        # Distribution
        dist = {}
        for t in turns:
            dist[t] = dist.get(t, 0) + 1
        print(f"  التوزيع: {dict(sorted(dist.items()))}")

    # ─── DIMENSION 2: Message Length Balance ───
    print("\n2️⃣  توازن طول الرسائل (User vs Assistant)")
    print("-" * 40)
    for name, stats in [("v2", v2_stats), ("الحالية", existing_stats)]:
        avg_u = sum(s['avg_user_len'] for s in stats) / len(stats)
        avg_a = sum(s['avg_asst_len'] for s in stats) / len(stats)
        ratio = avg_u / avg_a if avg_a > 0 else 0
        total = sum(s['total_chars'] for s in stats) / len(stats)
        print(f"  {name}: user={avg_u:.0f}ch, asst={avg_a:.0f}ch, "
              f"ratio(u/a)={ratio:.2f}, avg_total={total:.0f}ch")

    # ─── DIMENSION 3: Generic Template Rate ───
    print("\n3️⃣  نسبة الجمل العامة (Generic Templates)")
    print("-" * 40)
    for name, lst, raw in [("v2", v2_stats, v2_raw), ("الحالية", existing_stats, existing_raw)]:
        # Count generic user messages
        total_user = 0
        generic_user = 0
        for c in raw:
            msgs = c if isinstance(c, list) else c['messages']
            for m in msgs:
                if m['role'] == 'user':
                    total_user += 1
                    if detect_generic(m['content']):
                        generic_user += 1
        pct = 100 * generic_user / total_user if total_user else 0
        print(f"  {name}: {generic_user}/{total_user} = {pct:.1f}% generic")

    # ─── DIMENSION 4: Lexical Diversity ───
    print("\n4️⃣  التنوع اللغوي (Lexical Diversity)")
    print("-" * 40)
    for name, raw in [("v2", v2_raw), ("الحالية", existing_raw)]:
        all_user = []
        all_asst = []
        for c in raw:
            msgs = c if isinstance(c, list) else c['messages']
            for m in msgs:
                if m['role'] == 'user':
                    all_user.append(m['content'])
                elif m['role'] == 'assistant':
                    all_asst.append(m['content'])
        u_uniq = count_unique_tokens(all_user)
        a_uniq = count_unique_tokens(all_asst)
        u_total = sum(len(t.split()) for t in all_user)
        a_total = sum(len(t.split()) for t in all_asst)
        print(f"  {name}: user_unique={u_uniq}, asst_unique={a_uniq}")
        print(f"  {name}: user_total_words={u_total}, asst_total_words={a_total}")

    # ─── DIMENSION 5: Multi-turn Depth ───
    print("\n5️⃣  عمق الحوار (Multi-turn Depth)")
    print("-" * 40)
    for name, stats in [("v2", v2_stats), ("الحالية", existing_stats)]:
        deep = sum(1 for s in stats if s['turns'] >= 8)
        medium = sum(1 for s in stats if 5 <= s['turns'] < 8)
        short = sum(1 for s in stats if s['turns'] < 5)
        print(f"  {name}: deep(8+)={deep}, medium(5-7)={medium}, short(<5)={short}")

    # ─── DIMENSION 6: Sample Conversations ───
    print("\n6️⃣  أمثلة حية (مقارنة side-by-side)")
    print("-" * 40)

    # v2 examples
    print("\n  --- v2 example (18 turns) ---")
    for i, m in enumerate(v2_raw[1]):
        c = m['content']
        tag = m['role'][0].upper()
        print(f"  [{i}] {tag}: {c[:100]}")

    print("\n  --- Existing example (5 turns) ---")
    for i, m in enumerate(existing_raw[0]['messages']):
        c = m['content']
        tag = m['role'][0].upper()
        print(f"  [{i}] {tag}: {c[:100]}")

    # ─── DIMENSION 7: Asst/User Role Reversal in v2 ───
    print("\n7️⃣  نمط توزيع المعرفة (v2 فريد)")
    print("-" * 40)
    for name, raw in [("v2", v2_raw), ("الحالية", existing_raw)]:
        long_user = 0
        short_asst = 0
        total_pairs = 0
        for c in raw:
            msgs = c if isinstance(c, list) else c['messages']
            for i in range(1, len(msgs)):
                if msgs[i-1]['role'] == 'user' and msgs[i]['role'] == 'assistant':
                    total_pairs += 1
                    if len(msgs[i-1]['content']) > len(msgs[i]['content']):
                        long_user += 1
                    if len(msgs[i]['content']) < 200:
                        short_asst += 1
        print(f"  {name}:")
        print(f"    pairs where user_msg > asst_msg: {long_user}/{total_pairs} ({100*long_user/total_pairs:.0f}%)")
        print(f"    short asst responses (<200ch): {short_asst}/{total_pairs} ({100*short_asst/total_pairs:.0f}%)")

    # ─── SUMMARY ───
    print("\n" + "=" * 65)
    print("الخلاصة: الفجوة بين v2 والبيانات الحالية")
    print("=" * 65)
    print("""
    v2 تتفوق في:
    • حوار طبيعي متعدد الجولات (avg 8.3 vs 5.2)
    • المستخدم يحمل السياق (user أطول من asst)
    • ردود الموديل قصيرة وطبيعية
    • لا جمل عامة (0% generic templates)
    
    البيانات الحالية تحتاج:
    • تقليل الجمل العامة (3102 جملة عامة)
    • تحويل المقالات الطويلة لحوارات طبيعية
    • جعل المستخدم يحمل السياق بدل الموديل
    """)


if __name__ == '__main__':
    main()
