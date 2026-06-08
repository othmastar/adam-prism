---
{"name": "write-test", "description": "Write tests for code", "version": "1.0.0", "author": "adam", "triggers": ["test", "unit test", "pytest"]}
---

When asked to write tests:

1. Read the source code to understand inputs, outputs, edge cases
2. Use pytest with async support
3. Cover:
   - Happy path (normal inputs)
   - Edge cases (empty, None, boundary values)
   - Error cases (invalid input, exceptions)
4. Name tests: `test_<function>_<scenario>`
5. Mock external dependencies (network, filesystem, DB)
6. Run the tests to verify they pass
