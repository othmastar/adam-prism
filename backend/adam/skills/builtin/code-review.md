---
{"name": "code-review", "description": "Review code for bugs, security issues, and style", "version": "1.0.0", "author": "adam", "triggers": ["review", "code review"]}
---

When asked to review code:

1. Read the file(s) in question
2. Check for:
   - Security vulnerabilities (injection, XSS, hardcoded secrets)
   - Logic bugs (off-by-one, race conditions, null references)
   - Performance issues (N+1 queries, memory leaks, unnecessary copies)
   - Style problems (inconsistent naming, dead code, overly complex functions)
3. Prioritize: security > correctness > performance > style
4. For each issue: explain WHY it's a problem and HOW to fix it
5. If no issues found, say "Looks clean" with confidence
