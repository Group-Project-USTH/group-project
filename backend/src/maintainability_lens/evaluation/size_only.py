from pathlib import Path

from maintainability_lens.evaluation.scoped_measures import measure_file_in_project
from maintainability_lens.schemas import Characteristic, Evidence, Finding, MeasureName, Verdict

# Why: a file-size threshold alone matched the expert consensus with 0.91 accuracy on 304
# expert-rated Java files (Borg, Ezzouhri and Tornhill, ICSME 2024).
SIZE_ONLY_LIMIT_LINES_OF_CODE = 275
SIZE_ONLY_SOURCE = "Borg, Ezzouhri and Tornhill, ICSME 2024"


def decide_by_size(checkout: Path, file: str) -> list[Finding]:
    volumes = [
        measure
        for measure in measure_file_in_project(checkout, file).measures
        if measure.name is MeasureName.FILE_LINES_OF_CODE
    ]
    if not volumes:
        return [
            Finding(
                characteristic=characteristic,
                verdict=Verdict.UNKNOWN,
                rationale="The file could not be parsed.",
            )
            for characteristic in Characteristic
        ]
    volume = volumes[0]
    is_small = volume.value <= SIZE_ONLY_LIMIT_LINES_OF_CODE
    evidence = [Evidence(file=file, line_start=volume.line_start, line_end=volume.line_end)]
    rationale = (
        f"{volume.value} lines of code; the size-only limit is "
        f"{SIZE_ONLY_LIMIT_LINES_OF_CODE} ({SIZE_ONLY_SOURCE})."
    )
    return [
        Finding(
            characteristic=characteristic,
            verdict=Verdict.PASS if is_small else Verdict.FAIL,
            evidence=evidence,
            rationale=rationale,
        )
        for characteristic in Characteristic
    ]
