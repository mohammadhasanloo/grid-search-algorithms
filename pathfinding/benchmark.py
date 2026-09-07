"""Running every algorithm over every scenario and recording what it cost."""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from pathfinding.mission import ALGORITHMS, solve
from pathfinding.world import parse


@dataclass(frozen=True)
class Row:
    scenario: str
    algorithm: str
    cost: int
    expanded: int
    milliseconds: float
    complete: bool


def run(scenarios: list[Path], repeats: int = 3) -> list[Row]:
    """Solve each scenario with each algorithm, timing the best of `repeats`."""
    rows = []
    for path in scenarios:
        world = parse(path)
        for name, algorithm in ALGORITHMS.items():
            best = None
            result = None
            for _ in range(repeats):
                start = time.perf_counter()
                result = solve(world, algorithm)
                elapsed = (time.perf_counter() - start) * 1000
                best = elapsed if best is None else min(best, elapsed)
            rows.append(
                Row(path.stem, name, result.cost, result.expanded, round(best, 2), result.complete)
            )
    return rows


def to_markdown(rows: list[Row]) -> str:
    lines = ["| scenario | algorithm | path cost | nodes expanded | ms |",
             "| --- | --- | --- | --- | --- |"]
    for row in rows:
        lines.append(
            f"| {row.scenario} | {row.algorithm} | {row.cost} | {row.expanded:,} | {row.milliseconds} |"
        )
    return "\n".join(lines)


def write(rows: list[Row], directory: Path) -> tuple[Path, Path]:
    directory.mkdir(parents=True, exist_ok=True)
    markdown = directory / "benchmark.md"
    data = directory / "benchmark.json"
    markdown.write_text(to_markdown(rows) + "\n")
    data.write_text(json.dumps([asdict(r) for r in rows], indent=2) + "\n")
    return markdown, data
