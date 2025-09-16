# mxm-config

## Purpose

`mxm-config` provides a unified way to **load, layer, and resolve configuration** across all Money Ex Machina (MXM) packages and applications.  
It separates configuration from secrets and runtime metadata, enforces deterministic layering, and ensures that every run has a transparent, reproducible view of its operating context.

---

## Design Principles

- **Separation of concerns**  
  - Configuration ≠ secrets ≠ runtime.  
  - Secrets are handled by [`mxm-secrets`](https://github.com/moneyexmachina/mxm-secrets).  
  - Runtime metadata is handled by `mxm-runtime` (planned).  

- **Determinism**  
  - Configuration is layered in a fixed, documented order.  
  - Reproducible runs: the same context produces the same resolved config.  

- **Transparency**  
  - Configs are plain YAML files, no hidden state.  
  - Merging behavior is explicit and traceable.  

- **Extensibility**  
  - Layers are minimal and orthogonal.  
  - New packages can register defaults without breaking existing ones.  

---

## Configuration Layers

At runtime, configuration is resolved by merging up to five layers in order of precedence:

1. **`default.yaml`**  
   Baseline shipped with the package. Minimal but valid.  
   *Always present.*

2. **`environment.yaml`**  
   Deployment mode (`dev`, `staging`, `prod`).  
   Captures broad operational context.

3. **`machine.yaml`**  
   Host-specific overrides (paths, mounts, resources).  
   Example: different data root for laptop vs server.

4. **`profile.yaml`**  
   Role or user context (`research`, `production`, `public`).  
   Determines scope and feature availability.

5. **`overrides.yaml`**  
   Local scratchpad for ad-hoc tweaks.  
   *Not intended for version control.*

⚠️ Only **one file per layer** is active in `~/.config/mxm/<package>/`.  
If you want multiple variants (e.g. `dev.yaml` and `prod.yaml`), keep them under `templates/` and copy the one you need into place.

---

## Installation of Configs

`mxm-config` provides an installer that copies package-provided configs into the user’s config root (`~/.config/mxm/` by default, override with `$MXM_CONFIG_HOME`).

- **Defaults**  
  ```python
  from mxm_config.installer import install_default
  install_default("mxm_config.examples.demo_config")
  ```
  Installs:  
  ```
  ~/.config/mxm/demo_config/default.yaml
  ```

- **Templates**  
  ```python
  from mxm_config.installer import install_templates
  install_templates("mxm_config.examples.demo_config")
  ```
  Installs:  
  ```
  ~/.config/mxm/demo_config/templates/*.yaml
  ```

---

## Usage in Code

```python
from mxm_config.loader import load_config

cfg = load_config("demo_config")
print(cfg.parameters.refresh_interval)
```

By default, configs are read-only. Override behavior with `force` flags in the installer, or by editing `overrides.yaml`.

---

## Example Package (`demo_config`)

The repository ships a minimal demo package:

- `default.yaml` → valid baseline  
- `config_templates/environment.yaml` → dev/prod example  
- `config_templates/machine.yaml` → host paths/resources  
- `config_templates/profile.yaml` → role-specific example  
- `config_templates/overrides.yaml` → local tweaks  

This serves as a test case for installers and loaders.

---

## Testing

- Config root defaults to `~/.config/mxm/`.  
- Override with `$MXM_CONFIG_HOME` during tests.  
- Pytest suite included.  
  - Uses `monkeypatch` to redirect config root into a temp directory.  
  - Ensures functions respect layering and skip/overwrite semantics.

Run tests with:
```bash
poetry run pytest
```

---

## Roadmap

- Schema validation (e.g. `omegaconf.structured`)  
- CLI tool (`mxm-config install demo_config`)  
- Integration with `mxm-runtime` for provenance  
- Config hashing for reproducibility and auditability  

---

## License

MIT License. See [LICENSE](LICENSE).

