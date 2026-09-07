"""Tests for parsing, movement rules and the three search strategies."""

from __future__ import annotations

from pathlib import Path

import pytest

from pathfinding.mission import ALGORITHMS, solve
from pathfinding.search import Counter, State, a_star, breadth_first, iterative_deepening, successors
from pathfinding.world import Orak, World, parse

SCENARIOS = Path(__file__).resolve().parent.parent / "scenarios"


def empty_world(rows=5, columns=5, start=(0, 0), goal=(4, 4), oraks=(), helpers=(), destinations=()):
    from pathfinding.world import _watched_regions

    watchers, blocked = _watched_regions(rows, columns, oraks)
    return World(rows, columns, start, goal, oraks, helpers, destinations, watchers, blocked)


def test_parse_reads_every_section():
    world = parse(SCENARIOS / "test_02.txt")
    assert (world.rows, world.columns) == (8, 8)
    assert world.start == (0, 0) and world.goal == (7, 7)
    assert len(world.oraks) == 3 and len(world.helpers) == 2
    assert len(world.helpers) == len(world.destinations)


def test_orak_cells_are_impassable_and_their_region_is_watched():
    world = empty_world(oraks=(Orak(2, 2, 1),))
    assert (2, 2) in world.blocked
    assert set(world.watchers) == {(1, 2), (3, 2), (2, 1), (2, 3)}


def test_watched_region_is_a_manhattan_diamond():
    world = empty_world(rows=9, columns=9, oraks=(Orak(4, 4, 2),))
    assert (4, 6) in world.watchers and (5, 5) in world.watchers
    assert (5, 6) not in world.watchers  # distance 3


def test_moves_stay_inside_the_grid():
    world = empty_world()
    corner = list(successors(world, State((0, 0))))
    assert {letter for letter, _ in corner} == {"R", "D"}


def test_an_orak_cell_is_never_entered():
    world = empty_world(oraks=(Orak(0, 1, 1),))
    assert all(nxt.position != (0, 1) for _, nxt in successors(world, State((0, 0))))


def test_entering_a_region_starts_the_budget_at_rank_minus_one():
    world = empty_world(rows=9, columns=9, oraks=(Orak(4, 4, 2),))
    moves = {letter: nxt for letter, nxt in successors(world, State((4, 1)))}
    assert moves["R"].position == (4, 2)
    assert moves["R"].orak == 0 and moves["R"].budget == 1


def test_a_region_cannot_be_crossed_once_the_budget_is_spent():
    world = empty_world(rows=9, columns=9, oraks=(Orak(4, 4, 2),))
    spent = State((4, 2), orak=0, budget=0)
    assert all(nxt.position not in world.watchers for _, nxt in successors(world, spent))


def test_leaving_and_reentering_resets_the_budget():
    world = empty_world(rows=9, columns=9, oraks=(Orak(4, 4, 2),))
    outside = State((4, 1), orak=None, budget=0)
    moves = {letter: nxt for letter, nxt in successors(world, outside)}
    assert moves["R"].budget == world.rank_of(0) - 1


def test_breadth_first_finds_the_shortest_route():
    world = empty_world()
    result = breadth_first(world, State(world.start), {world.goal}, Counter())
    assert result.cost == 8  # 4 right, 4 down


@pytest.mark.parametrize("search", [breadth_first, iterative_deepening, a_star])
def test_every_optimal_search_agrees_on_cost(search):
    world = empty_world(oraks=(Orak(2, 2, 1),))
    result = search(world, State(world.start), {world.goal}, Counter())
    assert result.found
    assert result.cost == 8


def test_a_star_expands_fewer_nodes_than_breadth_first():
    """On an obstacle-free grid the heuristic is exact and almost every node ties
    on f, so the saving only appears once oraks force the search around them."""
    world = parse(SCENARIOS / "test_02.txt")
    informed = solve(world, ALGORITHMS["a*"])
    blind = solve(world, ALGORITHMS["bfs"])
    assert informed.cost == blind.cost
    assert informed.expanded < blind.expanded


def test_a_heavier_weight_never_finds_a_shorter_path():
    world = parse(SCENARIOS / "test_02.txt")
    optimal = solve(world, ALGORITHMS["a*"])
    greedy = solve(world, ALGORITHMS["weighted a* (w=10)"])
    assert greedy.cost >= optimal.cost


def test_an_unreachable_goal_is_reported_rather_than_hung():
    # A rank-1 orak in a 1-wide corridor seals it off.
    world = empty_world(rows=3, columns=1, start=(0, 0), goal=(2, 0), oraks=(Orak(1, 0, 1),))
    assert not breadth_first(world, State(world.start), {world.goal}, Counter())


@pytest.mark.parametrize("name", sorted(ALGORITHMS))
def test_every_algorithm_completes_the_published_scenarios(name):
    world = parse(SCENARIOS / "test_02.txt")
    result = solve(world, ALGORITHMS[name])
    assert result.complete
    assert result.cost in (34, 36)  # 34 optimal; 36 for the greediest weighting


def test_the_mission_visits_every_helper():
    world = parse(SCENARIOS / "test_02.txt")
    assert solve(world, ALGORITHMS["bfs"]).cost == 34
