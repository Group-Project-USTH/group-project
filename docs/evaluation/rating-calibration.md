# Rating calibration on Python code

[ADR 0001](../adr/0001-deliver-as-claude-code-plugin.md), decision 8, rates unit size, unit
interfacing and module coupling only against a 4-star limit, because no public source gives
their five-level tables. Phase 4 calibrates those tables on Python code. This page records how,
and the tables that came out. The Ratings do not use them yet; that is a separate change.

## The Calibration set

100 open-source Python projects, each at a pinned commit, listed in
[`backend/evaluation/calibration_set.json`](../../backend/evaluation/calibration_set.json).
[`scripts/select_calibration_set.py`](../../scripts/select_calibration_set.py) walks the
[top PyPI packages by downloads](https://hugovk.github.io/top-pypi-packages/) (snapshot of
2026-11-01) in rank order. It keeps a package when:

- PyPI links it to a GitHub repository not already taken by a higher-ranked package;
- GitHub reports Python as the repository's main language, and the repository is not
  archived, not a fork, and at most 1 GB (this leaves out the Azure and Google Cloud SDK
  monorepos, which are mostly generated code);
- it is not one of the Evaluation set's six projects;
- it has at least 1,000 lines of production code by our Measures.

The 100th project is at download rank 180. Production code ranges from 1,043 to 171,131 lines
(median 7,675; 2.45 million in all). Only references are stored, never copies. The Risk
profiles of every project are in
[`backend/evaluation/calibration_risk_profiles.json`](../../backend/evaluation/calibration_risk_profiles.json),
with the lines of code at each file fan-in value.

## Method

**Risk bands.**

- Unit size and unit interfacing keep the bands of the SIG/TÜV NORD *Guidance for Producers*
  V18.1 (2026), because our Measures match its definitions (lines of code per unit, parameters
  per unit).
- Module coupling does not. V18.1's bands, 10/20/50, count incoming dependencies "such as
  invocations"; our `file_fan_in` counts the files that import a file, which is far lower. On
  those bands, 40 of the 100 projects have no code at all above fan-in 10, so 40 projects tie
  at the best Rating and no limit can separate them.
- So module coupling gets bands derived from the Calibration set with the method of Alves,
  Ypma and Visser (ICSM 2010): each band ends where 70, 80 and 90 % of the code lies at or
  below the fan-in value, each project weighing the same whatever its size. This gives
  **3 / 5 / 10**. Alves et al. got 10 / 22 / 56 for file fan-in on 100 Java and C# systems.

**Rating limits.**

- V18.0 (2026), section 5, calibrates so that benchmark systems fall 5/30/30/30/5 % into the
  five Ratings. We use the same split: 5 % at `++`, 35 % at `+` or better, 65 % at `o` or
  better, 95 % at `-` or better.
- SIG's own search for the limits (Alves, Correia and Visser, IWSM-MENSURA 2011) is not openly
  available, so ours is our own, in
  [`rating_calibration.py`](../../backend/src/maintainability_lens/evaluation/rating_calibration.py):
  1. For each Rating, take the limit for each of the three cumulative shares (moderate or
     worse, high or worse, very high) at the same quantile across the projects, starting at
     the target share.
  2. Raise that quantile until enough projects fall within all three limits at once.
  3. Round each limit up to 0.1 %.
- A project is rated with the first Rating whose three limits it meets, and `--` if none.

## Results

Each cell is the most code (%) allowed above that band, cumulative. The last column is how
many of the 100 projects get that Rating.

**Unit size** (lines of code per unit; bands 15 / 30 / 60):

| Rating | > 15 | > 30 | > 60 | projects |
|---|---|---|---|---|
| `++` | 31.1 | 9.3 | 0.0 | 6 |
| `+` | 54.8 | 27.8 | 9.3 | 29 |
| `o` | 66.4 | 43.5 | 21.4 | 30 |
| `-` | 78.7 | 63.2 | 37.8 | 31 |
| `--` | above | above | above | 4 |

**Unit interfacing** (parameters per unit, without `self` and `cls`; bands 2 / 4 / 6):

| Rating | > 2 | > 4 | > 6 | projects |
|---|---|---|---|---|
| `++` | 16.4 | 2.1 | 0.0 | 5 |
| `+` | 32.0 | 12.8 | 6.4 | 30 |
| `o` | 40.9 | 22.7 | 11.9 | 30 |
| `-` | 62.1 | 38.4 | 30.7 | 31 |
| `--` | above | above | above | 4 |

**Module coupling** (files importing the file; bands 3 / 5 / 10, derived above):

| Rating | > 3 | > 5 | > 10 | projects |
|---|---|---|---|---|
| `++` | 0.0 | 0.0 | 0.0 | 12 |
| `+` | 23.7 | 16.4 | 2.8 | 23 |
| `o` | 39.0 | 29.9 | 15.0 | 30 |
| `-` | 62.1 | 52.1 | 29.7 | 31 |
| `--` | above | above | above | 4 |

12 projects, not 5, get `++` for module coupling: none of their code is in a file with
fan-in above 3, and no limit can split a tie at zero.

**Against V18.1's 4-star limits** (`+` above, same bands):

| | > low | > moderate | > high |
|---|---|---|---|
| Unit size, Python `+` | 54.8 | 27.8 | 9.3 |
| Unit size, V18.1 4 stars | 48.0 | 24.2 | 9.1 |
| Unit interfacing, Python `+` | 32.0 | 12.8 | 6.4 |
| Unit interfacing, V18.1 4 stars | 15.4 | 3.4 | 0.9 |

Unit size comes out close to SIG's limit. Unit interfacing comes out about twice as lenient:
popular Python libraries take more parameters per unit than SIG's benchmark.

## Limits of these tables

- **Libraries, not applications.** Top PyPI packages are mostly libraries and developer tools;
  SIG's benchmark is mostly industrial systems.
- **Calibrated on projects, applied to files too.** The Evaluation set is rated one file at a
  time, and a single file's Risk profile is more extreme than a project's.
- **A snapshot.** SIG recalibrates yearly. Rerunning the selection later picks newer commits;
  the pinned set reproduces these numbers.
- **Not SIG's numbers.** These are our own limits on our own Measures. They are not SIG or
  TÜV NORD Ratings and must not be called "SIG stars".

## Reproduce

From `backend/`:

```bash
# re-measure the pinned set (about 40 minutes; fetches only the .py files of each project)
uv run python ../scripts/select_calibration_set.py <checkout-folder> evaluation
# or select it anew from a top-PyPI snapshot (needs an authenticated `gh` for GitHub metadata)
uv run python ../scripts/select_calibration_set.py <checkout-folder> evaluation <top-pypi-packages.json>
# print the tables from the recorded Risk profiles
uv run python ../scripts/calibrate_rating_thresholds.py evaluation/calibration_risk_profiles.json
```
