"""The map: grid bounds, oraks and their watched regions, helpers and goals."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

Position = tuple[int, int]

MOVES: tuple[tuple[str, int, int], ...] = (
    ("L", 0, -1),
    ("R", 0, 1),
    ("U", -1, 0),
    ("D", 1, 0),
)


@dataclass(frozen=True)
class Orak:
    row: int
    column: int
    rank: int

    @property
    def position(self) -> Position:
        return (self.row, self.column)


@dataclass(frozen=True)
class World:
    """A parsed scenario.

    ``watchers`` maps every monitored cell to the orak watching it. A cell inside
    two regions is attributed to the later orak, matching how the regions are
    painted onto the map in order.
    """

    rows: int
    columns: int
    start: Position
    goal: Position
    oraks: tuple[Orak, ...]
    helpers: tuple[Position, ...]
    destinations: tuple[Position, ...]
    watchers: dict[Position, int]
    blocked: frozenset[Position]

    def in_bounds(self, position: Position) -> bool:
        row, column = position
        return 0 <= row < self.rows and 0 <= column < self.columns

    def rank_of(self, orak_index: int) -> int:
        return self.oraks[orak_index].rank


def _watched_regions(
    rows: int, columns: int, oraks: tuple[Orak, ...]
) -> tuple[dict[Position, int], frozenset[Position]]:
    """Cells each orak watches, out to its rank in Manhattan distance."""
    watchers: dict[Position, int] = {}
    blocked = {orak.position for orak in oraks}

    for index, orak in enumerate(oraks):
        for row_offset in range(-orak.rank, orak.rank + 1):
            remaining = orak.rank - abs(row_offset)
            for column_offset in range(-remaining, remaining + 1):
                if row_offset == 0 and column_offset == 0:
                    continue
                cell = (orak.row + row_offset, orak.column + column_offset)
                if 0 <= cell[0] < rows and 0 <= cell[1] < columns and cell not in blocked:
                    watchers[cell] = index

    return watchers, frozenset(blocked)


def parse(path: Path | str) -> World:
    """Read a scenario file.

    Format, one item per line: grid size, start, goal, then the orak and helper
    counts, then one line per orak (row, column, rank), one per helper position,
    and one per helper destination in the same order.
    """
    numbers = [
        [int(token) for token in line.split()]
        for line in Path(path).read_text().splitlines()
        if line.strip()
    ]
    if len(numbers) < 4:
        raise ValueError(f"{path} is too short to be a scenario")

    rows, columns = numbers[0]
    start = (numbers[1][0], numbers[1][1])
    goal = (numbers[2][0], numbers[2][1])
    orak_count, helper_count = numbers[3]

    cursor = 4
    oraks = tuple(Orak(*numbers[cursor + i]) for i in range(orak_count))
    cursor += orak_count
    helpers = tuple((numbers[cursor + i][0], numbers[cursor + i][1]) for i in range(helper_count))
    cursor += helper_count
    destinations = tuple(
        (numbers[cursor + i][0], numbers[cursor + i][1]) for i in range(helper_count)
    )

    watchers, blocked = _watched_regions(rows, columns, oraks)
    return World(
        rows=rows,
        columns=columns,
        start=start,
        goal=goal,
        oraks=oraks,
        helpers=helpers,
        destinations=destinations,
        watchers=watchers,
        blocked=blocked,
    )
