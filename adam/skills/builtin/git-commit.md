---
{"name": "git-commit", "description": "Create meaningful git commit messages", "version": "1.0.0", "author": "adam", "triggers": ["git commit", "commit message"]}
---

When asked to create a git commit message:

1. Run `git diff --staged` to see staged changes
2. Analyze what files changed and why
3. Suggest 3 commit messages following conventional commits:
   - `feat:` for new features
   - `fix:` for bug fixes
   - `refactor:` for code changes
   - `docs:` for documentation
   - `test:` for tests
4. Let the user pick one, or commit with `git commit -m "..."`
