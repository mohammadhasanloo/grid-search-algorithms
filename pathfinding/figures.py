"""Drawing a scenario and the routes different searches take through it."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.patches as patches  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

from pathfinding.mission import ALGORITHMS, solve  # noqa: E402
from pathfinding.world import MOVES, World  # noqa: E402

SENTRY_COLOUR = "#cf222e"
WATCHED_COLOUR = "#ffd8d6"
HELPER_COLOUR = "#0969da"
DESTINATION_COLOUR = "#8250df"
PATH_COLOUR = "#1a7f37"

STEPS = {letter: (row, column) for letter, row, column in MOVES}


def _walk(world: World, path: str) -> list[tuple[int, int]]:
    """Every cell the route passes through, starting at the world's start."""
    row, column = world.start
    cells = [(row, column)]
    for letter in path:
        row_offset, column_offset = STEPS[letter]
        row, column = row + row_offset, column + column_offset
        cells.append((row, column))
    return cells


def _draw_board(axis, world: World) -> None:
    for cell in world.watchers:
        axis.add_patch(patches.Rectangle((cell[1], cell[0]), 1, 1, color=WATCHED_COLOUR))
    for sentry in world.oraks:
        axis.add_patch(patches.Rectangle((sentry.column, sentry.row), 1, 1, color=SENTRY_COLOUR))
        axis.text(sentry.column + 0.5, sentry.row + 0.5, str(sentry.rank),
                  ha="center", va="center", color="white", fontsize=9, fontweight="bold")
    for helper in world.helpers:
        axis.add_patch(patches.Circle((helper[1] + 0.5, helper[0] + 0.5), 0.28, color=HELPER_COLOUR))
    for destination in world.destinations:
        axis.add_patch(patches.Rectangle((destination[1] + 0.25, destination[0] + 0.25),
                                         0.5, 0.5, fill=False, edgecolor=DESTINATION_COLOUR, lw=2))
    axis.text(world.start[1] + 0.5, world.start[0] + 0.5, "S", ha="center", va="center",
              fontsize=11, fontweight="bold")
    axis.text(world.goal[1] + 0.5, world.goal[0] + 0.5, "G", ha="center", va="center",
              fontsize=11, fontweight="bold")

    axis.set_xlim(0, world.columns)
    axis.set_ylim(world.rows, 0)
    axis.set_xticks(range(world.columns + 1))
    axis.set_yticks(range(world.rows + 1))
    axis.set_xticklabels([]), axis.set_yticklabels([])
    axis.grid(color="#d0d7de", linewidth=0.8)
    axis.set_aspect("equal")


def routes(world: World, output_path: Path, algorithms: list[str] | None = None) -> Path:
    """One panel per algorithm, each showing the route it found."""
    algorithms = algorithms or ["bfs", "a*", "weighted a* (w=10)"]
    figure, axes = plt.subplots(1, len(algorithms), figsize=(4.6 * len(algorithms), 4.8))
    axes = [axes] if len(algorithms) == 1 else list(axes)

    for axis, name in zip(axes, algorithms):
        result = solve(world, ALGORITHMS[name])
        _draw_board(axis, world)
        cells = _walk(world, result.path)
        axis.plot([c[1] + 0.5 for c in cells], [c[0] + 0.5 for c in cells],
                  color=PATH_COLOUR, linewidth=2, alpha=0.85, solid_capstyle="round")
        axis.set_title(f"{name}\ncost {result.cost}, {result.expanded:,} nodes expanded", fontsize=11)

    figure.suptitle(
        "S start, G goal, circles are helpers, outlines their destinations.\n"
        "Red cells are sentries labelled with their rank; pink is the region each watches.",
        fontsize=10,
        y=1.06,
    )
    figure.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, dpi=140, bbox_inches="tight")
    plt.close(figure)
    return output_path
