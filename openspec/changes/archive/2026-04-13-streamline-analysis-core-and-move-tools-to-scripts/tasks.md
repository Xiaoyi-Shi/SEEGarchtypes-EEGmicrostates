## 1. OpenSpec And Interface Alignment

- [x] 1.1 Update the retained specs to reflect the paper-focused command surface and scripts-owned tooling boundary
- [x] 1.2 Trim the public CLI and workflow exports to the retained analysis core

## 2. Core Code Simplification

- [x] 2.1 Remove public region activity/connectivity stages and retired exploratory branch dispatch from the Python package
- [x] 2.2 Remove dead package-level report/plot compatibility paths so the package only exports result tables and manifests
- [ ] 2.3 Drop legacy config and coupling exports that only supported retired branches

## 3. Verification And Documentation

- [x] 3.1 Update tests to match the retained analysis surface and scripts-owned tooling boundary
- [x] 3.2 Update README and `scripts/README.md` to document the streamlined workflow
- [x] 3.3 Run `uv run pytest` and fix regressions
