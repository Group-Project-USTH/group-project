from pathlib import Path

from maintainability_lens.evaluation import decide_by_size
from maintainability_lens.schemas import Characteristic, Verdict


def write_assignments(root: Path, relative_path: str, count: int) -> None:
    (root / relative_path).write_text(
        "".join(f"value_{index} = {index}\n" for index in range(count))
    )


def test_a_file_at_the_size_limit_passes_every_characteristic(tmp_path: Path) -> None:
    write_assignments(tmp_path, "small.py", 275)

    findings = decide_by_size(tmp_path, "small.py")

    assert [finding.characteristic for finding in findings] == list(Characteristic)
    assert {finding.verdict for finding in findings} == {Verdict.PASS}


def test_a_file_over_the_size_limit_fails_every_characteristic(tmp_path: Path) -> None:
    write_assignments(tmp_path, "large.py", 276)

    findings = decide_by_size(tmp_path, "large.py")

    assert {finding.verdict for finding in findings} == {Verdict.FAIL}


def test_size_only_cites_the_whole_file_and_its_lines_of_code(tmp_path: Path) -> None:
    write_assignments(tmp_path, "large.py", 276)

    finding = decide_by_size(tmp_path, "large.py")[0]

    assert [
        (evidence.file, evidence.line_start, evidence.line_end) for evidence in finding.evidence
    ] == [("large.py", 1, 276)]
    assert "276 lines of code" in finding.rationale


def test_an_unparsed_file_is_unknown_on_every_characteristic(tmp_path: Path) -> None:
    (tmp_path / "broken.py").write_text("def f(:\n")

    findings = decide_by_size(tmp_path, "broken.py")

    assert {finding.verdict for finding in findings} == {Verdict.UNKNOWN}
