# CI/CD Pipeline

## GitHub Actions

`.github/workflows/ci.yml`

### Trigger

```yaml
on: [push, pull_request, workflow_dispatch]
```

### Jobs

#### `test` (Python 3.12)

```yaml
steps:
  - checkout
  - setup-python@v5 (3.12)
  - Install dependencies (pip + requirements.txt + pytest + -e .)
  - Run tests (pytest -k "not slow" -x --tb=long)
  - Show failures (::error annotations)
  - Upload test output (artifact)
  - Build package (sdist + wheel)
```

### Key Features

- **`set -o pipefail`** — يضمن إن `tee` ما يخفيش exit code
- **`::error` annotations** — أول 15 failure line تظهر public في GitHub UI
- **Artifact upload** — test output متاح للتحميل
- **`-x` flag** — يقف عند أول failure (توفير وقت)

### Test Stats

```
251 passed, 5 skipped, 6 deselected in 0.65s
```

- 5 skipped = engine tests (تحتاج Ollama)
- 6 deselected = slow tests (`-k "not slow"`)

### Artifact

Test output متاح كـ artifact (`test-output.zip`):
- `test_output.txt` — full pytest output
- ~7 KB size

### Status Badge

```markdown
![CI](https://github.com/othmastar/adam-prism/actions/workflows/ci.yml/badge.svg)
```

## Build

```bash
python -m build --sdist --wheel
```

ينتج:
- `dist/adam_prism-1.0.0b1-py3-none-any.whl`
- `dist/adam-prism-1.0.0b1.tar.gz`

## Release (Future)

```yaml
release:
  if: startsWith(github.ref, 'refs/tags/v')
  runs-on: ubuntu-latest
  steps:
    - build
    - publish to PyPI
    - create GitHub Release
```

## Historical CI Fixes

### Problem 1: `| tee` masking exit code (Runs #1–#13)

```bash
python -m pytest ... | tee /tmp/test_output.txt
# tee always returns 0 — every run was "green" but actually failing
```

**Fix:** `set -o pipefail`

### Problem 2: Non-PEP 440 version (Runs #1–#4)

`1.0.0-experimental` and `1.0.0-beta` — rejected by modern pip/setuptools

**Fix:** `1.0.0b1`

### Problem 3: `uv` build conflicts (Runs #3–#5)

`uv pip install` caused dependency resolution failures

**Fix:** Switch to `pip` directly

### Problem 4: Hardcoded MEMORY_DB path (Run #9)

```python
MEMORY_DB = "/mnt/Workspace/adam_v8_output/adam_memory.db"
```

**Fix:** `os.getcwd()` based path

### Problem 5: embed() before cache check (Runs #1–#21)

`MemorySystem.search()` called `embed()` (HTTP→Ollama) before checking cache.
On CI without Ollama, `httpx.ConnectError` killed the test.

**Fix:** Check cache first, then embed. (`adam/memory/system.py:150`)
