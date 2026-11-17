# Rate with SIG 2007 where it has full tables, and do not invent the rest

Only three System properties have a full public table from Risk profile (or single Measure) to
Rating `++`…`--`: **volume, unit complexity and duplication**, all from Heitlager, Kuipers and
Visser (QUATIC 2007). For unit size, unit interfacing, module coupling and the component
properties, SIG publishes risk bands and the limits for **4 stars only**. That holds for the
2015 model in *Building Maintainable Software* and for the current 2026 criteria (V18.0) and
guidance (V18.1). No source we could open gives the other four boundaries. The current SIG
model also differs from 2007. It **dropped volume** in 2026, swapped component balance for
**component entanglement**, maps onto the five ISO/IEC 25010 Characteristics and aggregates
with a geometric/power mean. Two of our Measures do not match SIG's definitions:
`duplicated_lines` counts every copy, not the redundant ones, and `file_fan_in` counts
importing files, not dependencies. The recommendation at the end proposes a set made of 2007
tables plus V18.1 bands. It needs an ADR amendment, because ADR 0001 decision 8 names only
SIG 2007.

*Reading convention: **[Inference]** marks this author's reasoning, not a source's claim.
Page numbers are PDF pages of the copy linked. Read on 2026-11-17.*

## Sources actually read

