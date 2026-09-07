"""Uninformed and informed search over the grid.

The search state is more than a position. An orak watching a region tolerates
being crossed for at most ``rank`` consecutive cells, so how a cell was reached
determines whether it can be left. State therefore carries the orak whose region
is currently being crossed and how many steps remain inside it.
"""

from __future__ import annotations

import heapq
from collections import deque
from dataclasses import dataclass, field

from pathfinding.world import MOVES, Position, World


@dataclass(frozen=True)
class State:
    position: Position
    orak: int | None = None
    budget: int = 0


@dataclass
class Result:
    """A completed search."""

    path: str
    cost: int
    expanded: int
    found: bool = True

    def __bool__(self) -> bool:
        return self.found


@dataclass
class Counter:
    """Nodes expanded, carried across the legs of a multi-stage mission."""

    expanded: int = 0


def successors(world: World, state: State):
    """Legal moves out of a state, as (letter, next state)."""
    for letter, row_offset, column_offset in MOVES:
        cell = (state.position[0] + row_offset, state.position[1] + column_offset)
        if not world.in_bounds(cell) or cell in world.blocked:
            continue

        watcher = world.watchers.get(cell)
        if watcher is None:
            yield letter, State(cell, None, 0)
            continue

        if watcher == state.orak:
            if state.budget <= 0:
                continue  # this orak has watched us for long enough
            yield letter, State(cell, watcher, state.budget - 1)
        else:
            yield letter, State(cell, watcher, world.rank_of(watcher) - 1)


def manhattan(a: Position, b: Position) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _reconstruct(parents: dict, state: State) -> str:
    letters = []
    while parents[state][0] is not None:
        parent, letter = parents[state]
        letters.append(letter)
        state = parent
    return "".join(reversed(letters))


def breadth_first(world: World, start: State, targets: set[Position], counter: Counter) -> Result:
    """Shortest path by number of moves, exploring the frontier in order."""
    if start.position in targets:
        return Result("", 0, 0)

    parents = {start: (None, None)}
    frontier = deque([start])
    while frontier:
        state = frontier.popleft()
        counter.expanded += 1
        for letter, nxt in successors(world, state):
            if nxt in parents:
                continue
            parents[nxt] = (state, letter)
            if nxt.position in targets:
                path = _reconstruct(parents, nxt)
                return Result(path, len(path), counter.expanded)
            frontier.append(nxt)
    return Result("", 0, counter.expanded, found=False)


def _depth_limited(world, state, targets, limit, parents, counter, seen) -> State | None:
    """Depth-first search bounded by ``limit`` remaining moves.

    ``seen`` records the largest remaining depth each state has been explored
    with. Revisiting a state with no more depth left than last time can only
    reproduce paths already searched, so it is skipped. Plain backtracking DFS
    without this is exponential in the limit and does not finish on these grids.
    """
    if state.position in targets:
        return state
    if limit == 0 or seen.get(state, -1) >= limit:
        return None
    seen[state] = limit

    counter.expanded += 1
    for letter, nxt in successors(world, state):
        if nxt in parents:
            continue
        parents[nxt] = (state, letter)
        found = _depth_limited(world, nxt, targets, limit - 1, parents, counter, seen)
        if found is not None:
            return found
        del parents[nxt]
    return None


def iterative_deepening(
    world: World, start: State, targets: set[Position], counter: Counter, max_depth: int = 200
) -> Result:
    """Depth-first to a growing limit: BFS's optimality at DFS's memory cost."""
    for limit in range(max_depth + 1):
        parents = {start: (None, None)}
        found = _depth_limited(world, start, targets, limit, parents, counter, {})
        if found is not None:
            path = _reconstruct(parents, found)
            return Result(path, len(path), counter.expanded)
    return Result("", 0, counter.expanded, found=False)


def a_star(
    world: World,
    start: State,
    targets: set[Position],
    counter: Counter,
    weight: float = 1.0,
) -> Result:
    """Best-first search on f = g + weight * h, with h the Manhattan distance.

    At weight 1 the heuristic never overestimates, since every move costs one and
    Manhattan distance is the fewest moves an unobstructed path could take, so the
    result is optimal. Above 1 the search leans harder on the heuristic: it
    expands fewer nodes and may return a longer path.
    """
    if start.position in targets:
        return Result("", 0, 0)

    def heuristic(position: Position) -> int:
        return min(manhattan(position, target) for target in targets)

    parents = {start: (None, None)}
    best_cost = {start: 0}
    queue = [(weight * heuristic(start.position), 0, 0, start)]
    tie_break = 0

    while queue:
        _, cost, _, state = heapq.heappop(queue)
        if cost > best_cost.get(state, float("inf")):
            continue
        if state.position in targets:
            path = _reconstruct(parents, state)
            return Result(path, len(path), counter.expanded)

        counter.expanded += 1
        for letter, nxt in successors(world, state):
            new_cost = cost + 1
            if new_cost >= best_cost.get(nxt, float("inf")):
                continue
            best_cost[nxt] = new_cost
            parents[nxt] = (state, letter)
            tie_break += 1
            heapq.heappush(queue, (new_cost + weight * heuristic(nxt.position), new_cost, tie_break, nxt))

    return Result("", 0, counter.expanded, found=False)
