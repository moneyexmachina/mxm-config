# mxm-config

![Version](https://img.shields.io/github/v/release/moneyexmachina/mxm-config)
![License](https://img.shields.io/github/license/moneyexmachina/mxm-config)
![Python](https://img.shields.io/badge/python-3.12+-blue)
[![Checked with pyright](https://microsoft.github.io/pyright/img/pyright_badge.svg)](https://microsoft.github.io/pyright/)

## Purpose

`mxm-config` provides a unified way to **install, load, layer, and resolve configuration** across all Money Ex Machina (MXM) packages and applications.  
It separates configuration from secrets and runtime metadata, enforces deterministic layering, and ensures every run has a transparent, reproducible view of its operating context.

## Design Principles

- **Separation of concerns**  
  - Configuration ≠ secrets ≠ runtime.  
  - Secrets are handled by [`mxm-secrets`](https://github.com/moneyexmachina/mxm-secrets).  
  - Runtime metadata will be handled by `mxm-runtime` (planned).  

- **Determinism**  
  - Configuration is layered in a fixed, documented order.  
  - Reproducible runs: the same context always produces the same resolved config.  

- **Transparency**  
  - Configs are plain YAML files, no hidden state.  
  - Merging order is explicit and testable.  

- **Extensibility**  
  - Layers are minimal and orthogonal.  
  - New packages can register defaults without breaking existing ones.  

## The App-Owned Config Root

Every MXM application owns a dedicated configuration directory under:

```
~/.config/mxm/<app_id>/
```

This directory is the **single source of truth** for that application’s configuration.  
All MXM tooling — loaders, resolvers, CLIs — read exclusively from this location.  
Installing configs simply scaffolds this directory; once created, it becomes user- or environment-owned.

You can override the global root with the environment variable:

```
$ export MXM_CONFIG_HOME=/custom/path
```

## Configuration Layers

At runtime, configuration is resolved by merging up to six layers in order of precedence (lowest → highest):

1. **`default.yaml`**  
   Baseline shipped with the package.  
   *Always present.*

2. **`environment.yaml`**  
   Deployment mode (`dev`, `prod`, …).  
   Each environment is a block inside this file.

3. **`machine.yaml`**  
   Host-specific overrides (paths, mounts, resources).  

4. **`profile.yaml`**  
   Role or user context (`research`, `trading`, …).  

5. **`local.yaml`**  
   Local scratchpad for ad-hoc tweaks.  
   *Ignored by version control.*

6. **Explicit overrides (dict)**  
   Passed directly in code, applied last.

## Installing Configs (Python API)

Use `install_config` to copy packaged or local defaults into the app-owned config root.

```python
from mxm.config import install_config, DefaultsMode

# Install shipped defaults (packaged resources)
install_config(
    app_id="demo",
    mode=DefaultsMode.shipped,
    shipped_package="mxm.config._data.seeds",
)

# Install from a local folder of YAMLs (dev/test mode)
from importlib.resources import as_file, files
with as_file(files("mxm.config._data") / "seeds") as p:
    install_config(app_id="demo", mode=DefaultsMode.seed, seed_root=p)

# Create an empty directory + sentinel (for CI/bootstrap)
install_config(app_id="demo", mode=DefaultsMode.empty)
```

All installs target `~/.config/mxm/<app_id>/`, ensuring every MXM component reads from a predictable, canonical location.

The function returns an **`InstallReport`** summarising created, copied, and skipped files.

### Install Modes

| Mode | Source | Typical Use | Description |
|------|---------|--------------|--------------|
| `shipped` | Packaged folder, e.g. `mxm.config._data.seeds` | End-users | Install defaults bundled with the wheel. |
| `seed` | Filesystem path (e.g. repo `_data/seeds`) | Development, testing | Install from editable on-disk seeds. |
| `empty` | None | CI, sandbox setup | Create only directory and sentinel. |


## Command-Line Interface

You can also install configurations directly from the terminal using the `mxm-config` command.

```bash
mxm-config --help
```

### Basic Usage

```bash
# Install shipped defaults (requires a package with bundled seeds)
mxm-config install-config --app-id demo --mode shipped --pkg mxm.config

# Install from a local folder of YAMLs (development/testing)
mxm-config install-config --app-id demo --mode seed --seed-root ./src/mxm/config/_data/seeds

# Create an empty config directory with sentinel only (CI/bootstrap)
mxm-config install-config --app-id demo --mode empty

# Show JSON report instead of human-readable summary
mxm-config install-config \
  --app-id demo \
  --mode shipped --pkg mxm.config \
  --dest-root ~/.config/mxm \
  --overwrite \
  --json
```

### Options Overview

| Option | Description |
|--------|--------------|
| `--app-id <id>` | Target application ID (e.g., `mxm.config`, `my.app`). |
| `--mode <shipped\|seed\|empty>` | Installation mode. |
| `--pkg <package>` | Required for `--mode shipped`. |
| `--seed-root <path>` | Required for `--mode seed`. |
| `--dest-root <path>` | Destination root (default: `~/.config/mxm`). |
| `--overwrite` | Overwrite existing files if present. |
| `--no-sentinel` | Skip creation of the `.sentinel` file. |
| `--json` | Output JSON instead of human-readable summary. |
| `--version`, `--help` | Show version or help information. |

Both the CLI and Python API use the same underlying installer (`install_config`) and produce an `InstallReport` that lists all created, copied, or skipped files.

### Deprecation

`install_all(...)` is **deprecated**.  
It now delegates internally to `install_config(mode='shipped')` and will be removed in a future release.  
Existing code will continue to work but emit a `DeprecationWarning`.

## Loading Configs

```python
from mxm.config import load_config

cfg = load_config(package="demo", env="dev", profile="research")

print(cfg.parameters.refresh_interval)
print(cfg.paths.output)
```

- The loader reads from the app-owned config root (`~/.config/mxm/<package>/` by default).  
- Context (`mxm_env`, `mxm_profile`, `mxm_machine`) is injected automatically.  
- All `${...}` interpolations are resolved before returning.  
- The returned config is read-only by default.  

## Shipped Defaults

The repository’s canonical default configuration lives under:

```
src/mxm/config/_data/seeds/
```

These files are included in the wheel and used both for runtime defaults (`DefaultsMode.shipped`) and for tests (`DefaultsMode.seed`).  
They contain minimal but valid examples for all standard YAML layers:

- `default.yaml`
- `environment.yaml`
- `machine.yaml`
- `profile.yaml`
- `local.yaml`
- `templates/` (optional)

## Testing

Tests use `pytest` with `monkeypatch` to isolate config roots and hostnames.

Run with:

```bash
make test
# or
poetry run pytest -q
```

All tests run in a sandboxed temp directory and never touch the real `~/.config/mxm/`.

## Roadmap

- Config schema validation (`omegaconf.structured` / `pydantic`)  
- Environment variable overrides → auto-mapped into overrides dict  
- Integration with `mxm-runtime` for provenance tracking  
- Config hashing for reproducibility and auditability  

## License

MIT License. See [LICENSE](LICENSE).