| Source | Version | Access | Gives |
|---|---|---|---|
| Heitlager, Kuipers, Visser, "A Practical Model for Measuring Maintainability", QUATIC 2007, pp. 30–39, [doi:10.1109/QUATIC.2007.8](https://doi.org/10.1109/QUATIC.2007.8) | "preliminary report", PDF dated 2007-05-04 | [SIG-hosted copy](https://softwareimprovementgroup.com/wp-content/uploads/APracticalModelForMeasuringMaintainability.pdf) | full tables for volume, unit complexity, duplication, unit test coverage; ISO 9126 matrix |
| Alves, Ypma, Visser, "Deriving Metric Thresholds from Benchmark Data", ICSM 2010, pp. 1–10, [doi:10.1109/ICSM.2010.5609747](https://doi.org/10.1109/ICSM.2010.5609747) | — | read from a copy posted to a public mailing list (not an official host, so not linked); cite the DOI | the 70/80/90 % method; risk thresholds on Java/C# |
| Visser, *Building Maintainable Software*, Java ed. (O'Reilly, 2016) | "2015 version of the SIG/TÜViT Evaluation Criteria" | [SIG-hosted PDF](https://www.softwareimprovementgroup.com/resources/building-maintainable-software) | unit guidelines; 4-star limits for all eight System properties; 25010 matrix |
| SIG/TÜV NORD CERT *Evaluation Criteria Trusted Product Maintainability* | **V18.0, 2026-03-31** | [SIG PDF](https://www.softwareimprovementgroup.com/wp-content/uploads/SIG-TUViT-Evaluation-Criteria-Trusted-Product-Maintainability.pdf) | System properties, 25010 matrix, calibration, certification rules |
| … *Guidance for Producers* | **V18.1, 2026-03-31** | [SIG PDF](https://softwareimprovementgroup.com/wp-content/uploads/SIG-TUViT-Evaluation-Criteria-Trusted-Product-Maintainability-Guidance-for-producers.pdf) | risk bands and 4-star limits |
| Sigrid documentation (SIG's own docs repo) | 2026 | [sigridci/docs](https://github.com/Software-Improvement-Group/sigridci/tree/main/docs) | 0.5–5.5 scale, rounding, 2026 model changes, Python support |

**Not opened:** the full texts of Alves, Correia, Visser, "Benchmark-Based Aggregation of
Metrics to Ratings", IWSM/Mensura 2011, pp. 20–29
([doi:10.1109/IWSM-MENSURA.2011.15](https://doi.org/10.1109/IWSM-MENSURA.2011.15)) and Baggen,
Correia, Schill, Visser, *Software Quality Journal* 20 (2012) 287–307
([doi:10.1007/s11219-011-9144-9](https://doi.org/10.1007/s11219-011-9144-9)). Both are
paywalled, and the author copies on `di.uminho.pt` timed out from this machine. No Bijlsma et
al. paper was needed, because the guidance documents define the component properties.

## The course PDF matches Heitlager 2007 but covers three System properties

`docs/agents/Maintainability_Measurement_Models.pdf` is a two-page summary card. Card #12 is
dated 2026-10-24. It gives the CC bands 1–10/11–20/21–50/>50, the CC rating table, the
duplication table, the coverage table and "Sub-char rating = average of its linked
properties". All of these match Heitlager 2007 exactly (tables below). It gives **no
thresholds** for volume, unit size, unit interfacing, module coupling, component balance or
component independence. One detail is wrong: the card says SIG "maps them to the 5
sub-characteristics" under "SIG model (2007 / current)". The 2007 paper maps onto the **four
ISO 9126** ones (analysability, changeability, stability, testability; PDF p. 4, Fig. 3).

## Heitlager 2007: the only complete public rating tables

**Volume** (PDF p. 5). Man-years (MY) come from backfiring the LOC through the SPR
Programming Languages Table, and LOC excludes comment and blank lines:

| Rating | MY | Java KLOC | Cobol KLOC | PL/SQL KLOC |
|---|---|---|---|---|
| `++` | 0–8 | 0–66 | 0–131 | 0–46 |
| `+` | 8–30 | 66–246 | 131–491 | 46–173 |
| `o` | 30–80 | 246–665 | 491–1,310 | 173–461 |
| `-` | 80–160 | 655–1,310 (sic, 665) | 1,310–2,621 | 461–922 |
| `--` | >160 | >1,310 | >2,621 | >922 |

**Unit complexity** (PDF p. 6). Each unit falls into a band by McCabe CC, quoting the SEI
categories, and the Risk profile is the share of LOC in each band:

| CC | Risk | | Rating | max moderate | max high | max very high |
|---|---|---|---|---|---|---|
| 1–10 | low | | `++` | 25 % | 0 % | 0 % |
| 11–20 | moderate | | `+` | 30 % | 5 % | 0 % |
| 21–50 | high | | `o` | 40 % | 10 % | 0 % |
| >50 | very high | | `-` | 50 % | 15 % | 5 % |
| | | | `--` | otherwise | | |

The paper says these boundaries "are based on experience" and that the scheme is "language
independent" (p. 6).

**Duplication** (p. 7) is "the percentage of all code that occurs more than once in equal code
blocks of at least 6 lines", ignoring leading spaces. The Rating bands are `++` 0–3 %, `+`
3–5 %, `o` 5–10 %, `-` 10–20 % and `--` 20–100 %. **Unit test coverage** (p. 7) uses `++`
95–100 %, `+` 80–95 %, `o` 60–80 %, `-` 20–60 % and `--` 0–20 %. Coverage is dynamic, and
the paper admits it is not language independent. **Unit size** has no numbers: "The risk
categories and scoring guidelines are similar to those for complexity per unit, except that
the particular threshold values are different" (p. 7).

**Mapping and aggregation** (pp. 4, 8). Analysability takes volume, duplication, unit size
and unit testing. Changeability takes unit complexity and duplication. Stability takes unit
testing. Testability takes unit complexity, unit size and unit testing. Each ISO 9126 rating
is "a weighted average … The weights are all equal by default", and "averaging can be
applied again" for overall maintainability. No rounding rule is stated. The Fig. 5 worked
example has changeability = avg(`--`,`-`) = −1.5 shown as `-`, and an overall of `-`. Those
values fit an average of the *unrounded* ISO 9126 values (−0.625) rounded half up
**[Inference]**.

## Later versions publish risk bands, but only the 4-star limits

Alves et al. (2010) derived risk thresholds as the 70/80/90 % quantiles of LOC-weighted Measure
values. For unit interfacing they used 80/90/95 %. The benchmark was **100 Java and C#
systems** (about 12 MLOC) with test and generated code removed (Table IV, p. 10; §VII-D,
p. 9). The motivating example in §III uses 6/8/15 for CC, while Table IV gives 6/8/14. The
risk bands below are inclusive upper bounds of low/moderate/high, and anything above the last
one is very high:

| System property | Measure | Alves 2010 (Java/C#) | BMS 2016 ("2015 version") | V18.1 (2026) |
|---|---|---|---|---|
| unit size | LOC per unit | 30 / 44 / 74 | 15 / 30 / 60 | 15 / 30 / 60 |
| unit complexity | McCabe CC | 6 / 8 / 14 | 5 / 10 / 25 | 5 / 10 / 25 |
| unit interfacing | parameters | 2 / 3 / 4 | 2 / 4 / 6 (text says "more than seven" for the top band) | 2 / 4 / 6 |
| module coupling | incoming dependencies per module | 10 / 22 / 56 (file fan-in) | 10 / 20 / 50 (summed method fan-in per class) | 10 / 20 / 50 ("such as invocations") |

The limits below are the **cumulative maximum share of LOC above each band** for a 4-star
Rating. Sources: BMS Tables 2-2, 3-1, 4-1, 5-1 and 6-1 and chs. 7–9; V18.1 §3.1–3.7, pp. 6–14.

| System property | 4 stars, BMS 2016 | 4 stars, V18.1 (2026) |
|---|---|---|
| volume | ≤ 20 man-years (≈ 175 KLOC if Java only) | **removed** from the model |
| duplication (redundant LOC) | ≤ 4.6 % | ≤ 5.8 % |
| unit size >15 / >30 / >60 | 43.7 / 22.3 / 6.9 % | 48.0 / 24.2 / 9.1 % |
| unit complexity >5 / >10 / >25 | 25.2 / 10.0 / 1.5 % | 20.7 / 7.5 / 1.1 % |
| unit interfacing ≥3 / ≥5 / ≥7 | 13.8 / 2.7 / 0.7 % | 15.4 / 3.4 / 0.9 % |
| module coupling >10 / >20 / >50 | 21.6 / 13.8 / 6.6 % (per band, not cumulative; text says 21.8) | 9.7 / 5.3 / 1.8 % |
| component balance | ~9 components and adjusted Gini of sizes ≤ 0.71 | not in model |
| component independence | ≤ 14.2 % of code in modules with incoming cross-component dependencies | hidden code ≥ 94.5 % |
| component entanglement | not in model | ≤ 0.075 (normalised density + violation degree) |

Read the table with three cautions. First, "duplication" means different things. In 2007 it
counts every occurrence. BMS (ch. 4 sidebar, book p. 53) and V18.1 (p. 6) count only the
*redundant* lines, "occurrences … minus one". BMS also skips clones made only of import
statements. Second, the limits move every year. SIG "recalibrate[s] … yearly"
([2026 model changes](https://github.com/Software-Improvement-Group/sigridci/blob/main/docs/reference/quality-model-documents/2026-model-changes.md)),
and Sigrid lets users pin a model year such as `model: "2020"`
([scope configuration](https://github.com/Software-Improvement-Group/sigridci/blob/main/docs/reference/analysis-scope-configuration.md)).
Third, the BMS guidelines are developer advice, not Rating boundaries. They say 15 lines per
unit, 4 branch points (McCabe 5) and at most 4 parameters (BMS chs. 2, 3, 5). PyDriller cites
the guidance V11.0 (2019) for the same low-risk bounds 15/5/2
([PyDriller docs](https://pydriller.readthedocs.io/en/latest/deltamaintainability.html)).

**The `++`, `o`, `-` and `--` boundaries for these properties are not published in any
source we opened.** The method that produces them, calibrating rating thresholds so that
benchmark systems fall 5/30/30/30/5 % into 5…1 stars, is in Alves 2011 and Baggen 2012. V18.0
§5 (p. 11) confirms the 5/30/30/30/5 split. A search snippet of Alves's 2011 slides showed a
5-star CC row of 17.9 / 9.9 / 3.3 % on the 6/8/14 bands. **Unverified**: we could not open
the slides or the paper.

## SIG's matrix onto the five ISO/IEC 25010 Characteristics

| Characteristic | BMS 2016 (App. A, Table A-2) | V18.0 (2026, §4, p. 10 figure) |
|---|---|---|
| analysability | volume, duplication, unit size, component balance | duplication, unit size |
| modifiability | duplication, unit complexity, module coupling | duplication, unit complexity, module coupling |
| testability | volume, unit complexity, component independence | unit complexity, component independence |
| modularity | module coupling, component balance, component independence | module coupling, component entanglement, component independence |
| reusability | unit size, unit interfacing | unit size, unit interfacing |

V18.0 says the links "reflect expert opinion" (p. 9). Entanglement was already a Sigrid
System property in an API example dated 2022-02-06
([API docs](https://github.com/Software-Improvement-Group/sigridci/blob/main/docs/integrations/sigrid-api-documentation.md)).
The version that dropped component balance was not verified.

**Aggregation has changed over time:**

- **2007 and 2016:** an equal-weight average (2007) or a weighted average (BMS App. A) of
  System property Ratings into each Characteristic, then an average into maintainability.
- **Scale:** Sigrid computes on a continuous 0.5–5.5 scale. "rounding tolerances are always
  downwards, with a maximum of 2 decimals", so 1.49 gives 1 star and 2.5–3.49 gives 3 stars
  ([approach.md](https://github.com/Software-Improvement-Group/sigridci/blob/main/docs/getting-started/approach.md)).
  How a Risk profile is placed *between* boundaries on that scale (interpolation) is in
  Alves 2011 and Baggen 2012 (not verified).
- **2026:** the overall Rating switches from the arithmetic mean to the "geometric mean"
  (V18.0 §1.1, p. 5), which Sigrid's docs call the "power mean" (2026 model changes). The
  exponent is not published.
- **Certification:** requires maintainability ≥ 3 stars and every Characteristic ≥ 2 stars
  (V18.0 §6, p. 12).

## Thresholds are language-independent, and nothing is Python-specific

- **Same thresholds for every language.** Heitlager calls the CC and duplication schemes
  "language independent" (pp. 6–7). V18.0 measures "per programming language" and combines
  the languages weighted by volume (§3.2, p. 8). V18.1 states each limit "for each
  programming language used". SIG says it uses "technology-independent code measurements"
  ([2024 update](https://www.softwareimprovementgroup.com/maintainability-model-2024-update/)).
  No per-language threshold table is published.
- **Python.** Sigrid supports Python for maintainability
  ([technology support](https://github.com/Software-Improvement-Group/sigridci/blob/main/docs/reference/technology-support.md)),
  but SIG publishes no Python calibration. The only open threshold derivation (Alves 2010)
  used Java/C# only, and it warns that thresholds depend on the tool's McCabe variant and on
  scoping (§VII-D) **[Inference: lizard's CC on Python is not guaranteed to match SIG's]**.
- **Volume and backfiring.** 2007 converts LOC to man-years with the SPR table (p. 5). BMS
  gives 20 MY ≈ 175 KLOC for Java (ch. 9) and cites Capers Jones's 200 function points per
  year for Java (p. 99, footnote). **No Python factor was found.** SIG does not publish its
  factors, and QSM's public table v5.0 has no Python row
  ([QSM](https://www.qsm.com/resources/function-point-languages-table)). Since 2026 SIG
  shows volume in person-years but no longer rates it (2026 model changes).

## Our Measures do not all match SIG's definitions

| Our Measure | SIG definition | Consequence |
|---|---|---|
| `duplicated_lines` counts every line in a repeated 6-line block (`measures/duplication.py`) | 2007: same. 2016/2026: redundant lines only (copies − 1) | Use the 2007 table, or add a redundant-lines Measure before using 4.6/5.8 % |
| `file_fan_in` counts production files that import the file (`measures/module_coupling.py`) | incoming dependencies "such as invocations" (V18.1 §3.5). BMS: summed method fan-in per class | 10/20/50 assume call counts. Import counts are lower **[Inference]**, so those limits would be lenient |
| `parameter_count` without `self`/`cls` | "number of parameters (formal arguments)" (V18.1 §3.4) | SIG's treatment of Python `self` not stated (unverified) |
| unit LOC from lizard | LOC without comment and blank lines (2007 p. 5) | consistent |
| `is_test_code` | Alves 2010 removed test code before calibrating (§VII-D) | rate production code only |
| no coverage Measure | 2007 unit testing needs test runs | 2007 matrix not fully computable |
| no components | V18 entanglement and independence need top-level components | modularity and testability are partly unratable for now |

## Licensing and naming

- **The numbers.** Neither V18 PDF has a licence or copyright statement in its text. BMS is
  "Copyright © 2016 Software Improvement Group, B.V. All rights reserved" (p. 3). The Sigrid
  docs repo declares no licence (GitHub API `license: null`). **[Inference, not legal
  advice]:** numeric thresholds and a published method are facts and ideas, which tools such
  as PyDriller already reimplement with citation. Copying the documents' prose, figures or
  PDFs into the repo is not covered. Cite the numbers and link to them; do not commit the
  PDFs, the course card included.
- **The certification mark.** The *TÜV NORD CERT Trusted Product Maintainability* mark is
  issued only after a "licensed evaluation facility" reports the evaluation (V18.0 §6,
  p. 12). Our output must not claim certification, use the mark, or present its Ratings as
  "SIG stars".
- **Trademarks.** SIGRID is a US registered trademark of SIG (reg. 6182882), and the marks
  "SIG" and "SIG QM" are listed under the same owner
  ([Justia, secondary](https://trademarks.justia.com/owners/software-improvement-group-b-v-2124026);
  not checked in USPTO TSDR). **[Inference]:** say "thresholds from Heitlager et al. 2007 /
  SIG guidance V18.1", not "SIG Rating" or "Sigrid-compatible".

## Candidate threshold sets

| Set | System properties with a full `++`…`--` table | Currency | Licensing | Python fit |
|---|---|---|---|---|
| **A. SIG 2007 only** (ADR 0001 today) | unit complexity, duplication, volume (needs a Python MY factor we lack). Unit size, interfacing, coupling: **none** | 2007, lenient CC bands (10/20/50) | peer-reviewed paper, cite freely | language-independent by claim; matches our current `duplicated_lines` |
| **B. 2007 + BMS 2016 4-star limits** | as A; the rest get only a "meets 4 stars" boundary from a 2015 calibration | 2015 calibration, includes volume and component balance | copyrighted book: cite numbers, do not copy | Java benchmark; duplication and coupling definitions differ from ours |
| **C. V18.1 (2026) bands + 4-star limits** | none: one boundary per System property, no volume, entanglement needs components | current (2026-03-31), changes yearly | public PDFs, no stated licence: cite, do not redistribute | multi-language benchmark, nothing Python-specific; same Measure mismatches as B |
| **D. Own calibration** (Alves 2010 risk bands + Alves 2011 5/30/30/30/5 rating thresholds on a Python corpus, phase 4) | all we can measure, full five levels | as fresh as the corpus | our own numbers | calibrated on Python with our own tools (lizard, our fan-in), so no tool mismatch; needs a corpus of many Python systems and the Alves 2011 paper |

## Recommendation (this author's, not a source's)

1. **Phase 3 uses SIG 2007 tables verbatim for unit complexity and duplication.** These are the
   only published five-level tables, and both match the Measures we already compute. Each
   constant cites Heitlager 2007 with a page number, as ADR 0001 requires.
2. **For unit size, unit interfacing and module coupling, compute Risk profiles on the
   V18.1 bands (15/30/60, 2/4/6, 10/20/50) and report them, but give no five-level Rating
   yet.** At most report whether the profile meets the V18.1 4-star limit, labelled as such.
   Making up the `++`, `o`, `-` and `--` rows would put unsourced numbers behind a Verdict.
   For module coupling, first decide whether import fan-in is close enough to SIG's
   dependency count.
3. **Do not rate volume.** SIG itself dropped it in 2026, and there is no sourced Python
   man-year factor. Keep `file_lines_of_code` as a Measure and show it next to every Verdict
   as the size baseline.
4. **Map onto Characteristics with the V18.0 matrix**, which is native to ISO/IEC 25010, and
   average equally (2007). A Characteristic whose System properties are not all rated (for
   example modularity without components) gets `unknown` for its Rating, and the Verdict is
   left to Evidence.
5. **Plan set D for phase 4** if the team can assemble enough Python systems. Amend ADR 0001
   decision 8 now to say "SIG 2007 where a full table exists; V18.1 risk bands elsewhere;
   own calibration later".
