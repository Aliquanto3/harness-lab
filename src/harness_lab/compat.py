"""Compatibility with the project's former name (2.0.0: WaveStack became HarnessLab).

The only place where the old names live on in the code:

- every `HARNESS_LAB_X` environment variable read through `getenv` falls back on the former
  `WAVESTACK_X`, with one deprecation warning per variable;
- the former data directory (`%LOCALAPPDATA%\\WaveStack`, `~/.local/share/wavestack`) is
  copied once to the new one at the first launch, when the new one does not exist yet. The
  former directory is never deleted, and a second copy does nothing.
"""

from __future__ import annotations

import os
import shutil
import warnings
from pathlib import Path

PREFIX = "HARNESS_LAB_"
LEGACY_PREFIX = "WAVESTACK_"
LEGACY_DIR_WINDOWS = "WaveStack"
LEGACY_DIR_POSIX = "wavestack"

_warned: set[str] = set()


def getenv(name: str, default: str | None = None) -> str | None:
    """`os.environ[name]`, else its former `WAVESTACK_` twin (warned once), else `default`.

    `name` must start with `HARNESS_LAB_`. An empty new variable counts as set: it wins.
    """
    if not name.startswith(PREFIX):
        raise ValueError(f"{name} does not start with {PREFIX}")
    value = os.environ.get(name)
    if value is not None:
        return value
    legacy = LEGACY_PREFIX + name.removeprefix(PREFIX)
    value = os.environ.get(legacy)
    if value is None:
        return default
    if legacy not in _warned:
        _warned.add(legacy)
        warnings.warn(
            f"{legacy} is deprecated, use {name} (read as a fallback for now).",
            DeprecationWarning,
            stacklevel=2,
        )
    return value


def migrate_data_dir(legacy: Path, new: Path) -> bool:
    """Copy `legacy` to `new` when `new` does not exist and `legacy` is a directory.

    Returns whether a copy happened. The copy goes to a sibling first, then is renamed, so an
    interrupted copy never leaves a half-filled `new`. `legacy` is never modified.
    """
    if new.exists() or not legacy.is_dir():
        return False
    staging = new.with_name(new.name + ".migration")
    if staging.exists():
        shutil.rmtree(staging)  # a previous attempt cut short: only our own staging copy
    new.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(legacy, staging, symlinks=True)
    os.replace(staging, new)
    return True
