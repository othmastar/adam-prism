# Skill Marketplace Concept

## What is a Skill?

A **skill** is a reusable knowledge package that teaches Adam how to handle a specific task. Skills combine:
- **Instructions** — How to approach the task (Markdown)
- **Triggers** — Keywords that automatically activate the skill
- **Metadata** — Name, version, author, description

Skills are **not** plugins. Plugins hook into the engine lifecycle. Skills provide task-specific knowledge.

```python
# Conceptual difference
Plugin → "Run this code before every response"  (lifecycle hook)
Skill  → "When user asks about X, follow these steps"  (knowledge package)
```

## Current State

- Skills are stored as Markdown files with JSON frontmatter
- Built-in skills live in `adam/skills/builtin/`
- User skills can be placed in `~/.adam/skills/`
- SkillManager handles discovery, loading, and trigger matching
- 5 built-in skills: git-commit, code-review, explain-code, debug, write-test

## Marketplace Vision

### Source

A public GitHub repository: `github.com/adam-prism/skills`

### Structure

```
skills/
├── INDEX.json                       # Master index of all skills
├── git/
│   ├── git-commit.md               # Individual skill
│   └── git-bisect.md
├── security/
│   ├── sql-injection-scan.md
│   └── xss-prevention.md
├── devops/
│   ├── docker-compose-debug.md
│   └── kubernetes-troubleshoot.md
└── community/
    └── ...
```

### INDEX.json Format

```json
{
  "skills": [
    {
      "name": "git-commit",
      "description": "Write conventional commit messages",
      "version": "1.0.0",
      "author": "adam-prism",
      "tags": ["git", "commit", "conventional"],
      "triggers": ["commit", "git commit"],
      "path": "git/git-commit.md",
      "stars": 42,
      "installs": 1300
    }
  ]
}
```

### Installation

```bash
# Via CLI
adam skill install git-commit
adam skill install --from github:user/repo/ path/to/skill.md

# Via skill name (auto-resolve from INDEX)
adam skill install docker-compose-debug
```

### Search

```bash
adam skill search "docker"
adam skill search --tags security
adam skill list --installed
```

## Community Features

### Rating System

Users can rate skills after use:

```bash
adam skill rate git-commit 5
```

Ratings are tracked locally and optionally synced to the index.

### Versioning

Skills follow semver. The manager checks for updates:

```bash
adam skill update --all
adam skill update git-commit
```

### Dependencies

Skills can reference other skills or external tools:

```json
{
  "name": "full-stack-debug",
  "dependencies": ["git-bisect", "docker-compose-debug"],
  "tools_required": ["terminal", "browser"]
}
```

## Technical Implementation

### Storage

```
~/.adam/
├── skills/
│   ├── installed/           # Downloaded skills
│   │   ├── git-commit.md
│   │   └── ...
│   ├── user/                # User-created skills
│   │   └── my-custom.md
│   └── index.json           # Cached marketplace index
```

### Update Flow

```
1. User: "adam skill install git-commit"
2. CLI fetches INDEX.json from github.com/adam-prism/skills
3. Resolves "git-commit" → git/git-commit.md
4. Downloads to ~/.adam/skills/installed/git-commit.md
5. SkillManager.load() picks it up on next session
```

### Auto-Discovery

Skills are discovered automatically from:
1. `adam/skills/builtin/` — Shipping with the package
2. `~/.adam/skills/installed/` — Marketplace downloads
3. `~/.adam/skills/user/` — User-created

## Roadmap

| Feature | Priority | Notes |
|---------|----------|-------|
| `adam skill install` CLI | High | Needs `__main__.py` update |
| INDEX.json resolver | High | GitHub API integration |
| Dependency resolution | Medium | Safe loading order |
| Rating/feedback | Medium | Local tracking + optional sync |
| Skill generation | Done | Via ContinuousLearner |
| Auto-trigger on keywords | Done | SkillManager.match() |
| Version checking | Low | Semver comparison |

## Monetization (Future)

- **Verified Publisher** badge for high-quality skills
- **Skill Bundles** — Curated collections for specific domains
- **Enterprise** — Private skill registries for teams
