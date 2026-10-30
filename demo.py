"""Smoke test: load schema, seed words, run a review cycle and a mock test."""
import sqlite3, random
from datetime import date
from sm2 import CardState, review, quality_from_answer
from quizgen import build_mock_test

db = sqlite3.connect(":memory:")
db.row_factory = sqlite3.Row
db.executescript(open("schema.sql").read())

db.execute("INSERT INTO users(email, password_hash) VALUES ('a@b.com','x')")
db.execute("INSERT INTO tracks(name) VALUES ('Job exams'), ('MBA admission')")
seed = [
 ("ephemeral","adjective","lasting a very short time","Fame can be ephemeral.","transient,fleeting"),
 ("candid","adjective","honest and straightforward","She gave a candid opinion.","frank,open"),
 ("mitigate","verb","make less severe","Trees mitigate urban heat.","alleviate,reduce"),
 ("pragmatic","adjective","practical rather than ideal","A pragmatic approach works best.","practical,realistic"),
 ("scrutinize","verb","examine closely","Auditors scrutinize every record.","inspect,examine"),
 ("lucid","adjective","clearly expressed","His lucid explanation helped.","clear,coherent"),
]
for lemma, pos, meaning, ex, syn in seed:
    cur = db.execute("INSERT INTO words(lemma,part_of_speech,meaning,example,synonyms) VALUES (?,?,?,?,?)",
                     (lemma,pos,meaning,ex,syn))
    db.execute("INSERT INTO word_tracks VALUES (?,1,1)", (cur.lastrowid,))

# SM-2 cycle for one word
s = CardState()
for correct, ms in [(True, 3000), (True, 5000), (True, 6000), (False, 9000), (True, 4000)]:
    s = review(s, quality_from_answer(correct, ms), today=date(2026, 11, 1))
    print(f"correct={correct!s:5} -> reps={s.repetitions} interval={s.interval_days}d ef={s.ease_factor:.2f}")

# Mock test
rows = [dict(r) | {"priority": 1} for r in db.execute("SELECT * FROM words")]
for i, q in enumerate(build_mock_test(rows, rows, n=4, rng=random.Random(1)), 1):
    print(f"\nQ{i} [{q['type']}] {q['prompt']}")
    for j, o in enumerate(q["options"]):
        print(f"   {'*' if j == q['answer'] else ' '} {o}")
