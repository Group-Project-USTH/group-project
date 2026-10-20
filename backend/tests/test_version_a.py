from pathlib import Path

from maintain_eval.schemas import Characteristic, Verdict
from maintain_eval.version_a import Analyzer, NullAnalyzer


def test_null_analyzer_satisfies_protocol_and_answers_unknown(tmp_path: Path) -> None:
    analyzer = NullAnalyzer()
    assert isinstance(analyzer, Analyzer)
    findings = analyzer.analyze(tmp_path)
    assert {f.characteristic for f in findings} == set(Characteristic)
    assert all(f.verdict is Verdict.UNKNOWN and f.source == "tool:null" for f in findings)
