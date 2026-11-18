from maintainability_lens.evaluation.evaluation_scores import EvaluationScores
from maintainability_lens.schemas import Characteristic


def format_number(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.2f}"


def format_score_report(scores: EvaluationScores) -> str:
    approach_names = [str(approach.approach) for approach in scores.approaches]
    lines = [
        f"Raters: {scores.rater_count}. Consensus on {scores.consensus_pairs} pairs, "
        f"none on {scores.no_consensus_pairs}. Raters' pass share: "
        f"{format_number(scores.rater_pass_share)}.",
        "",
        "Accuracy against the Raters' consensus (alpha: agreement among Raters)",
        "",
        "| Characteristic | alpha | " + " | ".join(approach_names) + " |",
        "|---|---|" + "---|" * len(approach_names),
    ]
    for characteristic in Characteristic:
        accuracies = [
            format_number(approach.accuracy_per_characteristic[characteristic])
            for approach in scores.approaches
        ]
        alpha = format_number(scores.alpha_per_characteristic[characteristic])
        lines.append(f"| {characteristic} | {alpha} | " + " | ".join(accuracies) + " |")
    overall = [format_number(approach.accuracy_overall) for approach in scores.approaches]
    lines.append(f"| all | {format_number(scores.alpha_overall)} | " + " | ".join(overall) + " |")
    lines += [
        "",
        "| Approach | models | repetitions | compared pairs | pass share | unanimous share "
        "| alpha across repetitions | cost USD |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for approach in scores.approaches:
        lines.append(
            f"| {approach.approach} | {', '.join(approach.models) or '-'} | "
            f"{approach.repetitions} | {approach.compared_pairs} | "
            f"{format_number(approach.pass_share)} | {format_number(approach.unanimous_share)} | "
            f"{format_number(approach.alpha_across_repetitions)} | "
            f"{format_number(approach.total_cost_usd)} |"
        )
    lines += ["", "Each Rater against the consensus of the others:", ""]
    lines += [
        f"- {rater.rater}: {format_number(rater.accuracy_against_others)}"
        for rater in scores.raters
    ]
    return "\n".join(lines)
