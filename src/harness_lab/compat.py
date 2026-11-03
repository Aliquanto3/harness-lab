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
_migration_failed: set[tuple[str, str]] = set()


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
            FutureWarning,  # shown by default, unlike DeprecationWarning: meant for the user
            stacklevel=2,
        )
    return value


def migrate_data_dir(legacy: Path, new: Path) -> bool:
    """Copy `legacy` to `new` when `new` does not exist and `legacy` is a directory.

    Returns whether a copy happened. The copy goes to a sibling staging directory unique to
    this process first, then is renamed, so an interrupted copy never leaves a half-filled
    `new` and two concurrent launches never share a staging copy. `legacy` is never modified.
    A failed copy (locked file, full disk, a concurrent launch that renamed first) never
    blocks the start: it is warned once and the app goes on with `new`.
    """
    if new.exists() or not legacy.is_dir():
        return False
    key = (str(legacy), str(new))
    if key in _migration_failed:
        return False
    staging = new.with_name(f"{new.name}.migration-{os.getpid()}")
    try:
        if staging.exists():
            shutil.rmtree(staging)  # a previous attempt cut short: only our own staging copy
        new.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(legacy, staging, symlinks=True)
        os.replace(staging, new)
    except OSError as exc:
        _migration_failed.add(key)
        shutil.rmtree(staging, ignore_errors=True)
        if new.exists():  # a concurrent launch migrated first: nothing lost
            return False
        warnings.warn(
            f"Could not copy the former data directory {legacy} to {new} ({exc}); "
            f"starting with an empty {new}. {legacy} is left untouched: copy it by hand.",
            RuntimeWarning,
            stacklevel=2,
        )
        return False
    return True
