# Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),  
and this project adheres to [Semantic Versioning](https://semver.org/).

---

## [Unreleased]
### Added
- _Nothing yet._

### Changed
- _Nothing yet._

### Deprecated
- _Nothing yet._

### Removed
- _Nothing yet._

### Fixed
- _Nothing yet._

---

## [0.5.0] — 2025-11-10
### Added
- **Typer-based CLI:** `mxm-config install-config` with:
  - `--app-id`, `--mode {shipped,seed,empty}`, `--pkg`, `--seed-root`, `--dest-root`,
    `--overwrite`, `--no-sentinel`, `--json`.
- **Reporting structures:** `InstallReport` and `InstalledFile` (in `mxm.config.reports`)
  with `to_dict()`, `pretty()`, and strict/frozen dataclasses.
- **IDs validation:** `validate_app_id()` with comprehensive tests.
- **Packaging:** ship seeds from `src/mxm/config/_data/seeds/**` in the wheel.
- **Makefile:** added/updated `clean` and `distclean` targets and integrated CLI tests.

### Changed
- **Unified installer API:** `install_config(app_id, *, mode={'shipped','seed','empty'}, ...) -> InstallReport`
  (consolidates previous installer paths).
- Tests refactored to target `install_config` and single-source seeds.

### Deprecated
- `install_all(...)` remains available but emits `DeprecationWarning`. Use `install_config(...)`.

### Notes
- 0.5.0 **supersedes** the previously drafted but unreleased 0.4.0. All 0.4.0 changes are included here.

---
## [0.4.0] _never released_
> Draft notes existed (2025-11-06) but were not tagged or published. Changes were folded into **0.5.0**.

### Added
- `install_config(app_id, *, mode={'shipped','seed','empty'}, ...) -> InstallReport`
- `DefaultsMode` enum and `InstallReport` dataclass.
- Shipped defaults under `mxm.config._data.seeds/` (single source of truth).

### Changed
- Tests migrated to `install_config` and single-source seeds (no duplication).

### Deprecated
- `install_all(...)` — still available but emits `DeprecationWarning`. Use `install_config(...)`.

### Notes
- No breaking changes. Removal of `install_all` will happen in a future major/minor (TBD).
## [0.3.0] - 2025-10-22

### Added
- `make_view(cfg, path, *, readonly=True, resolve=False)` for safe, typed, **read-only subconfig views**. Enforces that `path` resolves to a mapping (`DictConfig`); raises `TypeError` for lists or primitive leaves.
- Tests: coverage for nested selection, interpolation resolution, read-only semantics, identity (no deep copy), error paths (missing path, non-`DictConfig` input, non-mapping selections).

### Changed
- Co-locate `make_subconfig` implementation with `make_view` in `mxm_config/helpers.py`.
- Re-export `make_subconfig` and `make_view` from package root (`mxm_config`).
- Docstrings and README sections (“View vs Subconfig”) updated for clarity.

### Removed
- `mxm_config/api.py` (legacy location for `make_subconfig`)—removed to simplify the public surface. Import from `mxm_config` or `mxm_config.helpers` instead.

## [0.2.5] — 2025-10-19
### Changed
- CI: Switch version-check to `tomllib.load(open(..., 'rb'))` to avoid bytes/str mismatch.
- CI: Re-run publish via GitHub Actions (Trusted Publishing / OIDC) on tag `v0.2.5`.

### Fixed
- Publishing pipeline now succeeds; `mxm-config` is published to PyPI from GitHub Actions.

## [0.2.4] — 2025-10-19
> Note: Tag exists but PyPI publish failed due to CI version-check bug; superseded by 0.2.5.

### Added
- GitHub Actions workflow `release.yml` to publish to PyPI using Trusted Publishing (OIDC).
- GitHub environment `pypi` with required reviewer & wait timer.

### Changed
- Packaging hygiene: ensure `dist/`, `build/`, and `*.egg-info/` excluded from VCS/sdist.
- Project metadata polish (classifiers/URLs), keep import path `mxm_config` (no API change).
## v0.2.3 — 2025-10-16
### Changed
- Normalized packaging metadata to Poetry-native layout:
  - Moved project metadata from `[project]` to `[tool.poetry]`.
  - Declared `python` constraint under `[tool.poetry.dependencies]`.
  - Added `Typing :: Typed` classifier and ensured `py.typed` is included.
- No runtime code changes.

### Notes
- This release improves build/publish consistency for PyPI and avoids mixed metadata sources.

## v0.2.2 — 2025-10-16
### Added
- `make_subconfig(data: Mapping[str, Any], *, readonly=True, resolve=False) -> MXMConfig`  
  Factory to build small, dot-accessible config objects from plain dicts without importing OmegaConf.  
  Useful for package boundaries (e.g., DataIO) and unit tests.

### Notes
- Re-exported via `from mxm_config import make_subconfig`.
- Non-breaking; complements v0.2.1’s `MXMConfig` typing surface.

## v0.2.1 — 2025-10-16
### Added
- **Typing surface for consumers:** exported `MXMConfig` Protocol so downstream packages can type `cfg` without importing OmegaConf.
- **Public API returns protocol:** `load_config(...) -> MXMConfig` (backed by OmegaConf `DictConfig` internally).
- **PEP 561 support:** ship `mxm_config/py.typed` so Pyright/Mypy treat inline annotations as authoritative.

### Notes
- No runtime behavior change; this is a typing/packaging improvement.
- Downstreams should import: `from mxm_config import MXMConfig, load_config` and annotate parameters as `cfg: MXMConfig`.

## v0.2.0 — 2025-10-05
### Added
- Automatic registration of standard MXM resolvers (`cwd`, `home`, `env`, `timestamp`)  
  on package import for all MXM packages.
- Exposed `install_all` and `load_config` as top-level API functions in `__all__`.

### Notes
- Resolvers use the `${name:}` syntax (with trailing colon) under OmegaConf ≥2.3.
- `register_mxm_resolvers()` now runs automatically when importing `mxm_config`.

## [0.1.0] - 2025-09-22
### Added
- Initial release of **mxm-config**.
- Deterministic configuration layering:
  1. `default.yaml`
  2. `environment.yaml`
  3. `machine.yaml`
  4. `profile.yaml`
  5. `local.yaml`
  6. explicit overrides dict
- Automatic injection of context variables (`mxm_env`, `mxm_profile`, `mxm_machine`).
- Interpolation resolution for `${...}` expressions.
- Installer utility (`install_all`) to scaffold package configs into `~/.config/mxm/`.
- Demo package (`examples/demo_config`) with sample YAMLs for testing.
- Full pytest suite with type checking (pyright strict mode).
