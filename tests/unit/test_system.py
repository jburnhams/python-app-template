import os

import pytest

from app import system


def test_folder_bytes_sums_nested_files_and_skips_ones_that_vanish(tmp_path, monkeypatch: pytest.MonkeyPatch):
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "x.bin").write_bytes(b"12345")
    (tmp_path / "y.bin").write_bytes(b"123")
    assert system.folder_bytes(str(tmp_path)) == 8
    real = os.path.getsize
    monkeypatch.setattr(
        os.path, "getsize", lambda p: (_ for _ in ()).throw(FileNotFoundError(p)) if p.endswith("y.bin") else real(p)
    )
    assert system.folder_bytes(str(tmp_path)) == 5
