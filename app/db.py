from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from .config import DB_PATH

SCHEMA = r'''
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS players (
    id INTEGER PRIMARY KEY,
    slug TEXT NOT NULL UNIQUE,
    canonical_name TEXT NOT NULL UNIQUE,
    role TEXT,
    display_order INTEGER NOT NULL DEFAULT 100,
    roster_status TEXT NOT NULL CHECK(roster_status IN ('main','recurring_sub','former_sub','wel_sub','occasional_sub')),
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS player_aliases (
    id INTEGER PRIMARY KEY,
    player_id INTEGER NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    riot_id TEXT NOT NULL UNIQUE,
    alias_type TEXT NOT NULL DEFAULT 'own_account',
    note TEXT
);
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY,
    slug TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    competition TEXT NOT NULL,
    tier TEXT NOT NULL DEFAULT 'C' CHECK(tier IN ('S','A','B','C')),
    event_notes TEXT,
    placement_text TEXT,
    first_date TEXT,
    last_date TEXT
);
CREATE TABLE IF NOT EXISTS series (
    id INTEGER PRIMARY KEY,
    event_id INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    series_key TEXT NOT NULL UNIQUE,
    stage TEXT,
    opponent TEXT NOT NULL,
    played_at TEXT,
    best_of INTEGER NOT NULL DEFAULT 1,
    maps_won INTEGER NOT NULL DEFAULT 0,
    maps_lost INTEGER NOT NULL DEFAULT 0,
    result TEXT CHECK(result IN ('W','L','D','N/A')),
    roster_category TEXT,
    is_bye INTEGER NOT NULL DEFAULT 0,
    bye_result TEXT,
    notes TEXT,
    career_highlight INTEGER NOT NULL DEFAULT 0,
    highlight_note TEXT
);
CREATE TABLE IF NOT EXISTS maps (
    id INTEGER PRIMARY KEY,
    series_id INTEGER NOT NULL REFERENCES series(id) ON DELETE CASCADE,
    match_id TEXT UNIQUE,
    map_index INTEGER NOT NULL DEFAULT 1,
    map_name TEXT NOT NULL,
    map_image_url TEXT,
    played_at TEXT,
    duration_ms INTEGER,
    raw_rounds INTEGER,
    official_rounds INTEGER,
    team_id TEXT,
    start_side TEXT,
    score_for INTEGER NOT NULL,
    score_against INTEGER NOT NULL,
    result TEXT NOT NULL CHECK(result IN ('W','L','D')),
    roster_category TEXT NOT NULL,
    composition_key TEXT,
    data_quality TEXT NOT NULL DEFAULT 'complete' CHECK(data_quality IN ('complete','partial','manual_result')),
    stats_complete INTEGER NOT NULL DEFAULT 1,
    source_path TEXT NOT NULL UNIQUE,
    raw_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS map_pistols (
    map_id INTEGER PRIMARY KEY REFERENCES maps(id) ON DELETE CASCADE,
    pistol_wins INTEGER NOT NULL DEFAULT 0,
    pistol_played INTEGER NOT NULL DEFAULT 0,
    attack_wins INTEGER NOT NULL DEFAULT 0,
    attack_played INTEGER NOT NULL DEFAULT 0,
    defense_wins INTEGER NOT NULL DEFAULT 0,
    defense_played INTEGER NOT NULL DEFAULT 0,
    conversion_wins INTEGER NOT NULL DEFAULT 0,
    conversion_opportunities INTEGER NOT NULL DEFAULT 0,
    first_half_result TEXT,
    second_half_result TEXT
);
CREATE TABLE IF NOT EXISTS player_map_stats (
    id INTEGER PRIMARY KEY,
    map_id INTEGER NOT NULL REFERENCES maps(id) ON DELETE CASCADE,
    player_id INTEGER NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    account_riot_id TEXT NOT NULL,
    agent TEXT,
    agent_image_url TEXT,
    agent_portrait_url TEXT,
    rank TEXT,
    rank_tier_id INTEGER,
    kills INTEGER,
    deaths INTEGER,
    assists INTEGER,
    kd REAL,
    acs REAL,
    adr REAL,
    kast REAL,
    first_kills INTEGER,
    first_deaths INTEGER,
    damage_delta_per_round REAL,
    headshot_pct REAL,
    plants INTEGER,
    defuses INTEGER,
    UNIQUE(map_id, player_id)
);
CREATE TABLE IF NOT EXISTS substitutions (
    id INTEGER PRIMARY KEY,
    map_id INTEGER NOT NULL REFERENCES maps(id) ON DELETE CASCADE,
    sub_player_id INTEGER NOT NULL REFERENCES players(id),
    replaced_player_id INTEGER REFERENCES players(id),
    confidence TEXT NOT NULL CHECK(confidence IN ('exact','ambiguous')),
    note TEXT
);
CREATE TABLE IF NOT EXISTS map_team_insights_cache (
    map_id INTEGER PRIMARY KEY REFERENCES maps(id) ON DELETE CASCADE,
    payload_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS map_leaderboard_cache (
    map_id INTEGER PRIMARY KEY REFERENCES maps(id) ON DELETE CASCADE,
    payload_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS data_issues (
    id INTEGER PRIMARY KEY,
    severity TEXT NOT NULL CHECK(severity IN ('info','warning','error')),
    issue_type TEXT NOT NULL,
    source_path TEXT,
    message TEXT NOT NULL,
    resolved INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_maps_played_at ON maps(played_at);
CREATE INDEX IF NOT EXISTS idx_maps_roster_category ON maps(roster_category);
CREATE INDEX IF NOT EXISTS idx_series_played_at ON series(played_at);
CREATE INDEX IF NOT EXISTS idx_series_roster_category ON series(roster_category);
CREATE INDEX IF NOT EXISTS idx_pms_player ON player_map_stats(player_id);
CREATE INDEX IF NOT EXISTS idx_pms_map ON player_map_stats(map_id);
'''


