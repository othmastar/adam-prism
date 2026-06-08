# Contributing to Adam Prism

First off, thanks for taking the time to contribute! 🎉

> **آدم بريزم مشروع مفتوح المصدر — أي مساهمة بتفرق**

## Code of Conduct

By participating, you agree to maintain a respectful, inclusive environment. Discrimination, harassment, or toxicity will not be tolerated.

## How to Contribute / إزاي تساهم

### 🐛 Report Bugs

Open an [issue](https://github.com/othmastar/adam-prism/issues) with:
- Python version, OS, reproduction steps
- Expected vs actual behavior
- Relevant test output or logs

### 💡 Suggest Features

Open an issue with the `enhancement` tag:
- Describe the feature, use case, and architecture fit
- Arabic or English — both welcome

### 🌍 Help with Arabic / تساعد في العربي

We especially need help with:
- Natural Egyptian Arabic training data
- Testing responses for naturalness
- Dialect variation coverage
- Technical term localization

### 🔧 Submit Code

1. **Fork & clone**
   ```bash
   git clone https://github.com/your-username/adam-prism.git
   cd adam-prism
   ```

2. **Set up environment**
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -e .
   ```

3. **Run tests before changes**
   ```bash
   pytest tests/ -v -k "not slow"
   ```

4. **Create a branch**
   ```bash
   git checkout -b feature/your-feature
   ```

5. **Make your changes**
   - Follow existing code style (no comments needed)
   - Add tests for new functionality
   - Old import paths must keep working (see `core/` for re-export pattern)

6. **Run tests again**
   ```bash
   pytest tests/ -v -k "not slow"
   pytest tests/test_your_feature.py -v
   ```

7. **Commit & push**
   ```bash
   git commit -m "feat: add your feature"
   git push origin feature/your-feature
   ```

8. **Open a Pull Request**
   - Describe your changes
   - Reference any related issues
   - Wait for CI to pass

## Development Guidelines

### Code Style
- **Python 3.12+** type hints everywhere
- No docstrings/comments unless the logic is genuinely non-obvious
- Egyptian Arabic for user-facing strings, English for code/APIs
- One class per file, single responsibility per module
- Follow existing naming conventions (snake_case for functions, PascalCase for classes)

### Architecture Rules
- New modules go under `adam/` package
- Old import paths must have re-exports (see `core/`, `api/`, `memory/` for patterns)
- Every public function needs a test
- Network-dependent features must have graceful fallback (skip if unavailable)
- No hardcoded secrets or API keys

### Testing
- Tests go in `tests/`
- Use `pytest` with `asyncio_mode = "auto"`
- Mark slow/integration tests with `@pytest.mark.slow`
- Mock external services (Ollama, Qdrant, etc.)
- Aim for > 80% coverage on new code

### Frontend (web-ui/)
- Next.js 16 + Tailwind v4 + shadcn/ui
- RTL/LTR support required for all components
- Arabic (ar) and English (en) translations for all UI strings
- Dark mode only (light mode not supported yet)
- Zustand for state management

## Project Structure

```
adam/           ← Python source package
tests/          ← Pytest test suite
config/         ← Default configuration files
docs/           ← Documentation & diagrams
deploy/         ← Docker & deployment scripts
scripts/        ← Utility & training scripts
web-ui/         ← Next.js frontend (separate package)
data/           ← Training datasets
.github/        ← CI workflows & templates
```

## Questions?

Open a [discussion](https://github.com/othmastar/adam-prism/discussions) or tag `@othmastar`.

---

**Made with ❤️ by Mohamed Othman — عين الحارس**
