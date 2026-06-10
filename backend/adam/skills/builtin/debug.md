---
{"name": "debug", "description": "Debug errors systematically", "version": "1.0.0", "author": "adam", "triggers": ["error", "bug", "غلط", "broken", "fail", "exception"]}
---

When helping debug an error:

1. Get the FULL error message and traceback
2. Identify: what line, what type of error, what values
3. Check the 5 most common causes for that error type
4. Reproduce if possible — isolate the minimal case
5. Fix with explanation of root cause
6. Verify: "هل الكود شغال دلوقتي؟"

For Python specifically:
- ImportError -> module not installed or circular import
- AttributeError -> typo in name or wrong object type
- TypeError -> wrong args or None where object expected
- ValueError -> bad input format or empty collection
- IndexError -> off-by-one or empty list
