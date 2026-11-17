import json
import subprocess
from pathlib import Path

import pytest
from upstream_repository import Upstream

from maintainability_lens.evaluation import check_out, load_evaluation_set


def test_evaluation_set_is_loaded_in_file_order(tmp_path: Path) -> None:
    entries = [
        {
            "file_id": file_id,
            "project": "p",
            "licence": "MIT",
            "repository_url": "https://example.com/p",
            "commit": "a" * 40,
            "path": f"{file_id}.py",
            "url": "https://example.com",
        }
        for file_id in ("F01", "F02")
    ]
    evaluation_set_file = tmp_path / "evaluation_set.json"
    evaluation_set_file.write_text(json.dumps(entries))

    evaluation_set = load_evaluation_set(evaluation_set_file)

    assert [evaluation_file.path for evaluation_file in evaluation_set] == ["F01.py", "F02.py"]


def test_check_out_gets_the_pinned_commit_not_the_latest(
    tmp_path: Path, upstream: Upstream
) -> None:
    pinned = upstream.commit("app.py", "VERSION = 1\n")
    upstream.commit("app.py", "VERSION = 2\n")

    checkout = check_out(upstream.describe(pinned, "app.py"), tmp_path / "checkouts")

    assert (checkout / "app.py").read_text() == "VERSION = 1\n"


def test_check_out_reuses_an_existing_checkout(tmp_path: Path, upstream: Upstream) -> None:
    pinned = upstream.commit("app.py", "VERSION = 1\n")
    first = check_out(upstream.describe(pinned, "app.py"), tmp_path / "checkouts")
    (upstream.repository / ".git").rename(tmp_path / "moved-away")

    second = check_out(upstream.describe(pinned, "app.py"), tmp_path / "checkouts")

    assert second == first


def test_check_out_rejects_a_checkout_at_another_commit(tmp_path: Path, upstream: Upstream) -> None:
    pinned = upstream.commit("app.py", "VERSION = 1\n")
    checkout = check_out(upstream.describe(pinned, "app.py"), tmp_path / "checkouts")
    later = upstream.commit("app.py", "VERSION = 2\n")
    git = ["git", "-C", str(checkout)]
    subprocess.run(
        [*git, "fetch", "-q", "--depth", "1", upstream.repository.as_uri(), later], check=True
    )
    subprocess.run([*git, "checkout", "-q", "FETCH_HEAD"], check=True)

    with pytest.raises(RuntimeError, match="not at"):
        check_out(upstream.describe(pinned, "app.py"), tmp_path / "checkouts")
