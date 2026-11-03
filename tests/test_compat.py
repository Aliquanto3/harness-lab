"""2.0.0 (WaveStack became HarnessLab): former variables and data directory, `compat`."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import warnings
from pathlib import Path

import pytest

from harness_lab import compat, config


@pytest.fixture(autouse=True)
def _fresh_warnings(monkeypatch):
    monkeypatch.setattr(compat, "_warned", set())
    monkeypatch.setattr(compat, "_migration_failed", set())


def test_getenv_prefers_the_new_variable(monkeypatch) -> None:
    monkeypatch.setenv("HARNESS_LAB_FOO", "new")
    monkeypatch.setenv("WAVESTACK_FOO", "old")
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert compat.getenv("HARNESS_LAB_FOO") == "new"


def test_getenv_empty_new_variable_still_wins(monkeypatch) -> None:
    monkeypatch.setenv("HARNESS_LAB_FOO", "")
    monkeypatch.setenv("WAVESTACK_FOO", "old")
    assert compat.getenv("HARNESS_LAB_FOO") == ""


def test_getenv_falls_back_on_the_former_name_and_warns_once(monkeypatch) -> None:
    monkeypatch.delenv("HARNESS_LAB_FOO", raising=False)
    monkeypatch.setenv("WAVESTACK_FOO", "old")
    with pytest.warns(FutureWarning, match="WAVESTACK_FOO is deprecated, use HARNESS_LAB_FOO"):
        assert compat.getenv("HARNESS_LAB_FOO") == "old"
    with warnings.catch_warnings():
        warnings.simplefilter("error")  # a second read: no second warning
        assert compat.getenv("HARNESS_LAB_FOO") == "old"


def test_getenv_default_when_neither_is_set(monkeypatch) -> None:
    monkeypatch.delenv("HARNESS_LAB_FOO", raising=False)
    monkeypatch.delenv("WAVESTACK_FOO", raising=False)
    assert compat.getenv("HARNESS_LAB_FOO") is None
    assert compat.getenv("HARNESS_LAB_FOO", "d") == "d"


def test_getenv_refuses_a_name_without_the_prefix() -> None:
    with pytest.raises(ValueError, match="does not start with HARNESS_LAB_"):
        compat.getenv("FOO")


def test_data_dir_reads_the_former_override(monkeypatch, tmp_path) -> None:
    monkeypatch.delenv("HARNESS_LAB_DATA_DIR", raising=False)
    monkeypatch.setenv("WAVESTACK_DATA_DIR", str(tmp_path / "old-override"))
    with pytest.warns(FutureWarning, match="WAVESTACK_DATA_DIR"):
        assert config.data_dir() == tmp_path / "old-override"


def _legacy_tree(root):
    root.mkdir(parents=True)
    (root / "settings.json").write_text('{"language": "en"}', encoding="utf-8")
    (root / "models").mkdir()
    (root / "models" / "m.gguf").write_bytes(b"GGUF")


def test_migrate_copies_the_former_directory_and_keeps_it(tmp_path) -> None:
    legacy, new = tmp_path / "WaveStack", tmp_path / "HarnessLab"
    _legacy_tree(legacy)
    assert compat.migrate_data_dir(legacy, new) is True
    assert (new / "settings.json").read_text(encoding="utf-8") == '{"language": "en"}'
    assert (new / "models" / "m.gguf").read_bytes() == b"GGUF"
    assert (legacy / "settings.json").exists() and (legacy / "models" / "m.gguf").exists()
    assert sorted(p.name for p in tmp_path.iterdir()) == ["HarnessLab", "WaveStack"]


def test_migrate_twice_does_nothing(tmp_path) -> None:
    legacy, new = tmp_path / "WaveStack", tmp_path / "HarnessLab"
    _legacy_tree(legacy)
    assert compat.migrate_data_dir(legacy, new) is True
    (new / "settings.json").write_text('{"language": "de"}', encoding="utf-8")
    (legacy / "settings.json").write_text('{"language": "fr"}', encoding="utf-8")
    assert compat.migrate_data_dir(legacy, new) is False
    assert (new / "settings.json").read_text(encoding="utf-8") == '{"language": "de"}'


def test_migrate_without_a_former_directory_does_nothing(tmp_path) -> None:
    assert compat.migrate_data_dir(tmp_path / "absent", tmp_path / "new") is False
    assert not (tmp_path / "new").exists()


def test_migrate_replaces_a_staging_copy_cut_short(tmp_path) -> None:
    legacy, new = tmp_path / "WaveStack", tmp_path / "HarnessLab"
    _legacy_tree(legacy)
    stale = tmp_path / f"HarnessLab.migration-{os.getpid()}"
    stale.mkdir()
    (stale / "half.tmp").write_bytes(b"x")
    assert compat.migrate_data_dir(legacy, new) is True
    assert not (new / "half.tmp").exists() and (new / "settings.json").exists()


def _without_override(monkeypatch, tmp_path):
    for name in ("HARNESS_LAB_DATA_DIR", "WAVESTACK_DATA_DIR"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "local"))
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("USERPROFILE", str(tmp_path / "home"))
    if sys.platform == "win32":
        return tmp_path / "local" / "WaveStack", tmp_path / "local" / "HarnessLab"
    share = tmp_path / "home" / ".local" / "share"
    return share / "wavestack", share / "harness-lab"


def test_data_dir_migrates_the_former_default_at_first_launch(monkeypatch, tmp_path) -> None:
    legacy, new = _without_override(monkeypatch, tmp_path)
    _legacy_tree(legacy)
    assert config.data_dir() == new
    assert (new / "models" / "m.gguf").read_bytes() == b"GGUF"
    assert (legacy / "models" / "m.gguf").exists()
    (new / "settings.json").unlink()
    assert config.data_dir() == new  # already there: never copied again
    assert not (new / "settings.json").exists()


def test_data_dir_with_an_override_migrates_nothing(monkeypatch, tmp_path) -> None:
    legacy, new = _without_override(monkeypatch, tmp_path)
    _legacy_tree(legacy)
    monkeypatch.setenv("HARNESS_LAB_DATA_DIR", str(tmp_path / "chosen"))
    assert config.data_dir() == tmp_path / "chosen"
    assert not new.exists()


def test_the_former_variable_warning_is_visible_without_any_filter(tmp_path) -> None:
    env = {k: v for k, v in os.environ.items() if not k.startswith(("HARNESS_LAB_", "PYTHONWARN"))}
    env["WAVESTACK_FOO"] = "old"
    code = "from harness_lab import compat; print(compat.getenv('HARNESS_LAB_FOO'))"
    out = subprocess.run(
        [sys.executable, "-c", code], env=env, capture_output=True, text=True, check=True
    )
    assert out.stdout.strip() == "old"
    assert "WAVESTACK_FOO is deprecated, use HARNESS_LAB_FOO" in out.stderr


def test_a_failed_copy_never_blocks_the_start(monkeypatch, tmp_path) -> None:
    legacy, new = tmp_path / "WaveStack", tmp_path / "HarnessLab"
    _legacy_tree(legacy)

    def locked(src, dst, **kwargs):
        os.makedirs(dst)
        (Path(dst) / "partial").write_bytes(b"x")
        raise PermissionError(32, "file in use", str(src))

    monkeypatch.setattr(shutil, "copytree", locked)
    with pytest.warns(RuntimeWarning, match="Could not copy the former data directory"):
        assert compat.migrate_data_dir(legacy, new) is False
    assert not new.exists()
    assert sorted(p.name for p in tmp_path.iterdir()) == ["WaveStack"]  # staging cleaned
    assert (legacy / "models" / "m.gguf").read_bytes() == b"GGUF"  # former one untouched
    with warnings.catch_warnings():
        warnings.simplefilter("error")  # not retried nor warned again in this process
        assert compat.migrate_data_dir(legacy, new) is False


def test_data_dir_starts_even_when_the_copy_fails(monkeypatch, tmp_path) -> None:
    legacy, new = _without_override(monkeypatch, tmp_path)
    _legacy_tree(legacy)

    def full(*args, **kwargs):
        raise OSError(28, "No space left on device")

    monkeypatch.setattr(shutil, "copytree", full)
    with pytest.warns(RuntimeWarning, match="No space left"):
        assert config.data_dir() == new
    assert (legacy / "settings.json").exists()


def test_a_concurrent_launch_that_migrated_first_is_not_an_error(monkeypatch, tmp_path) -> None:
    legacy, new = tmp_path / "WaveStack", tmp_path / "HarnessLab"
    _legacy_tree(legacy)
    real_replace = os.replace

    def other_process_first(src, dst):
        shutil.copytree(legacy, dst)  # the other launch renamed its own staging copy first
        real_replace(src, dst)

    monkeypatch.setattr(compat.os, "replace", other_process_first)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert compat.migrate_data_dir(legacy, new) is False
    assert (new / "settings.json").exists()
    assert sorted(p.name for p in tmp_path.iterdir()) == ["HarnessLab", "WaveStack"]
