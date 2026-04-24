# Repository Guidelines

## Project Structure & Module Organization
This repository is a small AstrBot plugin with a single runtime module. `main.py` contains the plugin class, command handler, and HTTP request logic. `metadata.yaml` defines the plugin name, display text, version, repository URL, and supported platforms. `README.md` is still close to the upstream template, so treat the code and metadata as the current source of truth. The `wiki/` folder can hold design notes or usage docs; keep executable plugin logic out of it.

## Build, Test, and Development Commands
There is no standalone build step in this repo. Typical local checks are:

```powershell
python -m py_compile main.py
python -m pytest
```

Use `py_compile` for a fast syntax check before committing. Run `pytest` only after adding tests; the repository does not currently ship a test suite. For full integration testing, load the plugin inside an AstrBot instance from `data/plugins/astrbot_plugin_search_mikan_bangumi` and invoke the `蜜柑搜番` command in chat.

## Coding Style & Naming Conventions
Follow Python conventions: 4-space indentation, `snake_case` for functions and variables, `UPPER_SNAKE_CASE` for module constants such as `MIKAN_RSS_SEARCH_URL`, and `CapWords` for classes like `MikanSearchPlugin`. Keep async handlers non-blocking; wrap synchronous network I/O with `asyncio.to_thread`, as done in `search_mikan`. Prefer standard-library dependencies unless AstrBot already requires something heavier. Keep comments short and only where intent is not obvious.

## Testing Guidelines
When adding tests, create a `tests/` directory at the repository root and name files `test_*.py`. Focus first on deterministic units such as `_build_search_url()` and error handling around `_fetch_rss_sync()`. Mock outbound HTTP requests instead of hitting the live Mikan endpoint in CI. Until coverage tooling is added, require at least one happy-path and one failure-path test for new behavior.

## Commit & Pull Request Guidelines
The current history starts with `Initial commit`, so no strict convention is established yet. Use short, imperative commit messages such as `Add RSS parsing for mikan results` or `Handle empty keyword input`. Keep pull requests narrow and include: what changed, how it was tested, any AstrBot compatibility impact, and screenshots or chat transcripts when user-visible responses change.

## Security & Configuration Tips
Do not hardcode secrets or cookies. Set explicit network timeouts for external requests, validate user input before composing URLs, and avoid returning unbounded RSS payloads to chat. If new configuration is introduced, document it in `README.md` and keep defaults safe for public bot deployments.

## Language
Use Chinese when communicating with me, and write code comments in Chinese as well.
