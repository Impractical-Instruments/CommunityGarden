"""Tests for _LevelBag, the ADR-0013 difficulty rule: same or +1, fall back to all."""
from __future__ import annotations

import pytest

from games.bodycaptcha import _LevelBag


def lv(name: str, difficulty: int) -> dict:
    return {"prompt": name, "difficulty": difficulty}


LEVELS = [lv("a1", 1), lv("b1", 1), lv("a2", 2), lv("a3", 3), lv("a4", 4), lv("a5", 5)]


def drawn(bag: _LevelBag, n: int, beat: int | None = None) -> list[dict]:
    first = bag.next(beat)
    return [first] + [bag.next() for _ in range(n - 1)]


def test_first_draw_comes_from_difficulty_one_or_two() -> None:
    for _ in range(30):
        bag = _LevelBag(LEVELS)
        assert bag.next()["difficulty"] in (1, 2)


def test_a_bag_is_emptied_before_it_refills() -> None:
    bag = _LevelBag(LEVELS)
    eligible = {"a1", "b1", "a2"}
    first_pass = [bag.next()["prompt"] for _ in range(3)]
    assert sorted(first_pass) == sorted(eligible)


def test_beating_a_level_moves_to_that_difficulty_plus_one() -> None:
    for _ in range(30):
        bag = _LevelBag(LEVELS)
        assert bag.next(beat_difficulty=2)["difficulty"] in (3, 4)


def test_beating_a_level_discards_the_old_bag() -> None:
    bag = _LevelBag(LEVELS)
    bag.next()                       # leaves the d1/d2 bag part-full
    assert bag.next(beat_difficulty=3)["difficulty"] in (4, 5)


def test_difficulty_is_capped_at_five() -> None:
    bag = _LevelBag(LEVELS)
    # beat 5 -> min(6, 5) = 5 -> eligible 5 or 6 -> only the d5 level
    assert bag.next(beat_difficulty=5)["prompt"] == "a5"


def test_falls_back_to_every_level_when_none_is_eligible() -> None:
    only_easy = [lv("x", 1), lv("y", 1)]
    bag = _LevelBag(only_easy)
    got = bag.next(beat_difficulty=4)       # wants 5 or 6; none exist
    assert got in only_easy
    assert {bag.next()["prompt"]} <= {"x", "y"}


def test_reset_returns_to_difficulty_one() -> None:
    bag = _LevelBag(LEVELS)
    for _ in range(30):
        bag.next(beat_difficulty=4)
        bag.reset()
        assert bag.next()["difficulty"] in (1, 2)


def test_level_without_difficulty_counts_as_one() -> None:
    bag = _LevelBag([{"prompt": "none"}, lv("hard", 5)])
    assert bag.next()["prompt"] == "none"


def test_bag_cycles_through_a_single_level() -> None:
    bag = _LevelBag([lv("only", 1)])
    assert [bag.next()["prompt"] for _ in range(4)] == ["only"] * 4
