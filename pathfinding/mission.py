"""The full errand: collect every helper, deliver each, then reach the goal."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from pathfinding.search import Counter, Result, State, a_star, breadth_first, iterative_deepening
from pathfinding.world import World

# A search takes the world, a starting state, the acceptable end positions and a
# shared counter, and returns a Result.
Search = Callable[[World, State, set, Counter], Result]

ALGORITHMS: dict[str, Search] = {
    "bfs": breadth_first,
    "ids": iterative_deepening,
    "a*": a_star,
    "weighted a* (w=2)": lambda w, s, t, c: a_star(w, s, t, c, weight=2),
    "weighted a* (w=10)": lambda w, s, t, c: a_star(w, s, t, c, weight=10),
}


@dataclass(frozen=True)
class MissionResult:
    path: str
    cost: int
    expanded: int
    complete: bool


def solve(world: World, search: Search) -> MissionResult:
    """Run the mission one leg at a time.

    Helpers are collected greedily: each leg heads for whichever remaining helper
    the search reaches first, then delivers that one before looking for the next.
    """
    counter = Counter()
    state = State(world.start)
    path: list[str] = []
    cost = 0

    remaining = {helper: destination for helper, destination in zip(world.helpers, world.destinations)}

    while remaining:
        leg = search(world, state, set(remaining), counter)
        if not leg:
            return MissionResult("".join(path), cost, counter.expanded, complete=False)
        path.append(leg.path)
        cost += leg.cost
        state = _advance(world, state, leg.path)

        destination = remaining.pop(state.position)
        leg = search(world, state, {destination}, counter)
        if not leg:
            return MissionResult("".join(path), cost, counter.expanded, complete=False)
        path.append(leg.path)
        cost += leg.cost
        state = _advance(world, state, leg.path)

    leg = search(world, state, {world.goal}, counter)
    if not leg:
        return MissionResult("".join(path), cost, counter.expanded, complete=False)
    path.append(leg.path)
    cost += leg.cost

    return MissionResult("".join(path), cost, counter.expanded, complete=True)


def _advance(world: World, state: State, path: str) -> State:
    """Replay a path to recover the state it ends in, budgets included."""
    from pathfinding.search import successors

    for letter in path:
        for step, nxt in successors(world, state):
            if step == letter:
                state = nxt
                break
        else:
            raise ValueError(f"path step {letter!r} is not legal from {state}")
    return state
