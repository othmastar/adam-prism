#!/usr/bin/env python3
"""
Build training dataset from extracted conversations.
Output: JSONL format suitable for QLoRA/transformers training.
"""
import json
import re
from pathlib import Path

DATA_DIR = Path("data/training")

def clean_text(text):
    """Remove excessive whitespace, normalize."""
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_pairs(messages):
    """Convert message list to user/assistant pairs."""
    pairs = []
    current_user = None

    for m in messages:
        role = m.get('role', 'unknown')
        text = clean_text(m.get('response', m.get('text', '')))

        if not text or len(text) < 5:
            continue

        if role == 'user':
            current_user = text
        elif role == 'assistant' and current_user:
            # Also try to include thinking
            thinking = clean_text(m.get('thinking', ''))
            response = text

            pairs.append({
                'user': current_user,
                'assistant': response,
                'thinking': thinking,
                'user_length': len(current_user),
                'assistant_length': len(response)
            })
            current_user = None

    return pairs

def process_deepseek():
    """Process DeepSeek conversations."""
    # Try 348 version first, fall back to old
    path = DATA_DIR / "deepseek_all_348.json"
    if not path.exists():
        path = DATA_DIR / "deepseek_all.json"
    if not path.exists():
        print("[!] No DeepSeek data found")
        return [], 0

    data = json.loads(path.read_text())
    print(f"  (using {path.name})")
    all_pairs = []
    stats = {'with_thinking': 0, 'total_pairs': 0, 'total_convs': 0}

    for conv in data:
        messages = conv.get('messages', [])
        pairs = extract_pairs(messages)

        for p in pairs:
            if p['thinking']:
                stats['with_thinking'] += 1
            all_pairs.append({
                'source': 'deepseek',
                'title': conv.get('title', ''),
                'conversation_index': stats['total_convs'],
                **p
            })

        stats['total_convs'] += 1
        stats['total_pairs'] += len(pairs)

    print(f"  Conversations: {stats['total_convs']}")
    print(f"  User/Assistant pairs: {stats['total_pairs']}")
    print(f"  With thinking traces: {stats['with_thinking']}")

    return all_pairs, stats['total_pairs']

def process_gemini():
    """Process Gemini conversations — try OTHMASTAR first."""
    path = DATA_DIR / "gemini_othmastar.json"
    if not path.exists():
        path = DATA_DIR / "gemini_all.json"
    if not path.exists():
        print("[!] No Gemini data found")
        return [], 0

    data = json.loads(path.read_text())
    print(f"  (using {path.name})")
    all_pairs = []
    stats = {'total_pairs': 0, 'total_convs': 0}

    for conv in data:
        messages = conv.get('messages', [])
        pairs = extract_pairs(messages)

        for p in pairs:
            all_pairs.append({
                'source': 'gemini',
                'title': conv.get('title', ''),
                'conversation_index': stats['total_convs'],
                **p
            })

        stats['total_convs'] += 1
        stats['total_pairs'] += len(pairs)

    print(f"  Conversations: {stats['total_convs']}")
    print(f"  User/Assistant pairs: {stats['total_pairs']}")

    return all_pairs, stats['total_pairs']

def build_chat_format(pair):
    """Format as chat template for gemma."""
    user_msg = clean_text(pair['user'])
    asst_msg = clean_text(pair['assistant'])

    return {
        "messages": [
            {"role": "user", "content": user_msg},
            {"role": "assistant", "content": asst_msg}
        ]
    }

def main():
    print("Building training dataset...\n")

    print("1. Processing DeepSeek...")
    ds_pairs, ds_count = process_deepseek()

    print("\n2. Processing Gemini...")
    gm_pairs, gm_count = process_gemini()

    # Combine
    all_pairs = ds_pairs + gm_pairs
    total_pairs = len(all_pairs)

    print(f"\n{'='*50}")
    print(f"Total pairs: {total_pairs}")
    print(f"DeepSeek: {ds_count}")
    print(f"Gemini: {gm_count}")

    # Filter: keep pairs with meaningful Arabic text
    arabic_pattern = re.compile(r'[\u0600-\u06FF]')
    arabic_pairs = [p for p in all_pairs if arabic_pattern.search(p['user'])]
    print(f"\nArabic user messages: {len(arabic_pairs)}/{total_pairs}")

    # Save chat format (JSONL for transformers)
    chat_format = [build_chat_format(p) for p in all_pairs]
    chat_path = DATA_DIR / "training_chat.jsonl"
    with open(chat_path, 'w', encoding='utf-8') as f:
        for item in chat_format:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    print(f"\nChat format saved: {chat_path}")
    print(f"  Lines: {len(chat_format)}")

    # Save plain pairs for inspection
    pairs_path = DATA_DIR / "training_pairs.json"
    pairs_path.write_text(
        json.dumps(all_pairs, ensure_ascii=False, indent=2)
    )
    print(f"Pairs saved: {pairs_path}")

    # Print some examples
    print(f"\n{'='*50}")
    print("Sample pairs:")
    for i, p in enumerate(all_pairs[:5]):
        print(f"\n--- Pair {i+1} ({p['source']}) ---")
        print(f"USER ({p['user_length']}c): {p['user'][:150]}")
        print(f"ASSISTANT ({p['assistant_length']}c): {p['assistant'][:200]}")

    total_chars_user = sum(len(p['user']) for p in all_pairs)
    total_chars_asst = sum(len(p['assistant']) for p in all_pairs)
    print(f"\n{'='*50}")
    print(f"Total user chars: {total_chars_user:,}")
    print(f"Total assistant chars: {total_chars_asst:,}")
    print(f"Grand total: {total_chars_user + total_chars_asst:,}")

if __name__ == "__main__":
    main()
