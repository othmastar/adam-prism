# Troubleshooting Guide

Common issues and how to fix them.

## Table of Contents
- [Installation Issues](#installation-issues)
- [Ollama Issues](#ollama-issues)
- [Qdrant Issues](#qdrant-issues)
- [API / Server Issues](#api--server-issues)
- [Web UI Issues](#web-ui-issues)
- [Desktop App Issues](#desktop-app-issues)
- [Mobile App Issues](#mobile-app-issues)
- [Authentication Issues](#authentication-issues)
- [Performance Issues](#performance-issues)
- [Docker Issues](#docker-issues)
- [Kubernetes Issues](#kubernetes-issues)
- [Development Issues](#development-issues)

---

## Installation Issues

### `pip install adam-prism` fails

**Problem:** pip can't find the package or version conflicts.

**Solution:**
```bash
# Make sure pip is up to date
python -m pip install --upgrade pip setuptools wheel

# Try installing from source
git clone https://github.com/othmastar/adam-prism.git
cd adam-prism
pip install -e .

# If you have dependency conflicts, use a virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -e .
```

### Python version is too old

**Problem:** Adam Prism requires Python 3.12+.

**Solution:**
```bash
# Check your Python version
python --version

# On macOS with Homebrew
brew install python@3.12

# On Ubuntu/Debian
sudo apt install python3.12 python3.12-venv

# On Windows: Download from python.org

# Use pyenv for multiple versions
pyenv install 3.12
pyenv local 3.12
```

### `python -m adam` not found

**Problem:** The entry point isn't installed properly.

**Solution:**
```bash
# Reinstall in editable mode
pip install -e .

# Or check if the entry point exists
ls venv/bin/adam-prism  # should exist

# If using system Python, try:
which adam-prism
python -c "import adam; print(adam.__file__)"
```

---

## Ollama Issues

### "Connection refused" to localhost:11434

**Problem:** Ollama isn't running.

**Solution:**
```bash
# macOS
brew services start ollama

# Linux
sudo systemctl start ollama
# OR run manually:
ollama serve

# Windows
# Start from Start Menu or run:
ollama serve

# Verify
curl http://localhost:11434/api/tags
```

### Ollama is slow / model is large

**Problem:** Default `gemma3:8b` model is 5GB and may be slow on CPU.

**Solution:**
```bash
# Use a smaller model
ollama pull gemma2:2b
# Set in .env:
ADAM_INFERENCE_MODE=ollama
ADAM_MODEL_NAME=gemma2:2b

# Or use a faster model
ollama pull phi3:mini  # 2.3GB, fast

# Enable GPU acceleration (Linux)
# Make sure nvidia-container-toolkit is installed
# Verify with:
nvidia-smi
```

### "model not found" error

**Problem:** The configured model isn't pulled yet.

**Solution:**
```bash
# Pull the default model
ollama pull gemma3:8b

# Or change the model name in .env
ADAM_MODEL_NAME=llama3.1:8b
ollama pull llama3.1:8b
```

---

## Qdrant Issues

### "Connection refused" to localhost:6333

**Problem:** Qdrant isn't running.

**Solution:**
```bash
# Run with Docker (recommended)
docker run -d --name adam-qdrant -p 6333:6333 qdrant/qdrant

# Or download binary
# See: https://qdrant.tech/documentation/quick_start/

# Verify
curl http://localhost:6333/
```

### Qdrant collection not found

**Problem:** Collection needs to be created.

**Solution:**
```bash
# Adam Prism auto-creates collections on first use
# Force creation by running:
python -c "
from adam.knowledge.qdrant_store import QdrantStore
store = QdrantStore({'qdrant_url': 'http://localhost:6333'})
store.ensure_collection('knowledge')
"

# Or via REST API
curl -X PUT http://localhost:6333/collections/knowledge \
  -H "Content-Type: application/json" \
  -d '{"vectors": {"size": 384, "distance": "Cosine"}}'
```

---

## API / Server Issues

### Server won't start: "Address already in use"

**Problem:** Port 8000 is occupied.

**Solution:**
```bash
# Use a different port
python main.py --port 8001

# Or find and kill the process using port 8000
lsof -i :8000  # macOS/Linux
# Then: kill <PID>

# On Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### "ModuleNotFoundError" for adam

**Problem:** The package isn't installed.

**Solution:**
```bash
# Reinstall in editable mode
pip install -e .

# Or add backend to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/backend"
python run_api.py
```

### API returns 401/403 Unauthorized

**Problem:** Missing or wrong API key.

**Solution:**
```bash
# Set the API key in .env
ADAM_API_KEY=your-secret-key-here

# Or pass via Authorization header
curl -H "Authorization: Bearer your-secret-key-here" \
  http://localhost:8000/api/chat

# Generate a new one:
openssl rand -hex 32
```

### Slow first response

**Problem:** Ollama loads the model on first request.

**Solution:**
```bash
# Pre-warm the model
curl -X POST http://localhost:11434/api/generate \
  -d '{"model": "gemma3:8b", "prompt": "hi", "stream": false}'

# Or set OLLAMA_KEEP_ALIVE=24h in .env to keep model in memory
OLLAMA_KEEP_ALIVE=24h
```

---

## Web UI Issues

### White screen / blank page

**Problem:** JavaScript error or backend not reachable.

**Solution:**
```bash
# Open browser DevTools (F12) → Console tab
# Look for errors

# Check if API is reachable:
curl http://localhost:8000/

# Set the correct API URL in .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000

# Clear browser cache and reload
```

### `next-auth` errors

**Problem:** Missing `NEXTAUTH_SECRET`.

**Solution:**
```bash
# Generate a secret
openssl rand -base64 32

# Add to .env.local
NEXTAUTH_SECRET=your-generated-secret
NEXTAUTH_URL=http://localhost:3000
```

### CORS errors

**Problem:** Backend not allowing the frontend origin.

**Solution:**
```bash
# In backend .env
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# Or for production
CORS_ORIGINS=https://yourdomain.com
```

---

## Desktop App Issues

### "Electron failed to install correctly"

**Problem:** Native dependencies not built.

**Solution:**
```bash
cd frontend/desktop-app
rm -rf node_modules
npm install
npm run postinstall  # rebuilds native modules
```

### White screen in production build

**Problem:** CSP or contextIsolation issue.

**Solution:**
```bash
# Check the browser DevTools (Ctrl+Shift+I) in dev mode first
npm run dev

# If CSP is blocking scripts, add a CSP exception
# Or check deploy/Dockerfile for missing files
```

### Auto-update not working

**Problem:** Not signed or no GitHub release.

**Solution:**
```bash
# Auto-update requires:
# 1. GitHub release with adam-prism-v1.0.0 in tag
# 2. Code-signed binaries (for macOS/Windows)
# 3. GITHUB_TOKEN in repo secrets for CD workflow

# Check releases at: https://github.com/othmastar/adam-prism/releases
```

---

## Mobile App Issues

### "Network request failed" on physical device

**Problem:** Mobile can't reach localhost.

**Solution:**
```typescript
// In mobile-app-expo/.env, set:
EXPO_PUBLIC_API_URL=http://YOUR-LAN-IP:8000
// E.g., http://192.168.1.100:8000

// Find your IP:
// macOS/Linux: ifconfig | grep "inet "
// Windows: ipconfig
```

### Android emulator can't reach API

**Problem:** Android emulator uses 10.0.2.2 for host.

**Solution:**
```bash
# In mobile-app-expo/.env
EXPO_PUBLIC_API_URL=http://10.0.2.2:8000
```

### Expo build fails

**Problem:** Missing credentials or wrong config.

**Solution:**
```bash
# Login to Expo
npx expo login

# Clear cache
npx expo start -c

# For EAS Build
npm install -g eas-cli
eas login
eas build --platform android --clear-cache
```

---

## Authentication Issues

### "Invalid credentials" on login

**Problem:** Wrong username/password or user doesn't exist.

**Solution:**
```bash
# Register a new user first
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "you@example.com", "username": "you", "password": "yourpass123"}'

# Then login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username_or_email": "you", "password": "yourpass123"}'
```

### JWT token expired

**Problem:** Default token TTL is 7 days.

**Solution:**
```python
# In your client code, handle 401 by refreshing
import httpx

client = httpx.AsyncClient(base_url="http://localhost:8000")
tokens = await login()

# When you get 401:
refresh_resp = await client.post(
    "/api/auth/refresh",
    json={"refresh_token": tokens["refresh_token"]}
)
new_access = refresh_resp.json()["access_token"]
```

---

## Performance Issues

### Slow chat responses

**Problem:** Slow model or insufficient resources.

**Solutions:**
1. **Use a smaller model:**
   ```bash
   ollama pull phi3:mini  # 2.3GB
   # Update ADAM_MODEL_NAME=phi3:mini
   ```

2. **Enable GPU acceleration:**
   - Linux: Install nvidia-container-toolkit, restart Ollama
   - macOS: Ollama uses Metal automatically

3. **Increase Ollama's context:**
   ```bash
   export OLLAMA_NUM_CTX=8192
   ```

4. **Use Redis caching:**
   ```bash
   # In .env
   ADAM_REDIS_URL=redis://localhost:6379/0
   ```

### High memory usage

**Problem:** Large context or too many loaded components.

**Solution:**
```bash
# Reduce context window
ADAM_CONTEXT_WINDOW=2048
ADAM_TOKEN_BUDGET=2000

# Use PostgreSQL instead of SQLite for multi-worker
ADAM_DATABASE_URL=postgresql://user:pass@localhost:5432/adam

# Monitor with
curl http://localhost:8000/metrics
```

---

## Docker Issues

### "Cannot connect to Docker daemon"

**Problem:** Docker Desktop not running.

**Solution:**
```bash
# macOS: Start Docker Desktop from Applications
# Linux: 
sudo systemctl start docker
sudo usermod -aG docker $USER  # logout/login after
# Windows: Start Docker Desktop from Start Menu
```

### Container exits immediately

**Problem:** Missing env vars or config.

**Solution:**
```bash
# Check logs
docker logs adam-api

# Run interactively
docker run -it --rm \
  -e ADAM_API_KEY=test \
  -e ADAM_OLLAMA_BASE=http://host.docker.internal:11434 \
  adam-prism-api:latest bash

# Note: Use host.docker.internal (macOS/Windows) or
# 172.17.0.1 (Linux) to reach host services
```

### Permission denied on volumes

**Problem:** UID mismatch.

**Solution:**
```bash
# Match container UID (1001) to host user
sudo chown -R 1001:1001 ./data ./logs

# Or use user mapping in compose
services:
  api:
    user: "1001:1001"
```

---

## Kubernetes Issues

### ImagePullBackOff

**Problem:** Image not found or auth issue.

**Solution:**
```bash
# Check image name
kubectl describe pod <pod-name> | grep Image:

# For private registry, create secret
kubectl create secret docker-registry ghcr-secret \
  --docker-server=ghcr.io \
  --docker-username=YOUR-USERNAME \
  --docker-password=YOUR-TOKEN

# Reference in deployment
spec:
  imagePullSecrets:
    - name: ghcr-secret
```

### CrashLoopBackOff

**Problem:** Container crashes on start.

**Solution:**
```bash
# Check logs
kubectl logs -f <pod-name>

# Check events
kubectl describe pod <pod-name>

# Common causes:
# 1. Missing env vars (check helm values)
# 2. Wrong secrets (check ADAM_API_KEY, etc.)
# 3. Can't reach Ollama/Qdrant (check service DNS)
```

### Pod stuck in Pending

**Problem:** Insufficient resources or PVC issues.

**Solution:**
```bash
# Check events
kubectl describe pod <pod-name> | grep -A 5 Events

# If PVC pending:
kubectl get pvc
# Check storage class exists and has capacity

# If insufficient CPU/memory:
# Reduce requests/limits in values.yaml
```

---

## Development Issues

### Tests fail with "Qdrant not available"

**Problem:** Qdrant isn't running during tests.

**Solution:**
```bash
# Option 1: Start Qdrant
docker run -d -p 6333:6333 qdrant/qdrant

# Option 2: Skip integration tests
pytest -k "not integration"

# Option 3: Use mocks
# (see tests/conftest.py for examples)
```

### TypeScript errors in web-ui

**Problem:** Strict mode now enabled.

**Solution:**
```bash
cd frontend/web-ui
npx tsc --noEmit  # see all errors
# Fix them one by one — this is a feature, not a bug!
# Don't revert to ignoreBuildErrors: true
```

### Hot reload not working

**Problem:** Vite/Next.js cache stale.

**Solution:**
```bash
# Clear Next.js cache
rm -rf frontend/web-ui/.next
npm run dev

# Clear Vite cache
rm -rf frontend/desktop-app/node_modules/.vite
npm run dev
```

---

## Getting More Help

If you're still stuck:

1. **Check the [Discussions](https://github.com/othmastar/adam-prism/discussions)**
   - Search for similar issues
   - Ask the community

2. **Run the doctor command:**
   ```bash
   adam-doctor
   ```
   This will diagnose most common issues.

3. **Enable debug logging:**
   ```bash
   export ADAM_LOG_LEVEL=DEBUG
   export ADAM_LOG_JSON=1
   python main.py
   ```

4. **Check the [GitHub Issues](https://github.com/othmastar/adam-prism/issues)**
   - Open a new issue with:
     - Output of `adam-doctor`
     - Relevant log lines
     - Steps to reproduce
     - Your environment (OS, Python version, etc.)

5. **Contact security issues privately:**
   - See [SECURITY.md](SECURITY.md) for disclosure policy

---

## Common Error Codes

| Code | Meaning | Common Cause |
|------|---------|--------------|
| 400 | Bad Request | Invalid input (check Pydantic schema) |
| 401 | Unauthorized | Missing or invalid auth |
| 403 | Forbidden | Wrong API key or insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 413 | Payload Too Large | Request body > 10MB (default) |
| 422 | Unprocessable Entity | Pydantic validation failed |
| 429 | Too Many Requests | Rate limit exceeded (wait 60s) |
| 500 | Internal Server Error | Bug in our code (open issue) |
| 503 | Service Unavailable | Subsystem not ready (check Ollama/Qdrant) |

---

Last updated: 2026-06-14
