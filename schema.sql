-- Vocabulary system MVP schema (SQLite; works on PostgreSQL with minor type changes)
PRAGMA foreign_keys = ON;

CREATE TABLE users (
    id            INTEGER PRIMARY KEY,
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Exam tracks: bank/govt jobs, MBA admission, IELTS, GRE-type, etc.
CREATE TABLE tracks (
    id    INTEGER PRIMARY KEY,
    name  TEXT NOT NULL UNIQUE,
    notes TEXT
);

CREATE TABLE words (
    id            INTEGER PRIMARY KEY,
    lemma         TEXT NOT NULL,
    type          TEXT NOT NULL DEFAULT 'word'
                  CHECK (type IN ('word','idiom','phrase','one_word_substitution')),
    part_of_speech TEXT,
    meaning       TEXT NOT NULL,
    example       TEXT,
    synonyms      TEXT,              -- comma-separated for MVP; normalize later
    antonyms      TEXT,
    source        TEXT,              -- e.g. 'past paper 2023', 'public list'
    UNIQUE (lemma, type)
);

-- A word can belong to several tracks, with a different priority in each.
CREATE TABLE word_tracks (
    word_id  INTEGER NOT NULL REFERENCES words(id) ON DELETE CASCADE,
    track_id INTEGER NOT NULL REFERENCES tracks(id) ON DELETE CASCADE,
    priority INTEGER NOT NULL DEFAULT 2 CHECK (priority IN (1,2,3)), -- 1=commonly asked
    PRIMARY KEY (word_id, track_id)
);

-- Per-user SM-2 state for each word
CREATE TABLE user_words (
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    word_id     INTEGER NOT NULL REFERENCES words(id) ON DELETE CASCADE,
    repetitions INTEGER NOT NULL DEFAULT 0,
    interval_days INTEGER NOT NULL DEFAULT 0,
    ease_factor REAL    NOT NULL DEFAULT 2.5,
    due_date    TEXT    NOT NULL DEFAULT (date('now')),
    last_reviewed TEXT,
    PRIMARY KEY (user_id, word_id)
);
CREATE INDEX idx_user_words_due ON user_words(user_id, due_date);

-- Every answer is logged: this is your data for future smart features.
CREATE TABLE review_logs (
    id          INTEGER PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    word_id     INTEGER NOT NULL REFERENCES words(id) ON DELETE CASCADE,
    question_type TEXT NOT NULL,      -- 'flashcard','meaning_mcq','synonym_mcq','fill_blank'
    correct     INTEGER NOT NULL CHECK (correct IN (0,1)),
    quality     INTEGER NOT NULL CHECK (quality BETWEEN 0 AND 5),
    response_ms INTEGER,
    reviewed_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_review_logs_user_time ON review_logs(user_id, reviewed_at);

-- Timed mock tests
CREATE TABLE tests (
    id          INTEGER PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    track_id    INTEGER REFERENCES tracks(id),
    n_questions INTEGER NOT NULL,
    score       INTEGER,
    duration_s  INTEGER,
    taken_at    TEXT NOT NULL DEFAULT (datetime('now'))
);
