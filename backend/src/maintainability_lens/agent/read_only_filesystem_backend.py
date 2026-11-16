"""A `FilesystemBackend` that refuses every mutating operation."""

from deepagents.backends import FilesystemBackend
from deepagents.backends.protocol import (
    DeleteResult,
    EditResult,
    FileUploadResponse,
    WriteResult,
)

READ_ONLY_ERROR = "permission denied: the target directory is read-only"


class ReadOnlyFilesystemBackend(FilesystemBackend):
    """Reads real files under `root_dir`; write/edit/delete/upload always fail.

    The async variants inherited from `BackendProtocol` delegate to these methods.
    This guards against writes, not reads: anything under `root_dir` can be read.
    """

    def write(self, file_path: str, content: str) -> WriteResult:
        return WriteResult(error=READ_ONLY_ERROR)

    def edit(
        self,
        file_path: str,
        old_string: str,
        new_string: str,
        replace_all: bool = False,
    ) -> EditResult:
        return EditResult(error=READ_ONLY_ERROR)

    def delete(self, file_path: str) -> DeleteResult:
        return DeleteResult(error=READ_ONLY_ERROR)

    def upload_files(self, files: list[tuple[str, bytes]]) -> list[FileUploadResponse]:
        return [FileUploadResponse(path=path, error="permission_denied") for path, _ in files]
