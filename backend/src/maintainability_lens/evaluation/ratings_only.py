from pathlib import Path

from maintainability_lens.evaluation.recorded_findings import FileFindings
from maintainability_lens.evaluation.scoped_measures import measure_file_in_project
from maintainability_lens.ratings import rate_project
from maintainability_lens.schemas import (
    CharacteristicRating,
    Evidence,
    Finding,
    MeasureName,
    Rating,
    Verdict,
)

# Why: `+` is the 4-star level of SIG's 5/30/30/30/5 split (ADR 0001, decision 8); `o` is
# the benchmark average, not good maintainability.
PASSING_RATINGS = frozenset({Rating.PLUS_PLUS, Rating.PLUS})


def describe_rating(characteristic_rating: CharacteristicRating) -> str:
    rated_from = ", ".join(characteristic_rating.rated_from)
    partial = f", partial: from {rated_from} only" if characteristic_rating.is_partial else ""
    return (
        f"{characteristic_rating.characteristic} is rated {characteristic_rating.rating}"
        f"{partial}; pass needs + or better."
    )


def decide_from_rating(
    characteristic_rating: CharacteristicRating, evidence: list[Evidence]
) -> Finding:
    if characteristic_rating.rating is None:
        return Finding(
            characteristic=characteristic_rating.characteristic,
            verdict=Verdict.UNKNOWN,
            rationale=f"No System property of {characteristic_rating.characteristic} is rated.",
        )
    is_passing = characteristic_rating.rating in PASSING_RATINGS
    return Finding(
        characteristic=characteristic_rating.characteristic,
        verdict=Verdict.PASS if is_passing else Verdict.FAIL,
        evidence=evidence,
        rationale=describe_rating(characteristic_rating),
    )


def decide_by_ratings(checkout: Path, file: str) -> FileFindings:
    file_measures = measure_file_in_project(checkout, file)
    evidence = [
        Evidence(file=file, line_start=measure.line_start, line_end=measure.line_end)
        for measure in file_measures.measures
        if measure.name is MeasureName.FILE_LINES_OF_CODE
    ]
    ratings = rate_project(file_measures)
    return FileFindings(
        findings=[
            decide_from_rating(characteristic_rating, evidence)
            for characteristic_rating in ratings.characteristic_ratings
        ]
    )
