"""Command-line entry point: `maintainability-lens smoke|measure|mcp|evaluate-set`."""

import argparse
import logging
import sys
from collections.abc import Sequence
from pathlib import Path

from maintainability_lens.evaluation import (
    Approach,
    ClaudeCodeOptions,
    load_evaluation_set,
    run_approach,
)
from maintainability_lens.measures import measure_project
from maintainability_lens.schemas import Characteristic


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="maintainability-lens")
    sub = parser.add_subparsers(dest="command", required=True)
    smoke = sub.add_parser("smoke", help="Run the agent once and print its Finding.")
    smoke.add_argument("--target", type=Path, required=True, help="Project directory to analyse.")
    smoke.add_argument(
        "--characteristic",
        type=Characteristic,
        choices=list(Characteristic),
        default=Characteristic.MODULARITY,
    )
    smoke.add_argument("--run-id", default=None, help="Defaults to a random id.")
    smoke.add_argument(
        "--session-id",
        default=None,
        help="Langfuse session grouping related runs.",
    )
    measure = sub.add_parser("measure", help="Print the project's Measures as JSON.")
    measure.add_argument("--target", type=Path, required=True, help="Project directory to measure.")
    sub.add_parser("mcp", help="Serve the Measures as an MCP server over stdio.")
    evaluate_set = sub.add_parser(
        "evaluate-set", help="Record one Approach's Findings on every file of the Evaluation set."
    )
    evaluate_set.add_argument("--approach", type=Approach, choices=list(Approach), required=True)
    evaluate_set.add_argument(
        "--evaluation-set", type=Path, default=Path("evaluation") / "evaluation_set.json"
    )
    evaluate_set.add_argument(
        "--checkouts", type=Path, required=True, help="Folder for the pinned project checkouts."
    )
    evaluate_set.add_argument(
        "--output", type=Path, required=True, help="Folder for the <approach>.jsonl Findings."
    )
    evaluate_set.add_argument("--repetitions", type=int, default=1)
    evaluate_set.add_argument("--model", help="Claude model id; required for claude-code-skill.")
    evaluate_set.add_argument(
        "--max-budget-usd", type=float, default=2.0, help="Spending cap per file and repetition."
    )
    evaluate_set.add_argument(
        "--plugin-dir", type=Path, default=Path(".."), help="The plugin root (the repo root)."
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
    if args.command == "measure":
        return run_measure(args.target)
    if args.command == "mcp":
        return run_mcp_server()
    if args.command == "evaluate-set":
        return run_evaluate_set(args)
    return run_smoke(args)


def run_measure(target: Path) -> int:
    try:
        project_measures = measure_project(target)
    except NotADirectoryError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(project_measures.model_dump_json(indent=2))
    return 0


def run_evaluate_set(args: argparse.Namespace) -> int:
    claude_code_options = None
    if args.approach is Approach.CLAUDE_CODE_SKILL:
        if args.model is None:
            print("error: claude-code-skill needs --model", file=sys.stderr)
            return 2
        claude_code_options = ClaudeCodeOptions(
            plugin_directory=args.plugin_dir.resolve(),
            model=args.model,
            max_budget_usd=args.max_budget_usd,
        )
    summary = run_approach(
        args.approach,
        load_evaluation_set(args.evaluation_set),
        args.checkouts,
        args.output,
        repetitions=args.repetitions,
        claude_code_options=claude_code_options,
    )
    print(f"{summary.recorded_findings} new Findings in {args.output / f'{args.approach}.jsonl'}")
    if summary.failed_file_ids:
        failed = ", ".join(summary.failed_file_ids)
        print(f"failed: {failed}; run again to retry them", file=sys.stderr)
        return 1
    return 0


def run_mcp_server() -> int:
    from maintainability_lens.mcp_server import serve

    serve()
    return 0


def run_smoke(args: argparse.Namespace) -> int:
    # The LLM stack is a dev-only dependency group, absent when installed with uvx.
    try:
        from maintainability_lens.agent import AgentOutputError, evaluate_characteristic
        from maintainability_lens.observability import check_langfuse_auth, new_run_id
    except ImportError:
        print(
            "error: smoke needs the agent dependency group (`uv sync` in backend/)", file=sys.stderr
        )
        return 1
    run_id = args.run_id or new_run_id()
    print(f"run_id={run_id} characteristic={args.characteristic.value}", file=sys.stderr)
    check_langfuse_auth()
    try:
        finding = evaluate_characteristic(
            args.target,
            args.characteristic,
            run_id=run_id,
            session_id=args.session_id,
            on_trace_url=lambda url: print(f"trace={url}", file=sys.stderr),
        )
    except (AgentOutputError, NotADirectoryError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # e.g. provider/network errors; already recorded on the trace
        print(f"error: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print(finding.model_dump_json(indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
