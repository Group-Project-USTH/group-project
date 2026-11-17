import subprocess
from pathlib import Path

from maintainability_lens.evaluation import EvaluationFile


class Upstream:
    def __init__(self, repository: Path) -> None:
        self.repository = repository
        subprocess.run(["git", "init", "-q", str(repository)], check=True)

    def commit(self, relative_path: str, source: str) -> str:
        path = self.repository / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source)
        git = ["git", "-C", str(self.repository), "-c", "user.name=test"]
        git += ["-c", "user.email=test@example.com"]
        subprocess.run([*git, "add", "."], check=True)
        subprocess.run([*git, "commit", "-q", "-m", relative_path], check=True)
        head = subprocess.run(
            [*git, "rev-parse", "HEAD"], check=True, capture_output=True, text=True
        )
        return head.stdout.strip()

    def describe(self, commit: str, path: str, file_id: str = "F01") -> EvaluationFile:
        uri = self.repository.as_uri()
        return EvaluationFile(
            file_id=file_id,
            project="upstream",
            licence="MIT",
            repository_url=uri,
            commit=commit,
            path=path,
            url=f"{uri}/blob/{commit}/{path}",
        )
