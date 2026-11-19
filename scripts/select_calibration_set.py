import json
import re
import subprocess
import sys
import urllib.request
from collections import Counter
from collections.abc import Iterable, Iterator
from dataclasses import asdict, dataclass
from pathlib import Path

from maintainability_lens.measures import measure_project
from maintainability_lens.ratings import build_risk_profiles
from maintainability_lens.schemas import MeasureName, ProjectMeasures

REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
EVALUATION_SET_FILE = REPOSITORY_ROOT / "backend" / "evaluation" / "evaluation_set.json"
SNAPSHOT_URL = "https://hugovk.github.io/top-pypi-packages/top-pypi-packages.min.json"
# Why: Alves, Ypma and Visser (ICSM 2010) and Alves, Correia and Visser (IWSM-MENSURA 2011)
# calibrated on a benchmark of 100 systems.
SYSTEM_COUNT = 100
MINIMUM_PRODUCTION_LINES_OF_CODE = 1000
# Why: the two repositories above 1 GB among the top packages are SDK monorepos made mostly
# of generated code, which SIG leaves out of its benchmark.
MAXIMUM_REPOSITORY_SIZE_KILOBYTES = 1_000_000
GITHUB_REPOSITORY = re.compile(r"https?://github\.com/([\w.-]+)/([\w.-]+)")
SOURCE_URL_LABEL = re.compile(r"source|repo|code|github", re.IGNORECASE)


@dataclass(frozen=True)
class CalibrationSystem:
    project: str
    download_rank: int
    repository_url: str
    commit: str
    licence: str


@dataclass(frozen=True)
class GithubRepository:
    language: str | None
    is_archived: bool
    is_fork: bool
    size_kilobytes: int
    licence: str


def fetch_json(url: str) -> dict[str, object]:
    with urllib.request.urlopen(url, timeout=30) as response:
        return dict(json.load(response))


def find_repository_url(package: str) -> str | None:
    try:
        info = fetch_json(f"https://pypi.org/pypi/{package}/json")["info"]
    except OSError:
        return None
    assert isinstance(info, dict)
    labelled_urls = sorted(
        (info.get("project_urls") or {}).items(),
        key=lambda label_and_url: not SOURCE_URL_LABEL.search(label_and_url[0]),
    )
    for _, url in [*labelled_urls, ("home page", info.get("home_page") or "")]:
        match = GITHUB_REPOSITORY.match(url)
        if match:
            owner, name = match.group(1), match.group(2).removesuffix(".git")
            return f"https://github.com/{owner}/{name}"
    return None


def describe_github_repository(repository_url: str) -> GithubRepository | None:
    path = repository_url.removeprefix("https://github.com/")
    completed = subprocess.run(
        ["gh", "api", f"repos/{path}"], capture_output=True, text=True, check=False
    )
    if completed.returncode:
        return None
    repository = json.loads(completed.stdout)
    return GithubRepository(
        language=repository["language"],
        is_archived=repository["archived"],
        is_fork=repository["fork"],
        size_kilobytes=repository["size"],
        licence=(repository["license"] or {}).get("spdx_id") or "unknown",
    )


def is_eligible(repository: GithubRepository) -> bool:
    return (
        repository.language == "Python"
        and not repository.is_archived
        and not repository.is_fork
        and repository.size_kilobytes <= MAXIMUM_REPOSITORY_SIZE_KILOBYTES
    )


def find_head_commit(repository_url: str) -> str:
    completed = subprocess.run(
        ["git", "ls-remote", repository_url, "HEAD"], capture_output=True, text=True, check=True
    )
    return completed.stdout.split()[0]


def check_out_python_files(system: CalibrationSystem, checkouts: Path) -> Path:
    checkout = checkouts / f"{system.project}-{system.commit[:12]}"
    git = ["git", "-C", str(checkout)]
    if not checkout.exists():
        checkout.mkdir(parents=True)
        subprocess.run([*git, "init", "-q"], check=True)
        subprocess.run([*git, "sparse-checkout", "set", "--no-cone", "*.py"], check=True)
        subprocess.run(
            [
                *git,
                "fetch",
                "-q",
                "--depth",
                "1",
                "--filter=blob:none",
                system.repository_url,
                system.commit,
            ],
            check=True,
        )
        subprocess.run([*git, "checkout", "-q", "FETCH_HEAD"], check=True)
    head = subprocess.run(
        [*git, "rev-parse", "HEAD"], capture_output=True, text=True, check=True
    ).stdout.strip()
    if head != system.commit:
        raise SystemExit(f"{checkout} is at {head}, not at {system.commit}")
    return checkout


