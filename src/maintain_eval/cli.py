"""Command-line entry point: `maintain-eval smoke --target PATH`."""

import argparse
import logging
import sys
from collections.abc import Sequence
from pathlib import Path

from maintain_eval.observability import new_run_id
from maintain_eval.schemas import Characteristic
from maintain_eval.version_b import AgentOutputError, run_smoke


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="maintain-eval")
    sub = parser.add_subparsers(dest="command", required=True)
    smoke = sub.add_parser("smoke", help="Run the Version B agent once and print its Finding.")
    smoke.add_argument("--target", type=Path, required=True, help="Project directory to analyse.")
    smoke.add_argument(
        "--characteristic",
        type=Characteristic,
        choices=list(Characteristic),
        default=Characteristic.MODULARITY,
    )
    smoke.add_argument("--run-id", default=None, help="Defaults to a random id.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")

    run_id = args.run_id or new_run_id()
    print(f"run_id={run_id} characteristic={args.characteristic.value}", file=sys.stderr)
    try:
        finding = run_smoke(args.target, args.characteristic, run_id=run_id)
    except (AgentOutputError, NotADirectoryError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(finding.model_dump_json(indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
