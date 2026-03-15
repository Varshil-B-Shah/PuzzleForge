import sqlite3

_DB_PATH = "puzzleforge.db"


def init_db(db_path: str = "puzzleforge.db") -> None:
    global _DB_PATH
    _DB_PATH = db_path
    conn = sqlite3.connect(_DB_PATH)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS game_history (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id         TEXT NOT NULL,
            game_number     INTEGER NOT NULL,
            pgn             TEXT,
            result          TEXT,
            duration_moves  INTEGER,
            level3_snapshot TEXT,
            played_at       DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS level2_scouting (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id     TEXT NOT NULL,
            game_number INTEGER NOT NULL,
            result      TEXT,
            report_text TEXT,
            created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS level3_profile (
            id               INTEGER PRIMARY KEY,
            style_name       TEXT,
            style_class      TEXT,
            full_profile     TEXT,
            counter_strategy TEXT,
            target_win_rate  REAL,
            games_analyzed   INTEGER,
            last_updated     DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    conn.close()


def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(_DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def save_game(game_id, game_number, pgn, result, duration_moves, level3_snapshot):
    with _conn() as c:
        c.execute(
            "INSERT INTO game_history (game_id,game_number,pgn,result,duration_moves,level3_snapshot) VALUES (?,?,?,?,?,?)",
            (game_id, game_number, pgn, result, duration_moves, level3_snapshot)
        )


def get_game_count() -> int:
    with _conn() as c:
        return c.execute("SELECT COUNT(*) FROM game_history").fetchone()[0]


def get_game_history() -> list[dict]:
    with _conn() as c:
        return [dict(r) for r in c.execute("SELECT * FROM game_history ORDER BY played_at ASC").fetchall()]


def save_level2_report(game_id, game_number, result, report_text):
    with _conn() as c:
        c.execute(
            "INSERT INTO level2_scouting (game_id,game_number,result,report_text) VALUES (?,?,?,?)",
            (game_id, game_number, result, report_text)
        )


def get_latest_level2_report() -> str | None:
    with _conn() as c:
        r = c.execute("SELECT report_text FROM level2_scouting ORDER BY id DESC LIMIT 1").fetchone()
        return r[0] if r else None


def get_level2_reports(n: int) -> list[str]:
    with _conn() as c:
        rows = c.execute("SELECT report_text FROM level2_scouting ORDER BY id DESC LIMIT ?", (n,)).fetchall()
        return [r[0] for r in rows]


def get_level3_profile() -> dict | None:
    with _conn() as c:
        r = c.execute("SELECT * FROM level3_profile WHERE id = 1").fetchone()
        return dict(r) if r else None


def save_level3_profile(style_name, style_class, full_profile, counter_strategy, target_win_rate, games_analyzed):
    with _conn() as c:
        c.execute(
            "INSERT OR REPLACE INTO level3_profile (id,style_name,style_class,full_profile,counter_strategy,target_win_rate,games_analyzed,last_updated) VALUES (1,?,?,?,?,?,?,CURRENT_TIMESTAMP)",
            (style_name, style_class, full_profile, counter_strategy, target_win_rate, games_analyzed)
        )


def reset_db() -> None:
    """Drop and recreate all tables. Called by the UI reset button."""
    with _conn() as c:
        c.executescript("""
            DROP TABLE IF EXISTS game_history;
            DROP TABLE IF EXISTS level2_scouting;
            DROP TABLE IF EXISTS level3_profile;
        """)
    init_db(_DB_PATH)
