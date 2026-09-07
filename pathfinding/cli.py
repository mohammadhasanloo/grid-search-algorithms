"""Command line entry point: ``python -m pathfinding.cli ...``"""

from __future__ import annotations

import argparse
from pathlib import Path

from pathfinding.benchmark import run, to_markdown, write
from pathfinding.figures import routes
from pathfinding.mission import ALGORITHMS, solve
from pathfinding.world import parse

ROOT = Path(__file__).resolve().parent.parent
SCENARIOS = ROOT / "scenarios"
RESULTS = ROOT / "results"
DOCS = ROOT / "docs"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    solver = subparsers.add_parser("solve", help="solve one scenario")
    solver.add_argument("scenario", type=Path)
    solver.add_argument("--algorithm", choices=sorted(ALGORITHMS), default="a*")

    bench = subparsers.add_parser("benchmark", help="run every algorithm over every scenario")
    bench.add_argument("--scenarios", type=Path, default=SCENARIOS)
    bench.add_argument("--results", type=Path, default=RESULTS)
    bench.add_argument("--repeats", type=int, default=3)

    figure = subparsers.add_parser("figure", help="draw the routes for one scenario")
    figure.add_argument("scenario", type=Path)
    figure.add_argument("--output", type=Path, default=DOCS / "routes.png")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    if args.command == "solve":
        world = parse(args.scenario)
        result = solve(world, ALGORITHMS[args.algorithm])
        status = "reached the goal" if result.complete else "did not finish"
        print(f"{args.algorithm}: {status}")
        print(f"  path cost      {result.cost}")
        print(f"  nodes expanded {result.expanded:,}")
        print(f"  path           {result.path}")
        return 0

    if args.command == "figure":
        print(f"wrote {routes(parse(args.scenario), args.output)}")
        return 0

    scenarios = sorted(args.scenarios.glob("*.txt"))
    if not scenarios:
        raise SystemExit(f"no scenarios found in {args.scenarios}")
    rows = run(scenarios, repeats=args.repeats)
    print(to_markdown(rows))
    markdown, data = write(rows, args.results)
    print(f"\nwrote {markdown} and {data}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
