# Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),  
and this project adheres to [Semantic Versioning](https://semver.org/).

---

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
