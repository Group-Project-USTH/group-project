import asyncio
from pathlib import Path

import pytest

from maintainability_agent.agent.read_only_filesystem_backend import (
    READ_ONLY_ERROR,
    ReadOnlyFilesystemBackend,
)


@pytest.fixture
def project(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    root.mkdir()
    (root / "a.py").write_text("x = 1\n")
    return root


@pytest.fixture
def backend(project: Path) -> ReadOnlyFilesystemBackend:
    return ReadOnlyFilesystemBackend(root_dir=project, virtual_mode=True)


def test_reads_real_files(backend: ReadOnlyFilesystemBackend) -> None:
    result = backend.read("/a.py")
    assert result.error is None
    assert "x = 1" in str(result)


def test_write_edit_delete_upload_are_refused(
    backend: ReadOnlyFilesystemBackend, project: Path
) -> None:
    assert backend.write("/new.py", "y = 2").error == READ_ONLY_ERROR
    assert backend.edit("/a.py", "x = 1", "x = 2").error == READ_ONLY_ERROR
    assert backend.delete("/a.py").error == READ_ONLY_ERROR
    assert backend.upload_files([("/up.bin", b"z")])[0].error == "permission_denied"
    assert sorted(p.name for p in project.iterdir()) == ["a.py"]
    assert (project / "a.py").read_text() == "x = 1\n"


def test_async_variants_are_refused(backend: ReadOnlyFilesystemBackend, project: Path) -> None:
    async def attempt() -> None:
        assert (await backend.awrite("/new.py", "y")).error == READ_ONLY_ERROR
        assert (await backend.aedit("/a.py", "x = 1", "x = 2")).error == READ_ONLY_ERROR
        assert (await backend.adelete("/a.py")).error == READ_ONLY_ERROR

    asyncio.run(attempt())
    assert sorted(p.name for p in project.iterdir()) == ["a.py"]
    assert (project / "a.py").read_text() == "x = 1\n"


def test_paths_outside_root_are_rejected(backend: ReadOnlyFilesystemBackend) -> None:
    with pytest.raises(ValueError):
        backend.read("/../outside.txt")
