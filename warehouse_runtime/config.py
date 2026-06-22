from __future__ import annotations

from pathlib import Path
from typing import Any


def load_yaml(path: str | Path) -> dict[str, Any]:
    """Load a YAML config file.

    PyYAML is intentionally the only non-stdlib dependency used by the runtime.
    The hackathon starter venv may need `pip install -r requirements.txt` after
    this runtime stage because the original requirements did not include it.
    """
    try:
        import yaml  # type: ignore
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "PyYAML is required for runtime configs. Install with `pip install PyYAML` "
            "or run `pip install -r requirements.txt` from Robothon-starter."
        ) from exc

    with Path(path).open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping at top level of {path}")
    return data
