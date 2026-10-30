"""Question generators and mock-test builder (works on sqlite3 rows / dicts)."""
import random
import re


def meaning_mcq(word: dict, pool: list[dict], n_options: int = 4, rng=random) -> dict:
    """'What does X mean?' with distractors from the same part of speech/type."""
    same = [w for w in pool if w["id"] != word["id"]
            and w.get("part_of_speech") == word.get("part_of_speech")
            and w.get("type") == word.get("type")]
    others = same if len(same) >= n_options - 1 else [w for w in pool if w["id"] != word["id"]]
    distractors = rng.sample(others, min(n_options - 1, len(others)))
    options = [word["meaning"]] + [d["meaning"] for d in distractors]
    rng.shuffle(options)
    return {"word_id": word["id"], "type": "meaning_mcq",
            "prompt": f"What does '{word['lemma']}' mean?",
            "options": options, "answer": options.index(word["meaning"])}


def synonym_mcq(word: dict, pool: list[dict], n_options: int = 4, rng=random):
    """Pick the synonym of X. Returns None if the word has no synonyms."""
    syns = [s.strip() for s in (word.get("synonyms") or "").split(",") if s.strip()]
    if not syns:
        return None
    correct = rng.choice(syns)
    banned = set(syns) | {word["lemma"]}
    candidates = [w["lemma"] for w in pool if w["lemma"] not in banned]
    distractors = rng.sample(candidates, min(n_options - 1, len(candidates)))
    options = [correct] + distractors
    rng.shuffle(options)
    return {"word_id": word["id"], "type": "synonym_mcq",
            "prompt": f"Choose the synonym of '{word['lemma']}'.",
            "options": options, "answer": options.index(correct)}


def fill_blank(word: dict, pool: list[dict], n_options: int = 4, rng=random):
    """Blank the word out of its example sentence. Returns None if it doesn't appear."""
    ex = word.get("example") or ""
    pattern = re.compile(re.escape(word["lemma"]), re.IGNORECASE)
    if not pattern.search(ex):
        return None
    sentence = pattern.sub("_____", ex, count=1)
    same = [w["lemma"] for w in pool if w["id"] != word["id"]
            and w.get("part_of_speech") == word.get("part_of_speech")]
    distractors = rng.sample(same, min(n_options - 1, len(same)))
    options = [word["lemma"]] + distractors
    rng.shuffle(options)
    return {"word_id": word["id"], "type": "fill_blank", "prompt": sentence,
            "options": options, "answer": options.index(word["lemma"])}


def build_mock_test(words: list[dict], pool: list[dict], n: int = 20, rng=random) -> list[dict]:
    """Mixed-format test, weighted to high-priority (priority 1) words."""
    weights = [{1: 3, 2: 2, 3: 1}.get(w.get("priority", 2), 2) for w in words]
    chosen, seen = [], set()
    while len(chosen) < min(n, len(words)):
        w = rng.choices(words, weights=weights, k=1)[0]
        if w["id"] not in seen:
            seen.add(w["id"]); chosen.append(w)
    generators = [meaning_mcq, synonym_mcq, fill_blank]
    questions = []
    for w in chosen:
        order = rng.sample(generators, len(generators))
        for g in order:
            q = g(w, pool, rng=rng)
            if q:
                questions.append(q); break
    return questions
