"""Load YAML configuration files from the config/ directory."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = ROOT / "config"


@lru_cache(maxsize=None)
def load_yaml(name: str) -> dict[str, Any]:
    with open(CONFIG_DIR / name, encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def app_config() -> dict[str, Any]:
    return load_yaml("app.yaml")


def skill_names() -> list[str]:
    return list(load_yaml("skills.yaml").get("skills", {}).keys())


def skill_areas() -> list[str]:
    return list(load_yaml("skills.yaml").get("areas", []))


def scoring() -> dict[str, float]:
    return dict(load_yaml("skills.yaml")["scoring"])


def roles() -> list[dict[str, Any]]:
    return list(load_yaml("roles.yaml")["roles"])


def role_names() -> list[str]:
    return [r["name"] for r in roles()]
