from __future__ import annotations

import re

# Allowed: lowercase letters, digits, dots, underscores, hyphens.
# No leading/trailing separators; no consecutive dots (optional).
_APP_ID_RE = re.compile(r"^(?!.*\.\.)[a-z0-9](?:[a-z0-9._-]*[a-z0-9])?$")


def is_valid_app_id(app_id: str) -> bool:
    return bool(_APP_ID_RE.match(app_id))


def validate_app_id(app_id: str) -> None:
    if not is_valid_app_id(app_id):
        raise ValueError(
            "Invalid app_id. Use lowercase letters, digits, dots, underscores, and hyphens; "
            "no leading/trailing separators, and avoid consecutive dots. "
            "Examples: 'mxm.config', 'mxm.datakraken', 'iic.profile'. "
            f"Got: {app_id!r}"
        )
