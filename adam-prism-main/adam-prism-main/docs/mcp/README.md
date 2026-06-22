# Model Context Protocol (MCP) Integration

Adam Prism supports the [Model Context Protocol (MCP)](https://modelcontextprotocol.io) — the open standard for connecting AI applications with tools and data sources.

## Architecture

Adam Prism acts as both an **MCP host** (runs its own MCP server exposing tools) and an **MCP client** (can connect to external MCP servers).

```
┌─────────────────┐     MCP Protocol      ┌──────────────────┐
│  Claude Desktop  │◄─────────────────────►│  Adam Prism      │
│  Cursor          │                       │  - memory tools   │
│  VS Code         │                       │  - browser tools  │
│  Any MCP Host    │                       │  - skills system  │
└─────────────────┘                       │  - ...            │
                                           └──────────────────┘
```

## Quick Start

1. Install the Adam Prism MCP server:
```bash
pip install adam-prism
```

2. Configure your MCP host to connect to Adam Prism.

### Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "adam-prism": {
      "command": "adam-prism",
      "args": ["mcp"],
      "env": {
        "OLLAMA_BASE": "http://localhost:11434",
        "INFERENCE_MODE": "ollama"
      }
    }
  }
}
```

### VS Code (Cline / Continue)

Add to your `cline.json` or `continue.json`:

```json
{
  "experimental": {
    "mcpServers": {
      "adam-prism": {
        "transport": "stdio",
        "command": "adam-prism",
        "args": ["mcp"],
        "env": {
          "OLLAMA_BASE": "http://localhost:11434"
        }
      }
    }
  }
}
```

### Cursor

Add to `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "adam-prism": {
      "command": "adam-prism",
      "args": ["mcp"],
      "env": {
        "OLLAMA_BASE": "http://localhost:11434"
      }
    }
  }
}
```

## Available Tools

When connected, Adam Prism exposes these MCP tools:

| Tool | Description |
|------|-------------|
| `adam_chat` | Send a message to Adam and get a response |
| `adam_memory_store` | Store a memory with metadata |
| `adam_memory_search` | Search memories by query |
| `adam_skill_list` | List loaded skills |
| `adam_skill_load` | Load a skill by name |
| `adam_browser_fetch` | Fetch a webpage content |
| `adam_tools_execute` | Execute a system tool (terminal, files, etc.) |
| `adam_status` | Get engine status |

## Advanced: Custom MCP Server Config

```json
{
  "mcpServers": {
    "adam-prism": {
      "command": "python",
      "args": ["-m", "adam.tools.mcp_server"],
      "env": {
        "OLLAMA_BASE": "http://localhost:11434",
        "QDRANT_URL": "http://localhost:6333",
        "LOG_LEVEL": "info"
      }
    }
  }
}
```

## Docker

When running via Docker, use the HTTP transport instead:

```json
{
  "mcpServers": {
    "adam-prism": {
      "transport": "http",
      "url": "http://localhost:8000/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_API_KEY"
      }
    }
  }
}
```

## Creating Custom MCP Servers for Adam

Adam can also consume external MCP servers. Configure them in `config/mcp_servers.json`:

```json
{
  "mcp_servers": [
    {
      "name": "weather-api",
      "transport": "stdio",
      "command": "python",
      "args": ["-m", "weather_mcp_server"],
      "env": {
        "API_KEY": "your-key"
      }
    },
    {
      "name": "github-api",
      "transport": "http",
      "url": "http://localhost:9000/mcp"
    }
  ]
}
```
