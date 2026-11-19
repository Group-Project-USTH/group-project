import json
import sys
from collections import Counter
from fractions import Fraction
from pathlib import Path

from maintainability_lens.evaluation import calibrate_rating_limits, derive_band_limits
from maintainability_lens.ratings import BandLimits, BandShares, find_cumulative_band_shares
from maintainability_lens.schemas import Rating, RiskBand, RiskProfile, SystemProperty

CALIBRATED_SYSTEM_PROPERTIES = (
    SystemProperty.UNIT_SIZE,
    SystemProperty.UNIT_INTERFACING,
    SystemProperty.MODULE_COUPLING,
)


def load_system_shares(
    risk_profiles_file: Path, system_property: SystemProperty
) -> list[BandShares]:
    system_shares = []
    for system in json.loads(risk_profiles_file.read_text()):
        lines_of_code_per_band = system["risk_profiles"][system_property.value]
        profile = RiskProfile(
            system_property=system_property,
            lines_of_code_per_band={
                RiskBand(band): lines for band, lines in lines_of_code_per_band.items()
            },
        )
        shares = find_cumulative_band_shares(profile)
        if shares is not None:
            system_shares.append(shares)
    return system_shares


def load_lines_of_code_per_file_fan_in(risk_profiles_file: Path) -> list[dict[int, int]]:
    return [
        {int(fan_in): lines for fan_in, lines in system["lines_of_code_per_file_fan_in"].items()}
        for system in json.loads(risk_profiles_file.read_text())
    ]


def find_cumulative_shares_above(
    lines_of_code_per_value: dict[int, int], band_limits: BandLimits
) -> BandShares:
    total = sum(lines_of_code_per_value.values())
    moderate, high, very_high = (
        Fraction(
            100 * sum(lines for value, lines in lines_of_code_per_value.items() if value > limit),
            total,
        )
        for limit in band_limits
    )
    return moderate, high, very_high


def rate(shares: BandShares, limits: tuple[tuple[Rating, BandShares], ...]) -> Rating:
    return next(
        (
            rating
            for rating, rating_limits in limits
            if all(share <= limit for share, limit in zip(shares, rating_limits, strict=True))
        ),
        Rating.MINUS_MINUS,
    )


def format_percentage(share: Fraction) -> str:
    return f"{float(share):.1f}"


def print_rating_table(title: str, system_shares: list[BandShares]) -> None:
    limits = calibrate_rating_limits(system_shares)
    systems_per_rating = Counter(rate(shares, limits) for shares in system_shares)
    print(f"\n{title} ({len(system_shares)} systems)\n")
    print("| Rating | moderate or worse | high or worse | very high | systems |")
    print("|---|---|---|---|---|")
    for rating, rating_limits in limits:
        shares = " | ".join(format_percentage(limit) for limit in rating_limits)
        print(f"| `{rating.value}` | {shares} | {systems_per_rating[rating]} |")
    print(f"| `{Rating.MINUS_MINUS.value}` | above | above | above | ", end="")
    print(f"{systems_per_rating[Rating.MINUS_MINUS]} |")


def main() -> None:
    risk_profiles_file = Path(sys.argv[1])
    for system_property in CALIBRATED_SYSTEM_PROPERTIES:
        system_shares = load_system_shares(risk_profiles_file, system_property)
        print_rating_table(f"{system_property.value}, bands of V18.1", system_shares)
    lines_of_code_per_file_fan_in = load_lines_of_code_per_file_fan_in(risk_profiles_file)
    band_limits = derive_band_limits(lines_of_code_per_file_fan_in)
    print(f"\nmodule_coupling band limits derived from the Calibration set: {band_limits}")
    print_rating_table(
        f"module_coupling, bands {band_limits}",
        [
            find_cumulative_shares_above(lines_of_code_per_value, band_limits)
            for lines_of_code_per_value in lines_of_code_per_file_fan_in
        ],
    )


if __name__ == "__main__":
    main()
