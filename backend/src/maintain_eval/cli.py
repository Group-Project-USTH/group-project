"""Command-line entry point: `maintain-eval smoke --target PATH`."""

import argparse
import logging
import sys
from collections.abc import Sequence
from pathlib import Path

from maintain_eval.agent import AgentOutputError, run_smoke
from maintain_eval.observability import check_langfuse_auth, new_run_id
from maintain_eval.schemas import Characteristic


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="maintain-eval")
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
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")

    run_id = args.run_id or new_run_id()
    print(f"run_id={run_id} characteristic={args.characteristic.value}", file=sys.stderr)
    check_langfuse_auth()
    try:
        finding = run_smoke(
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
