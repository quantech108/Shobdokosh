"""SM-2 spaced repetition (the algorithm Anki's scheduler descends from)."""
from dataclasses import dataclass
from datetime import date, timedelta


@dataclass
class CardState:
    repetitions: int = 0
    interval_days: int = 0
    ease_factor: float = 2.5
    due_date: date = None


def quality_from_answer(correct: bool, response_ms: int | None = None,
                        fast_ms: int = 4000, slow_ms: int = 12000) -> int:
    """Map an objective quiz result to SM-2's 0-5 quality scale.
    Wrong -> 1. Right -> 5 if fast, 4 if normal, 3 if slow (recalled with effort)."""
    if not correct:
        return 1
    if response_ms is None:
        return 4
    if response_ms <= fast_ms:
        return 5
    if response_ms >= slow_ms:
        return 3
    return 4


def review(state: CardState, quality: int, today: date | None = None) -> CardState:
    """Return the new state after one review. quality: 0-5."""
    if not 0 <= quality <= 5:
        raise ValueError("quality must be 0..5")
    today = today or date.today()

    reps, interval, ef = state.repetitions, state.interval_days, state.ease_factor

    if quality < 3:                      # failed: restart, see it again tomorrow
        reps, interval = 0, 1
    else:
        if reps == 0:
            interval = 1
        elif reps == 1:
            interval = 6
        else:
            interval = round(interval * ef)
        reps += 1

    ef = max(1.3, ef + 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))

    return CardState(reps, interval, ef, today + timedelta(days=interval))


def cram_due(state: CardState, exam_date: date, today: date | None = None) -> bool:
    """Cram mode: ignore long intervals; a word is 'due' if its next review
    would land after the exam, so it must be shown now."""
    today = today or date.today()
    return state.due_date is None or state.due_date <= today or state.due_date > exam_date
