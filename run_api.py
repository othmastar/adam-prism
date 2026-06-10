import asyncio
import uvicorn
import logging
import sys
from pathlib import Path

# Add project root and backend to path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from api.server import create_app
from core.engine import AdamPrismEngine

async def main():
    # Load config
    import json
    import os
    config_path = Path(__file__).parent / "config" / "default.json"
    config = {}
    if config_path.exists():
        with open(config_path) as f:
            config = json.load(f)
    else:
        config = {
            "ollama_base": "http://localhost:11434",
            "model_name": "adam-prism-v13:latest",
            "context_window": 4096,
            "token_budget": 4000,
        }

    # Environment variables override config (useful for Docker)
    env_overrides = {
        "OLLAMA_BASE": "ollama_base",
        "MODEL_NAME": "model_name",
        "QDRANT_URL": "qdrant_url",
        "API_HOST": "api_host",
        "API_PORT": "api_port",
        "INFERENCE_MODE": "inference_mode",
    }
    for env_key, config_key in env_overrides.items():
        if env_key in os.environ:
            val = os.environ[env_key]
            # Convert numeric ports
            if config_key in ("api_port",):
                config[config_key] = int(val)
            else:
                config[config_key] = val

    # Create engine
    engine = AdamPrismEngine(config)
    app = create_app(engine)

    # Start server
    config_uv = uvicorn.Config(
        app,
        host=config.get("api_host", "0.0.0.0"),
        port=config.get("api_port", 8000),
        log_level="info"
    )
    server = uvicorn.Server(config_uv)
    await server.serve()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
