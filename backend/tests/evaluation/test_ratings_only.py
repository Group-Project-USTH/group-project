from pathlib import Path

from maintainability_lens.evaluation import decide_by_ratings
from maintainability_lens.schemas import Characteristic, Verdict


def branching_function(name: str, branch_count: int) -> str:
    branches = "".join(
        f"    if x == {index}:\n        return {index}\n" for index in range(branch_count)
    )
    return f"def {name}(x):\n{branches}    return x\n\n\n"


def simple_function(name: str) -> str:
    return f"def {name}(x):\n    y = x + 1\n    return y\n\n\n"


def verdicts_by_characteristic(checkout: Path, file: str) -> dict[Characteristic, Verdict]:
    return {
        finding.characteristic: finding.verdict
        for finding in decide_by_ratings(checkout, file).findings
    }


def test_simple_code_passes_every_characteristic(
    tmp_path: Path,
) -> None:
    (tmp_path / "app.py").write_text(simple_function("f") + simple_function("g"))

    verdicts = verdicts_by_characteristic(tmp_path, "app.py")

    assert verdicts == {
        Characteristic.MODULARITY: Verdict.PASS,
        Characteristic.REUSABILITY: Verdict.PASS,
        Characteristic.ANALYSABILITY: Verdict.PASS,
        Characteristic.MODIFIABILITY: Verdict.PASS,
        Characteristic.TESTABILITY: Verdict.PASS,
    }


def test_a_very_complex_unit_fails_testability(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text(branching_function("f", 51))

    assert (
        verdicts_by_characteristic(tmp_path, "app.py")[Characteristic.TESTABILITY] is Verdict.FAIL
    )


def test_a_neutral_rating_fails(tmp_path: Path) -> None:
    moderate = branching_function("moderate", 10)
    simple = "".join(simple_function(f"simple_{index}") for index in range(13))
    (tmp_path / "app.py").write_text(moderate + simple)

    findings = {
        finding.characteristic: finding
        for finding in decide_by_ratings(tmp_path, "app.py").findings
    }

    assert "rated o" in findings[Characteristic.TESTABILITY].rationale
    assert findings[Characteristic.TESTABILITY].verdict is Verdict.FAIL
