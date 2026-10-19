from __future__ import annotations

import copy
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
        {"pattern": "**/*.log", "action": "copy"},
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
    from .swss import read, reject_legacy
    reject_legacy(root)
    if not (root / "swss.toml").exists() and not (root / "swss.toml").is_symlink():
        return {}
    try:
        document = read(root)
    except (ValueError, OSError, UnicodeError, TypeError, RecursionError):
        # Registration selects source, not a declaration capability. Leave the
        # invalid companion untouched; discovery diagnoses it and manual launch
        # remains available using the visibly saved/default capture settings.
        return {}
    return extension_project(document)


def extension_project(document):
    """Optional local extension; portable fields cannot be duplicated here."""
    extension = document['raw'].get('extensions', {}).get('simshelf')
    if extension is None:
        return {}
    if not isinstance(extension, dict) or extension.get('schema_version') != 1 or type(extension.get('schema_version')) is not int:
        raise ValueError('Unsupported extensions.simshelf schema; supported version is 1')
    if set(extension) - {'schema_version', 'name', 'description', 'source', 'capture'}:
        raise ValueError('Unknown/conflicting extensions.simshelf fields')
    for key in ('name', 'description'):
        if key in extension and not isinstance(extension[key], str):
            raise ValueError('Extension name/description must be strings')
    source, capture = extension.get('source', {}), extension.get('capture', {})
    if not isinstance(source, dict) or set(source) - {'include', 'exclude'} or not isinstance(capture, dict) or set(capture) - {'output_dir', 'max_file_mb', 'max_run_mb', 'rules'}:
        raise ValueError('Unsupported SimShelf source/capture fields')
    config = dict(capture)
    for key in ('include', 'exclude'):
        if key in source:
            config['source_' + key] = source[key]
    return {**{k: extension[k] for k in ('name', 'description') if k in extension}, 'config': validate_config(config)}
