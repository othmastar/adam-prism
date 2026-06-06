#!/bin/bash
# OthMastar v3 — filters thinking block, returns clean reply

[ $# -eq 0 ] && echo "Usage: $0 <prompt>" && exit 1

output=$(ollama run othmastar-v3 "$*" 2>/dev/null)

if echo "$output" | grep -q "done thinking"; then
    echo "$output" | sed '1,/\.\.\.done thinking\./d'
else
    echo "$output" | grep -v "^Thinking"
fi