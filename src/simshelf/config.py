from __future__ import annotations

import copy
import tomllib
from pathlib import Path

DEFAULT_CONFIG = {
    "source_include": ["**/*.py", "**/*.toml", "**/*.yaml", "**/*.yml", "**/*.json", "**/*.txt"],
    "source_exclude": ["outputs/**", ".env*", "**/.env*", "**/*secret*", "**/*credential*"],
    "output_dir": "outputs",
    "max_file_mb": 25,
    "max_run_mb": 200,
    "rules": [
        {"pattern": "**/*.tmp", "action": "ignore"},
        {"pattern": "cache/**", "action": "ignore"},
        {"pattern": "**/*.png", "action": "copy"},
        {"pattern": "**/*.jpg", "action": "copy"},
        {"pattern": "**/*.jpeg", "action": "copy"},
        {"pattern": "**/*.webp", "action": "copy"},
        {"pattern": "**/*.json", "action": "copy"},
        {"pattern": "**/*.csv", "action": "copy"},
        {"pattern": "**/*", "action": "reference"},
    ],
}


def validate_config(config: dict) -> dict:
    config = {**copy.deepcopy(DEFAULT_CONFIG), **config}
    for key in ("source_include", "source_exclude"):
        if not isinstance(config[key], list) or not all(isinstance(x, str) and x for x in config[key]):
            raise ValueError(f"{key} must be a list of filename patterns")
    if not isinstance(config["output_dir"], str) or Path(config["output_dir"]).is_absolute() or ".." in Path(config["output_dir"]).parts or config["output_dir"] in ("", "."):
        raise ValueError("output_dir must be a relative subfolder of the simulation")
    for key in ("max_file_mb", "max_run_mb"):
        if not isinstance(config[key], (int, float)) or not 0 < config[key] <= 100000:
            raise ValueError(f"{key} must be between 0 and 100000 MB")
    if not isinstance(config["rules"], list) or len(config["rules"]) > 100:
        raise ValueError("Use at most 100 capture rules")
    for rule in config["rules"]:
        if not isinstance(rule, dict) or not isinstance(rule.get("pattern"), str) or not rule["pattern"] or rule.get("action") not in ("copy", "reference", "ignore"):
            raise ValueError("Each capture rule needs a pattern and a copy, reference, or ignore action")
    return config


def read_project(root: Path) -> dict:
    file = root / "simshelf.toml"
    if not file.exists():
        return {}
    raw = tomllib.loads(file.read_text())
    result = dict(raw.get("simulation", {}))
    config = {**raw.get("source", {}), **raw.get("capture", {})}
    if "include" in config:
        config["source_include"] = config.pop("include")
    if "exclude" in config:
        config["source_exclude"] = config.pop("exclude")
    result["config"] = validate_config(config)
    return result
