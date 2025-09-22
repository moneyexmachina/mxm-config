# mxm-config

![Version](https://img.shields.io/github/v/release/moneyexmachina/mxm-config)
![License](https://img.shields.io/github/license/moneyexmachina/mxm-config)
![Python](https://img.shields.io/badge/python-3.12+-blue)
[![Checked with pyright](https://microsoft.github.io/pyright/img/pyright_badge.svg)](https://microsoft.github.io/pyright/)

## Purpose

`mxm-config` provides a unified way to **install, load, layer, and resolve configuration** across all Money Ex Machina (MXM) packages and applications.  
It separates configuration from secrets and runtime metadata, enforces deterministic layering, and ensures every run has a transparent, reproducible view of its operating context.

---

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

---

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

---

## Installing Configs

Use the installer to copy package-shipped configs into the user’s config root (`~/.config/mxm/` by default, override with `$MXM_CONFIG_HOME`).

```python
from mxm_config.installer import install_all

install_all("mxm_config.examples.demo_config", target_name="demo")
```

This creates:

```
~/.config/mxm/demo/default.yaml
~/.config/mxm/demo/environment.yaml
~/.config/mxm/demo/machine.yaml
~/.config/mxm/demo/profile.yaml
~/.config/mxm/demo/local.yaml
```

Any `templates/*.yaml` files shipped with the package will also be installed under `~/.config/mxm/<package>/templates/`.

---

## Loading Configs

```python
from mxm_config.loader import load_config

cfg = load_config("demo", env="dev", profile="research")

print(cfg.parameters.refresh_interval)
print(cfg.paths.output)
```

- Context (`mxm_env`, `mxm_profile`, `mxm_machine`) is injected automatically.  
- All `${...}` interpolations are resolved before returning.  
- The returned config is read-only by default.

---

## Example Package

The repo ships a minimal demo package: `mxm_config/examples/demo_config`

- `default.yaml` → valid baseline  
- `environment.yaml` → defines `dev` and `prod`  
- `machine.yaml` → overrides per host (`bridge`, `wildling`, `monolith`)  
- `profile.yaml` → defines `research`, `trading`  
- `local.yaml` → local overrides (optional, not versioned)

This serves as a test fixture for installers and loaders.

---

## Testing

Tests use `pytest` with `monkeypatch` to isolate config roots and hostnames.

Run with:

```bash
poetry run pytest
```

---

## Roadmap

- Config schema validation (via `omegaconf.structured` or pydantic)  
- CLI tool (`mxm-config install demo`)  
- Environment variable overrides → auto-mapped into overrides dict  
- Integration with `mxm-runtime` for provenance tracking  
- Config hashing for reproducibility and auditability  

---

## License

MIT License. See [LICENSE](LICENSE).
