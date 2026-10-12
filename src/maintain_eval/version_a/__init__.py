"""Version A: static analysis tools only.

Each tool (SonarQube, dependency checker, coverage tool, ...) implements `Analyzer`
and returns one `Finding` per characteristic it can judge, with `source="tool:<name>"`.
"""

from pathlib import Path
from typing import Protocol, runtime_checkable

from maintain_eval.schemas import Characteristic, Finding, Verdict


@runtime_checkable
class Analyzer(Protocol):
    name: str

    def analyze(self, target: Path) -> list[Finding]:
        """Analyse the project at `target` and return findings."""
        ...


class NullAnalyzer:
    """Placeholder that answers UNKNOWN for every characteristic."""

    name = "null"

    def analyze(self, target: Path) -> list[Finding]:
        return [
            Finding(
                characteristic=c,
                verdict=Verdict.UNKNOWN,
                rationale="No analysis tools are integrated yet.",
                source=f"tool:{self.name}",
            )
            for c in Characteristic
        ]


__all__ = ["Analyzer", "NullAnalyzer"]
