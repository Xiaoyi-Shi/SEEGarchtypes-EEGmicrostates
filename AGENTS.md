# Repository Guidelines

## Project Structure & Module Organization
This repository is a small `src`-layout Python package. Put application code in `src/seeg_eegmicrostates/`; the current CLI entry point resolves to `seeg_eegmicrostates:main`. Project metadata and dependencies live in `pyproject.toml`, and `uv.lock` pins the environment for reproducible installs. Use `openspec/` for spec-driven work: `openspec/specs/` for accepted specs and `openspec/changes/` for active proposals. Do not commit local environment contents from `.venv/`.

## Build, Test, and Development Commands
Use `uv` for all local workflows:

- `uv sync --dev`: install runtime and development dependencies into `.venv`.
- `uv run seeg-eegmicrostates`: run the current package entry point.
- `uv run pytest`: run tests with `pytest` from the repo root.
- `uv build`: build source and wheel distributions via `uv_build`.

Example: run `uv sync --dev` once, then use `uv run pytest` before opening a PR.

## Coding Style & Naming Conventions
Target Python 3.13+ and keep code PEP 8-aligned: 4-space indentation, clear type hints, and small functions. Use `snake_case` for modules, files, and functions, `CapWords` for classes, and `UPPER_SNAKE_CASE` for constants. Keep importable package code under `src/`; avoid placing runtime logic in loose top-level scripts. No formatter or linter is configured yet, so keep style consistent and readable when adding new modules.

## Testing Guidelines
`pytest` is already included in the dev dependencies, but the repository currently has no test suite. Add tests in a top-level `tests/` directory that mirrors the package layout, for example `tests/test_cli.py`. Name files `test_*.py` and test functions `test_*`. For EEG/SEEG processing code, prefer small synthetic fixtures over checked-in raw datasets, and cover every new branch or bug fix you introduce.

## Commit & Pull Request Guidelines
There is no commit history yet, so establish the convention now: write short, imperative commit subjects such as `Add initial connectivity loader`. Keep commits focused and reference an OpenSpec change when relevant. PRs should include a concise summary, the commands you ran (`uv run pytest`, etc.), and notes about dependency, data, or output changes. Include screenshots only when a change affects generated figures or visual outputs.

## Security & Data Handling
Do not commit `.venv/`, build artifacts, or raw EEG/SEEG data exports. Large binary datasets and patient-derived files should stay out of git; document their expected location instead.
