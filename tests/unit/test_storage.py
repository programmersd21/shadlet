from __future__ import annotations

import io
from pathlib import Path

import pytest
import shadlet as ui
from shadlet.storage import LocalStorage, StorageError, sanitise_filename


def test_local_storage_round_trip_and_overwrite(tmp_path: Path):
    storage = LocalStorage(tmp_path / "uploads")
    stored = storage.write("reports/2026.csv", b"a,b\n1,2\n")
    assert stored.key == "reports/2026.csv"
    assert stored.size == 8
    assert storage.exists("reports/2026.csv")
    assert storage.read("reports/2026.csv") == b"a,b\n1,2\n"

    with pytest.raises(FileExistsError):
        storage.write("reports/2026.csv", b"new")
    storage.write("reports/2026.csv", b"new", overwrite=True)
    assert storage.read("reports/2026.csv") == b"new"

    storage.delete("reports/2026.csv")
    assert not storage.exists("reports/2026.csv")
    storage.delete("reports/2026.csv")


def test_local_storage_streams_with_a_limit(tmp_path: Path):
    storage = LocalStorage(tmp_path, max_bytes=4)
    assert storage.write_stream("small.bin", io.BytesIO(b"1234")).size == 4
    with pytest.raises(StorageError, match="limit"):
        storage.write_stream("large.bin", io.BytesIO(b"12345"))
    assert not storage.exists("large.bin")


@pytest.mark.parametrize(
    "key",
    [
        "",
        "/absolute",
        "../escape",
        "a/../b",
        "a//b",
        "a\\b",
        "C:/x",
        "a:b",
        "file.txt:stream",
        "trailing.",
        "trailing ",
        "nul\x00",
    ],
)
def test_local_storage_rejects_unsafe_keys(tmp_path: Path, key: str):
    storage = LocalStorage(tmp_path)
    with pytest.raises(StorageError):
        storage.write(key, b"x")
    assert list(tmp_path.rglob("*")) == []


def test_sanitise_filename_strips_paths_and_reserved_names():
    assert sanitise_filename("../../etc/passwd") == "passwd"
    assert sanitise_filename(r"C:\temp\report.csv") == "report.csv"
    assert sanitise_filename("..") == "upload"
    assert sanitise_filename("") == "upload"
    assert sanitise_filename("CON.txt") == "_CON.txt"
    assert sanitise_filename('bad<>:"|?*.txt') == "bad-------.txt"
    assert len(sanitise_filename("x" * 500)) == 255


def test_uploaded_file_saves_through_storage(tmp_path: Path):
    storage = LocalStorage(tmp_path)
    upload = ui.UploadedFile(
        filename="../../danger.txt",
        content_type="text/plain",
        data=b"safe",
    )
    assert upload.safe_filename == "danger.txt"
    stored = upload.save_to(storage)
    assert stored.key == "danger.txt"
    assert storage.read("danger.txt") == b"safe"

    explicit = upload.save_to(storage, key="nested/renamed.txt")
    assert explicit.key == "nested/renamed.txt"
    assert storage.read(explicit.key) == b"safe"
