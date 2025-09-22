# Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),  
and this project adheres to [Semantic Versioning](https://semver.org/).

---

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
