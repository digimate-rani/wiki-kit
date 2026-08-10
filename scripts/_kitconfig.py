"""
Shared helper: locate the project root and read wiki-kit.json.

Every wiki-kit script lives at <project>/scripts/wiki/<script>.py, so the
project root is two levels up. If wiki-kit.json is missing (someone copied a
single script by hand), sane defaults are used instead of crashing.
"""

import json
from pathlib import Path

DEFAULTS = {
    "wiki_root": "wiki",
    "scripts_dir": "scripts/wiki",
    "categories": [],
}


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def config() -> dict:
    root = project_root()
    cfg = dict(DEFAULTS)
    cfg_path = root / "wiki-kit.json"
    if cfg_path.is_file():
        try:
            cfg.update(json.loads(cfg_path.read_text(encoding="utf-8")))
        except (ValueError, OSError):
            pass
    return cfg


def wiki_dir() -> Path:
    return project_root() / config()["wiki_root"]


def sources_dir(kind: str) -> Path:
    """kind: web | pdf | local"""
    return wiki_dir() / "sources" / kind
