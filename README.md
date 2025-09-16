# mxm-config

`mxm-config` is a layered configuration loader for the Money Ex Machina ecosystem.

It provides a reproducible, environment-aware, and compositional interface to application context:
- Who is running (identity / profile)
- Where they are running (machine)
- What environment they are in (dev, prod, test)
- Where resources live (data, cache, logs, code)
- How to behave (backend selection, policy flags)

It is built as a thin, policy-driven wrapper around [OmegaConf](https://omegaconf.readthedocs.io).

## Installation

This package is managed via [Poetry](https://python-poetry.org/):

```bash
poetry install
```

## Usage
```python
from mxm_config import load_config

cfg = load_config()

print(cfg.env.name)
print(cfg.paths.data_root)
```

## Project Structure

mxm-config/
├── mxm_config/
│   ├── loader.py          # main entry point: load_config()
│   ├── ...
├── pyproject.toml
├── README.md
└── LICENSE

## Status

Work in progress (v0.1). Schema, layering, and validation model evolving alongside mxm-core.