def total_production(project_measures: ProjectMeasures, name: MeasureName) -> int:
    return sum(
        measure.value
        for measure in project_measures.measures
        if measure.name is name and not measure.is_test_code
    )


def count_lines_of_code_per_file_fan_in(project_measures: ProjectMeasures) -> dict[str, int]:
    production = [measure for measure in project_measures.measures if not measure.is_test_code]
    lines_of_code = {
        measure.file: measure.value
        for measure in production
        if measure.name is MeasureName.FILE_LINES_OF_CODE
    }
    lines_of_code_per_fan_in: Counter[int] = Counter()
    for measure in production:
        if measure.name is MeasureName.FILE_FAN_IN:
            lines_of_code_per_fan_in[measure.value] += lines_of_code.get(measure.file, 0)
    return {str(fan_in): lines for fan_in, lines in sorted(lines_of_code_per_fan_in.items())}


def describe_risk_profiles(
    system: CalibrationSystem, project_measures: ProjectMeasures
) -> dict[str, object]:
    return {
        "project": system.project,
        "production_lines_of_code": total_production(
            project_measures, MeasureName.FILE_LINES_OF_CODE
        ),
        "duplicated_lines": total_production(project_measures, MeasureName.DUPLICATED_LINES),
        "risk_profiles": {
            profile.system_property.value: {
                band.value: lines for band, lines in profile.lines_of_code_per_band.items()
            }
            for profile in build_risk_profiles(project_measures)
        },
        "lines_of_code_per_file_fan_in": count_lines_of_code_per_file_fan_in(project_measures),
    }


def find_candidate_systems(
    packages: list[str], excluded_repository_urls: set[str]
) -> Iterator[CalibrationSystem]:
    seen_repository_urls = set(excluded_repository_urls)
    for download_rank, package in enumerate(packages, start=1):
        repository_url = find_repository_url(package)
        if repository_url is None or repository_url.lower() in seen_repository_urls:
            continue
        seen_repository_urls.add(repository_url.lower())
        repository = describe_github_repository(repository_url)
        if repository is None or not is_eligible(repository):
            continue
        yield CalibrationSystem(
            project=package,
            download_rank=download_rank,
            repository_url=repository_url,
            commit=find_head_commit(repository_url),
            licence=repository.licence,
        )


def measure_systems(
    candidate_systems: Iterable[CalibrationSystem], checkouts: Path
) -> tuple[list[CalibrationSystem], list[dict[str, object]]]:
    systems: list[CalibrationSystem] = []
    risk_profiles: list[dict[str, object]] = []
    for system in candidate_systems:
        project_measures = measure_project(check_out_python_files(system, checkouts))
        lines_of_code = total_production(project_measures, MeasureName.FILE_LINES_OF_CODE)
        print(f"{system.download_rank:5} {system.project}: {lines_of_code} LOC", file=sys.stderr)
        if lines_of_code < MINIMUM_PRODUCTION_LINES_OF_CODE:
            continue
        systems.append(system)
        risk_profiles.append(describe_risk_profiles(system, project_measures))
        if len(systems) == SYSTEM_COUNT:
            break
    return systems, risk_profiles


def find_snapshot_candidates(snapshot: dict[str, object]) -> Iterator[CalibrationSystem]:
    rows = snapshot["rows"]
    assert isinstance(rows, list)
    excluded_repository_urls = {
        entry["repository_url"].lower() for entry in json.loads(EVALUATION_SET_FILE.read_text())
    }
    return find_candidate_systems([row["project"] for row in rows], excluded_repository_urls)


def main() -> None:
    checkouts, output_directory = Path(sys.argv[1]), Path(sys.argv[2])
    calibration_set_file = output_directory / "calibration_set.json"
    if len(sys.argv) > 3:
        snapshot = json.loads(Path(sys.argv[3]).read_text())
        systems, risk_profiles = measure_systems(find_snapshot_candidates(snapshot), checkouts)
        calibration_set = {
            "snapshot": {"url": SNAPSHOT_URL, "last_update": snapshot["last_update"]},
            "systems": [asdict(system) for system in systems],
        }
        calibration_set_file.write_text(json.dumps(calibration_set, indent=2) + "\n")
    else:
        pinned_systems = [
            CalibrationSystem(**system)
            for system in json.loads(calibration_set_file.read_text())["systems"]
        ]
        systems, risk_profiles = measure_systems(pinned_systems, checkouts)
        if systems != pinned_systems:
            raise SystemExit("a pinned system no longer has enough production lines of code")
    (output_directory / "calibration_risk_profiles.json").write_text(
        json.dumps(risk_profiles, indent=2) + "\n"
    )
    print(f"{len(systems)} systems, last at download rank {systems[-1].download_rank}")


if __name__ == "__main__":
    main()
