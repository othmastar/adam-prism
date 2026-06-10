# Adam Prism — Desktop App

Lightweight Electron chat client for Adam Prism.

## Features

- System tray integration (minimizes to tray)
- Custom frameless window
- Dark theme with RTL Arabic support
- Settings panel (endpoint + API key)
- Connection status indicator
- Markdown rendering (code blocks, bold)

## Quick Start

```bash
# Install dependencies
npm install

# Run
npm start

# Build for your platform
npm run build:linux   # → dist/*.AppImage
npm run build:mac     # → dist/*.dmg
npm run build:win     # → dist/*.exe
```

## Requirements

- Adam Prism API server running (default: `http://localhost:8000`)
- Node.js 18+
