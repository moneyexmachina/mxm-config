# mxm-config

![Version](https://img.shields.io/github/v/release/moneyexmachina/mxm-config)
![License](https://img.shields.io/github/license/moneyexmachina/mxm-config)
![Python](https://img.shields.io/badge/python-3.13+-blue)
[![Checked with pyright](https://microsoft.github.io/pyright/img/pyright_badge.svg)](https://microsoft.github.io/pyright/)

## Purpose

`mxm-config` provides a unified way to **install, load, layer, and resolve configuration** across all Money Ex Machina (MXM) packages and applications.

It separates configuration from secrets and runtime metadata, enforces deterministic layering, and ensures every run has a transparent, reproducible view of its operating context.

## Installation

```bash
pip install mxm-config
```

## Usage

### Installing configuration

```python
from mxm.config import install_config, DefaultsMode

install_config(
    app_id="demo",
    mode=DefaultsMode.shipped,
    shipped_package="mxm.config._data.seeds",
)
```

### Loading configuration

```python
from mxm.config import load_config

cfg = load_config(package="demo", env="dev", profile="research")

print(cfg.parameters.refresh_interval)
print(cfg.paths.output)
```

### CLI usage

```bash
mxm-config install-config --app-id demo --mode shipped --pkg mxm.config
```

## Design Principles

- **Separation of concerns**  
  Configuration ≠ secrets ≠ runtime  
  Secrets are handled by `mxm-secrets`  
  Runtime metadata will be handled by `mxm-runtime` (planned)

- **Determinism**  
  Fixed layering order  
  Reproducible resolution

- **Transparency**  
  Plain YAML files  
  Explicit merge order

- **Extensibility**  
  Orthogonal layers  
  Package-level defaults

## The App-Owned Config Root

Every MXM application owns a configuration directory:

```
~/.config/mxm/<app_id>/
```

This is the single source of truth for runtime configuration.

Override with:

```bash
export MXM_CONFIG_HOME=/custom/path
```

## Configuration Layers

Configuration is resolved by merging the following layers (lowest → highest precedence):

1. `default.yaml`
2. `environment.yaml`
3. `machine.yaml`
4. `profile.yaml`
5. `local.yaml`
6. explicit overrides

## Installing Configs (Python API)

```python
from mxm.config import install_config, DefaultsMode
from importlib.resources import as_file, files

install_config(
    app_id="demo",
    mode=DefaultsMode.shipped,
    shipped_package="mxm.config._data.seeds",
)

with as_file(files("mxm.config._data") / "seeds") as p:
    install_config(app_id="demo", mode=DefaultsMode.seed, seed_root=p)

install_config(app_id="demo", mode=DefaultsMode.empty)
```

Returns an `InstallReport` describing all actions taken.

### Install Modes

| Mode | Description |
|------|-------------|
| `shipped` | Install packaged defaults |
| `seed` | Install from local filesystem |
| `empty` | Create empty config root |

## Command-Line Interface

```bash
mxm-config --help
```

Example:

```bash
mxm-config install-config \
  --app-id demo \
  --mode shipped \
  --pkg mxm.config
```

## Shipped Defaults

Default configuration files are located in:

```
src/mxm/config/_data/seeds/
```

These are bundled with the package and used for both runtime defaults and testing.

## Development

```bash
make check
```

This runs:

- Ruff (lint + import sorting)
- Black (format check)
- Isort (consistency check)
- Pyright (type checking)
- Pytest (tests)

## Testing

```bash
make test
```

Tests run in isolated temporary directories and never touch real user configuration.

## Roadmap

- Schema validation (`omegaconf.structured`, `pydantic`)
- Environment variable overrides
- Integration with `mxm-runtime`
- Configuration hashing and provenance tracking

## License

MIT License. See [LICENSE](LICENSE).
