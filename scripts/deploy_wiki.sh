#!/usr/bin/env bash
set -euo pipefail

# ─── 1. تأكد إن الـ wiki repo موجود ──────────────────────────────────────
WIKI_REPO="git@github.com:othmastar/adam-prism.wiki.git"
WIKI_DIR="/tmp/adam-prism.wiki.$$"

echo "🔍 Checking wiki repo..."
if ! git ls-remote "$WIKI_REPO" &>/dev/null; then
  echo "⚠️  Wiki repo doesn't exist yet."
  echo "   → Go to https://github.com/othmastar/adam-prism/wiki"
  echo "   → Click 'Create the first page'"
  echo "   → Then run this script again."
  exit 1
fi

# ─── 2. Clone wiki ─────────────────────────────────────────────────────────
echo "📦 Cloning wiki..."
rm -rf "$WIKI_DIR"
git clone "$WIKI_REPO" "$WIKI_DIR"

# ─── 3. Copy wiki pages ────────────────────────────────────────────────────
echo "📝 Copying wiki pages..."
SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cp "$SCRIPT_DIR/wiki/"*.md "$WIKI_DIR/"

# ─── 4. Commit and push ────────────────────────────────────────────────────
cd "$WIKI_DIR"
git add -A
if git diff --cached --quiet; then
  echo "✅ No changes — wiki is up to date."
else
  git commit -m "Update wiki — $(date +%Y-%m-%d)"
  git push origin master
  echo "✅ Wiki deployed!"
fi

# ─── 5. Cleanup ────────────────────────────────────────────────────────────
rm -rf "$WIKI_DIR"
