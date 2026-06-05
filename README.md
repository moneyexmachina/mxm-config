# mxm-config

![Version](https://img.shields.io/github/v/release/moneyexmachina/mxm-config)
![License](https://img.shields.io/github/license/moneyexmachina/mxm-config)
![Python](https://img.shields.io/badge/python-3.13+-blue)
[![Checked with pyright](https://microsoft.github.io/pyright/img/pyright_badge.svg)](https://microsoft.github.io/pyright/)

## Purpose

`mxm-config` provides deterministic configuration resolution for Money Ex Machina (MXM) applications.

It resolves configuration from an external configuration store using a `RuntimeIdentity`, applies a fixed layering model, and returns a transparent and reproducible configuration view for the running application.

`mxm-config` is responsible for configuration resolution only.

It does not manage secrets, discover runtime identity, or own configuration storage.

## Installation

```bash
pip install mxm-config
```

## Usage

### Loading configuration

```python
from pathlib import Path

from mxm.config import load_config
from mxm.types import RuntimeIdentity

identity = RuntimeIdentity(
    app="mxm-moneymachine",
    environment="dev",
    machine="bridge",
    substrate="local-process",
    role="marketdata",
)

cfg = load_config(
    identity=identity,
    store_root=Path("~/mxm-config-store").expanduser(),
)

print(cfg.parameters.refresh_interval)
print(cfg.paths.output)
```

### Using the default config store

```python
from mxm.config import load_config

cfg = load_config(identity=identity)
```

By default, `mxm-config` resolves configuration from:

```text
~/mxm-config-store
```

## Design Principles

### Separation of Concerns

Configuration, secrets, and runtime identity are separate concerns.

```text
mxm-runtime
    discovers RuntimeIdentity

mxm-config
    resolves configuration

mxm-secrets
    resolves secrets
```

### Determinism

Configuration resolution follows a fixed precedence order.

The same `RuntimeIdentity` and configuration store will always produce the same resolved configuration.

### Transparency

Configuration is stored as plain YAML files.

Layer selection and merge order are explicit and inspectable.

### Composability

Each configuration layer expresses a single concern.

Applications compose behavior through layering rather than duplication.

## Configuration Store

`mxm-config` resolves configuration from an external configuration store.

The configuration store is the authoritative source of configuration data.

A typical store layout is:

```text
mxm-config-store/
└── apps/
    └── <app_id>/
        ├── default.yaml
        ├── environment.yaml
        ├── machine.yaml
        ├── substrate.yaml
        └── role.yaml
```

The configuration store contains configuration data only.

Configuration resolution semantics belong to `mxm-config`.

## Runtime Identity

Configuration selection is driven by a `RuntimeIdentity`.

```text
RuntimeIdentity
├── app
├── environment
├── machine
├── substrate
└── role
```

Each identity dimension selects a configuration layer from the store.

## Configuration Layers

Configuration is resolved by merging the following layers (lowest → highest precedence):

1. `default.yaml`
2. `environment.yaml`
3. `machine.yaml`
4. `substrate.yaml`
5. `role.yaml`
6. explicit overrides

For a runtime identity:

```text
app         = mxm-moneymachine
environment = dev
machine     = bridge
substrate   = local-process
role        = marketdata
```

the resolver selects:

```text
default.yaml
environment.yaml["dev"]
machine.yaml["bridge"]
substrate.yaml["local-process"]
role.yaml["marketdata"]
```

and merges them in order.

## Python API

### Loading configuration

```python
cfg = load_config(
    identity=identity,
    store_root=Path("~/mxm-config-store"),
)
```

### Explicit overrides

```python
cfg = load_config(
    identity=identity,
    overrides={
        "parameters.refresh_interval": 60,
    },
)
```

## Command-Line Interface

```bash
mxm-config --help
```

Example:

```bash
mxm-config show-config \
  --app mxm-moneymachine \
  --environment dev \
  --machine bridge \
  --substrate local-process \
  --role marketdata
```

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

Tests run in isolated temporary directories and use temporary configuration stores.

## Roadmap

- Schema validation
- Configuration provenance reporting
- Configuration hashing
- Layer introspection and diagnostics
- RuntimeContext integration

## License

MIT License. See [LICENSE](LICENSE).

