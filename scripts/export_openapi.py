#!/usr/bin/env python3
"""
[PHASE3] OpenAPI 3.1 spec generator for Adam Prism.

Exports the FastAPI app's routes to an OpenAPI spec file.
Generates client SDKs in multiple languages via openapi-generator-cli.

Usage:
    python scripts/export_openapi.py
    python scripts/export_openapi.py --output api-spec.json
    python scripts/export_openapi.py --generate-sdk python    # generates clients/python
    python scripts/export_openapi.py --generate-sdk typescript
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent

def main():
    parser = argparse.ArgumentParser(description="Export Adam Prism OpenAPI spec and generate SDKs")
    parser.add_argument("--output", default=str(ROOT / "api-spec.json"), help="Output spec file path")
    parser.add_argument("--generate-sdk", choices=["python", "typescript", "go", "java"], help="Generate client SDK")
    parser.add_argument("--sdk-output", help="SDK output directory")
    args = parser.parse_args()

    # Make sure backend is importable
    sys.path.insert(0, str(ROOT / "backend"))
    os.environ.setdefault("ADAM_API_KEY", "export-script")
    os.environ.setdefault("ADAM_PRODUCTION", "0")

    # Import and create app
    try:
        from adam.api.server import create_app
    except ImportError as e:
        print(f"❌ Cannot import adam.api.server: {e}")
        print("  Run: pip install -e .")
        sys.exit(1)

    print("🔧 Creating FastAPI app...")
    app = create_app()

    print(f"📝 Exporting OpenAPI spec to {args.output}...")
    spec = app.openapi()

    # Post-process spec: add info, servers, security
    spec.setdefault("info", {})
    spec["info"].update({
        "title": "Adam Prism API",
        "version": "2.0.0",
        "description": "API for the Adam Prism AI agent framework — built-in security, ethics, memory, and 25+ channel integrations.",
        "contact": {
            "name": "Mohamed Othman",
            "email": "othmastar@gmail.com",
            "url": "https://github.com/othmastar/adam-prism",
        },
        "license": {"name": "Apache-2.0", "url": "https://www.apache.org/licenses/LICENSE-2.0"},
    })

    spec.setdefault("servers", [
        {"url": "http://localhost:8000", "description": "Local development"},
        {"url": "https://api.adam-prism.example.com", "description": "Production"},
    ])

    spec.setdefault("security", [{"BearerAuth": []}])
    spec.setdefault("components", {}).setdefault("securitySchemes", {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    })

    # Add tags
    spec["tags"] = [
        {"name": "chat", "description": "Chat endpoints — send messages, get responses"},
        {"name": "knowledge", "description": "Knowledge base — RAG with Qdrant"},
        {"name": "sessions", "description": "Chat session management"},
        {"name": "skills", "description": "Skills system"},
        {"name": "plugins", "description": "Plugin management"},
        {"name": "channels", "description": "Channel integrations (Telegram, Discord, etc.)"},
        {"name": "memory", "description": "Memory and notebook"},
        {"name": "security", "description": "Security and audit logs"},
        {"name": "scheduler", "description": "Job scheduler"},
        {"name": "ollama", "description": "Ollama model management"},
        {"name": "voice", "description": "Voice transcription and synthesis"},
        {"name": "mcp", "description": "MCP (Model Context Protocol) integration"},
        {"name": "subagents", "description": "Subagent teams"},
        {"name": "system", "description": "System status, health, diagnostics"},
        {"name": "auth", "description": "Authentication endpoints (registration, login, JWT)"},
    ]

    # Write spec
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(spec, f, ensure_ascii=False, indent=2)

    # Stats
    n_paths = len(spec.get("paths", {}))
    n_ops = sum(len([k for k in v.keys() if k in ("get", "post", "put", "delete", "patch")]) for v in spec.get("paths", {}).values())
    print(f"✅ Spec exported: {n_paths} paths, {n_ops} operations")

    # Generate SDK if requested
    if args.generate_sdk:
        generate_sdk(args.output, args.generate_sdk, args.sdk_output)

def generate_sdk(spec_path: str, language: str, output_dir: str | None = None):
    """[PHASE3] Generate client SDK from OpenAPI spec using openapi-generator."""
    if output_dir is None:
        output_dir = str(ROOT / f"clients/sdk-{language}")

    print(f"🔧 Generating {language} SDK to {output_dir}...")

    # Map language to generator name
    generators = {
        "python": "python",
        "typescript": "typescript-fetch",
        "go": "go",
        "java": "java",
    }

    cmd = [
        "openapi-generator-cli", "generate",
        "-i", spec_path,
        "-g", generators[language],
        "-o", output_dir,
        "--additional-properties", "packageName=adam_prism_client,projectName=adam-prism-sdk",
    ]

    try:
        subprocess.run(cmd, check=True)
        print(f"✅ {language} SDK generated at {output_dir}")
    except FileNotFoundError:
        print("⚠ openapi-generator-cli not found. Install with:")
        print("  npm install -g @openapitools/openapi-generator-cli")
        print("  # or")
        print("  brew install openapi-generator")
    except subprocess.CalledProcessError as e:
        print(f"❌ SDK generation failed: {e}")

if __name__ == "__main__":
    main()
