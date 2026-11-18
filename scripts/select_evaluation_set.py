import json
import random
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from maintainability_lens.measures import measure_project
from maintainability_lens.schemas import MeasureName


@dataclass(frozen=True)
class SourceProject:
    name: str
    repository_url: str
    commit: str
    licence: str


SOURCE_PROJECTS = [
    SourceProject(
        "beets",
        "https://github.com/beetbox/beets",
        "d3631b205a1bc47f62639b95b2cfcb0c124ec909",
        "MIT",
    ),
    SourceProject(
        "httpx",
        "https://github.com/encode/httpx",
        "7cff5f79bc78649bbcd3fd9aa7a74c86e0f63016",
        "BSD-3-Clause",
    ),
    SourceProject(
        "requests",
        "https://github.com/psf/requests",
        "3c7baaa05ab4aa49cc819ce3a819d260de19c157",
        "Apache-2.0",
    ),
    SourceProject(
        "rich",
        "https://github.com/Textualize/rich",
        "3a109ccdffe5b2d0e30684a304fbd388e99ce57b",
        "MIT",
    ),
    SourceProject(
        "tqdm",
        "https://github.com/tqdm/tqdm",
        "9cf5a12b1f955468a17f0ba3c59092b23e4258ac",
        "MPL-2.0 and MIT",
    ),
    SourceProject(
        "youtube-dl",
        "https://github.com/ytdl-org/youtube-dl",
        "bc069d2bb40bcbc5bdfdf352ca15bf586c7792cb",
        "Unlicense",
    ),
]

RANDOM_SEED = 20261117
FILES_PER_SIZE_BAND = 10
MAXIMUM_FILES_PER_PROJECT = 6
MINIMUM_UNITS_PER_FILE = 2
# Why: a rater needs about 10-15 minutes per file (Borg et al. 2024); larger files would
# not fit that budget, smaller ones give too little to judge.
SIZE_BANDS = [(30, 149), (150, 349), (350, 600)]
# Why: SIG 2007 cyclomatic complexity risk bands (Heitlager, Kuipers and Visser, QUATIC 2007).
COMPLEXITY_BANDS = [(1, 10), (11, 20), (21, None)]


@dataclass(frozen=True)
class CandidateFile:
    project: SourceProject
    path: str
    lines_of_code: int
    worst_cyclomatic_complexity: int


def check_out(project: SourceProject, corpus_directory: Path) -> Path:
    checkout = corpus_directory / project.name
    if not checkout.exists():
        subprocess.run(["git", "init", "-q", str(checkout)], check=True)
        subprocess.run(
            [
                "git",
                "-C",
                str(checkout),
                "fetch",
                "-q",
                "--depth",
                "1",
                project.repository_url,
                project.commit,
            ],
            check=True,
        )
        subprocess.run(["git", "-C", str(checkout), "checkout", "-q", "FETCH_HEAD"], check=True)
    head = subprocess.run(
        ["git", "-C", str(checkout), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    if head.stdout.strip() != project.commit:
        raise SystemExit(f"{checkout} is not at {project.commit}")
    return checkout


def find_candidate_files(project: SourceProject, checkout: Path) -> list[CandidateFile]:
    lines_of_code: dict[str, int] = {}
    complexities: dict[str, list[int]] = {}
    for measure in measure_project(checkout).measures:
        if measure.is_test_code:
            continue
        if measure.name == MeasureName.FILE_LINES_OF_CODE:
            lines_of_code[measure.file] = measure.value
        if measure.name == MeasureName.CYCLOMATIC_COMPLEXITY:
            complexities.setdefault(measure.file, []).append(measure.value)
    return [
        CandidateFile(project, path, lines_of_code[path], max(complexities[path]))
        for path in sorted(lines_of_code)
        if len(complexities.get(path, [])) >= MINIMUM_UNITS_PER_FILE
    ]


def is_in_band(value: int, band: tuple[int, int | None]) -> bool:
    lowest, highest = band
    return value >= lowest and (highest is None or value <= highest)


def pick_from_cell(
    cell: list[CandidateFile], count: int, picks_per_project: Counter[str], generator: random.Random
) -> list[CandidateFile]:
    pool = generator.sample(cell, len(cell))
    picked: list[CandidateFile] = []
    while len(picked) < count:
        open_pool = [
            candidate
            for candidate in pool
            if picks_per_project[candidate.project.name] < MAXIMUM_FILES_PER_PROJECT
        ]
        if not open_pool:
            break
        choice = min(open_pool, key=lambda candidate: picks_per_project[candidate.project.name])
        pool.remove(choice)
        picked.append(choice)
        picks_per_project[choice.project.name] += 1
    return picked


def split_evenly(total: int, parts: int) -> list[int]:
    return [total // parts + (1 if index < total % parts else 0) for index in range(parts)]


def select_evaluation_set(candidates: list[CandidateFile]) -> list[CandidateFile]:
    generator = random.Random(RANDOM_SEED)
    picks_per_project: Counter[str] = Counter()
    selected: list[CandidateFile] = []
    for size_band in SIZE_BANDS:
        in_size_band = [
            candidate for candidate in candidates if is_in_band(candidate.lines_of_code, size_band)
        ]
        cells = [
            [
                candidate
                for candidate in in_size_band
                if is_in_band(candidate.worst_cyclomatic_complexity, band)
            ]
            for band in COMPLEXITY_BANDS
        ]
        cells_by_scarcity = sorted(range(len(cells)), key=lambda index: len(cells[index]))
        remaining = FILES_PER_SIZE_BAND
        for position, index in enumerate(cells_by_scarcity):
            share = split_evenly(remaining, len(cells) - position)[0]
            picked = pick_from_cell(cells[index], share, picks_per_project, generator)
            selected.extend(picked)
            remaining -= len(picked)
    return generator.sample(selected, len(selected))


def describe(position: int, candidate: CandidateFile) -> dict[str, str]:
    project = candidate.project
    return {
        "file_id": f"F{position:02d}",
        "project": project.name,
        "licence": project.licence,
        "repository_url": project.repository_url,
        "commit": project.commit,
        "path": candidate.path,
        "url": f"{project.repository_url}/blob/{project.commit}/{candidate.path}",
    }


def main() -> None:
    corpus_directory, output_file = Path(sys.argv[1]), Path(sys.argv[2])
    corpus_directory.mkdir(parents=True, exist_ok=True)
    candidates = [
        candidate
        for project in SOURCE_PROJECTS
        for candidate in find_candidate_files(project, check_out(project, corpus_directory))
    ]
    selected = select_evaluation_set(candidates)
    evaluation_set = [
        describe(position, candidate) for position, candidate in enumerate(selected, start=1)
    ]
    output_file.write_text(json.dumps(evaluation_set, indent=2) + "\n")
    files_per_project = Counter(candidate.project.name for candidate in selected)
    print(f"{len(evaluation_set)} of {len(candidates)} candidate files: {dict(files_per_project)}")


if __name__ == "__main__":
    main()