class CompatRow(dict):
    """sqlite3.Row-like mapping for rows returned by the remote libSQL driver."""
    def __init__(self, columns, values):
        super().__init__(zip(columns, values))
        self._values = tuple(values)

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._values[key]
        return super().__getitem__(key)


class CompatCursor:
    def __init__(self, cursor):
        self._cursor = cursor

    @property
    def description(self):
        return self._cursor.description

    def _columns(self):
        return [d[0] for d in (self._cursor.description or [])]

    def _row(self, row):
        if row is None:
            return None
        if isinstance(row, sqlite3.Row):
            return row
        return CompatRow(self._columns(), row)

    def fetchone(self):
        return self._row(self._cursor.fetchone())

    def fetchall(self):
        return [self._row(row) for row in self._cursor.fetchall()]

    def __iter__(self):
        # libsql cursors may not implement sqlite3's iterator protocol.
        while True:
            row = self.fetchone()
            if row is None:
                break
            yield row


class RemoteConnection:
    """Small sqlite3-compatible adapter around the libsql Turso client."""
    def __init__(self, connection):
        self._connection = connection

    def execute(self, sql, params=()):
        return CompatCursor(self._connection.execute(sql, params))

    def executescript(self, script):
        # This schema has no trigger bodies, so semicolon splitting is safe.
        for statement in script.split(";"):
            statement = statement.strip()
            if statement:
                self._connection.execute(statement)
        return self

    def commit(self):
        return self._connection.commit()

    def rollback(self):
        try:
            return self._connection.rollback()
        except AttributeError:
            return None

    def close(self):
        return self._connection.close()


def using_turso() -> bool:
    return bool(os.getenv("TURSO_DATABASE_URL"))


def _connect_turso():
    url = os.getenv("TURSO_DATABASE_URL")
    token = os.getenv("TURSO_AUTH_TOKEN")
    if not token:
        raise RuntimeError("TURSO_DATABASE_URL is set but TURSO_AUTH_TOKEN is missing.")
    try:
        import libsql
    except ImportError as exc:
        raise RuntimeError("Turso mode requires the 'libsql' package. Install requirements.txt.") from exc
    connection = libsql.connect(database=url, auth_token=token)
    connection.execute("PRAGMA foreign_keys = ON")
    return RemoteConnection(connection)


@contextmanager
def connect():
    """Use Turso Cloud when configured; otherwise use the local SQLite file."""
    if using_turso():
        con = _connect_turso()
    else:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        con = sqlite3.connect(DB_PATH)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys = ON")
    try:
        yield con
        con.commit()
    except Exception:
        try:
            con.rollback()
        finally:
            raise
    finally:
        con.close()


INITIAL_ROSTER = [
    ("takaa", "Takaa", "Duelist", 1),
    ("duke", "Duke", "Recon", 2),
    ("tempokd", "TempoKD", "Duelist", 3),
    ("ljph", "LJPH", "IGL / Controller", 4),
    ("lugia", "Lugia", "Sentinel", 5),
]


def seed_initial_roster(con):
    """Add the confirmed starting five without overwriting later admin edits."""
    for slug, name, role, order in INITIAL_ROSTER:
        con.execute(
            """INSERT OR IGNORE INTO players
               (slug, canonical_name, role, display_order, roster_status, active)
               VALUES (?, ?, ?, ?, 'main', 1)""",
            (slug, name, role, order),
        )


def init_db(reset=False):
    """Initialize local SQLite or bootstrap an empty remote Turso database."""
    if reset and using_turso():
        raise RuntimeError("Refusing to reset the remote Turso database from this local reset option.")
    if reset and DB_PATH.exists():
        DB_PATH.unlink()
    if not using_turso():
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with connect() as con:
        if using_turso():
            # Avoid replaying the full remote schema on every Vercel cold start,
            # but safely finish setup if a previous bootstrap was interrupted.
            expected = {
                "players", "player_aliases", "events", "series", "maps",
                "map_pistols", "player_map_stats", "substitutions",
                "map_team_insights_cache", "map_leaderboard_cache", "data_issues",
            }
            existing = {
                row[0] for row in con.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }
            if not expected.issubset(existing):
                con.executescript(SCHEMA)
        else:
            con.executescript(SCHEMA)
        seed_initial_roster(con)
