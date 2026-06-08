# Adam Prism — VS Code Extension

Your conscious AI digital twin in VS Code.

## Features

- **Open Chat** (`Ctrl+Alt+A`) — Chat with آدم directly in VS Code
- **Explain Code** (`Ctrl+Alt+E`) — Select code and get explanations in Arabic
- **Review Code** — Security and bug review of selected code
- **Debug Code** — Find bugs and get fixes
- **Write Tests** — Generate unit tests for selected code
- **Ask About File** — Ask questions about the current file

## Requirements

- Adam Prism API server running (see [adam-prism on PyPI](https://pypi.org/project/adam-prism/))
- Default endpoint: `http://localhost:8000`

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `adam-prism.endpoint` | `http://localhost:8000` | API server URL |
| `adam-prism.apiKey` | — | API key (optional) |
| `adam-prism.language` | `ar` | Response language (ar/en) |
| `adam-prism.maxTokens` | `4096` | Max response tokens |

## Commands

- `آدم: Open Chat` — Open chat panel
- `آدم: Explain Selected Code` — Explain selection
- `آدم: Review Selected Code` — Security review
- `آدم: Debug Selected Code` — Debug with fixes
- `آدم: Write Test for Selected Code` — Generate tests
- `آدم: Ask About Current File` — File-level questions
- `آدم: Set API Endpoint` — Change server URL

## Development

```bash
npm install
npm run compile
# Then F5 in VS Code to debug
```
