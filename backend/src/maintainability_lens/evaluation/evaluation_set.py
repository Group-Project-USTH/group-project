import subprocess
from pathlib import Path

from pydantic import BaseModel, TypeAdapter

SHORT_COMMIT_LENGTH = 12


class EvaluationFile(BaseModel):
    file_id: str
    project: str
    licence: str
    repository_url: str
    commit: str
    path: str
    url: str


def load_evaluation_set(evaluation_set_file: Path) -> list[EvaluationFile]:
    return TypeAdapter(list[EvaluationFile]).validate_json(evaluation_set_file.read_bytes())


def run_git(checkout: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(checkout), *arguments], check=True, capture_output=True, text=True
    )
    return completed.stdout.strip()


def check_out(evaluation_file: EvaluationFile, checkouts: Path) -> Path:
    checkout = (
        checkouts / f"{evaluation_file.project}-{evaluation_file.commit[:SHORT_COMMIT_LENGTH]}"
    )
    if not checkout.exists():
        checkout.mkdir(parents=True)
        run_git(checkout, "init", "-q")
        run_git(
            checkout,
            "fetch",
            "-q",
            "--depth",
            "1",
            evaluation_file.repository_url,
            evaluation_file.commit,
        )
        run_git(checkout, "checkout", "-q", "FETCH_HEAD")
    head = run_git(checkout, "rev-parse", "HEAD")
    if head != evaluation_file.commit:
        raise RuntimeError(f"{checkout} is at {head}, not at {evaluation_file.commit}")
    return checkout
