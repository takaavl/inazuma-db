from __future__ import annotations

import json
import shutil
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.db import init_db, connect
from app.analytics import upsert_map_caches

DB = ROOT / "data" / "inazuma.sqlite3"
FULL = ROOT / "data" / "private_full.sqlite3"
PRIVATE_RAW = ROOT / "data" / "private_raw"


def _valid_raw(raw_text: str | None) -> bool:
    if not raw_text:
        return False
    try:
        obj = json.loads(raw_text)
        return isinstance(obj, dict) and isinstance(obj.get("data", {}).get("segments"), list)
    except Exception:
        return False


def _raw_from_private_raw(match_id, source_path=None):
    """New admin imports are archived by match_id in data/private_raw/.

    The compact public DB strips raw_json on prepare, while private_full.sqlite3
    is only the original historical archive and does not contain later imports.
    """
    candidates = []
    if match_id:
        safe_match_id = str(match_id).strip()
        if safe_match_id and Path(safe_match_id).name == safe_match_id:
            candidates.append(PRIVATE_RAW / f"{safe_match_id}.json")
    if source_path:
        source_name = Path(str(source_path)).name
        if source_name and source_name not in {p.name for p in candidates}:
            candidates.append(PRIVATE_RAW / source_name)
    for path in candidates:
        try:
            raw_text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
        if _valid_raw(raw_text):
            return raw_text
    return None


def _raw_from_full(full_con, map_id, match_id):
    if full_con is None:
        return None
    # Match by Tracker ID first. A row-ID fallback is allowed only when its
    # Tracker ID agrees (or the legacy archive has no Tracker ID), so a newly
    # imported map can never accidentally inherit an unrelated historical board.
    if match_id:
        try:
            row = full_con.execute(
                "SELECT raw_json FROM maps WHERE match_id=?", (str(match_id),)
            ).fetchone()
        except sqlite3.Error:
            row = None
        if row and _valid_raw(row["raw_json"]):
            return row["raw_json"]
    try:
        row = full_con.execute(
            "SELECT match_id,raw_json FROM maps WHERE id=?", (map_id,)
        ).fetchone()
    except sqlite3.Error:
        row = None
    if row and (not match_id or not row["match_id"] or str(row["match_id"]) == str(match_id)):
        if _valid_raw(row["raw_json"]):
            return row["raw_json"]
    return None


def _cache_needs_rebuild(con, map_id):
    cache_count = con.execute(
        "SELECT (SELECT COUNT(*) FROM map_team_insights_cache WHERE map_id=?) + "
        "(SELECT COUNT(*) FROM map_leaderboard_cache WHERE map_id=?)",
        (map_id, map_id),
    ).fetchone()[0]
    leaderboard_row = con.execute(
        "SELECT payload_json FROM map_leaderboard_cache WHERE map_id=?", (map_id,)
    ).fetchone()
    player_count = con.execute(
        "SELECT COUNT(*) FROM player_map_stats WHERE map_id=?", (map_id,)
    ).fetchone()[0]
    try:
        leaderboard_payload = json.loads(leaderboard_row["payload_json"]) if leaderboard_row else None
    except Exception:
        leaderboard_payload = None
    # A blank leaderboard with stored player stats is the known signature of the
    # old prepare-deploy bug. If a map has no stored player stats, an empty board
    # can be legitimate (manual-result/partial data).
    cache_is_valid = cache_count == 2 and (bool(leaderboard_payload) or player_count == 0)
    return not cache_is_valid


def main():
    init_db(reset=False)
    full_con = None
    if FULL.exists():
        full_con = sqlite3.connect(FULL)
        full_con.row_factory = sqlite3.Row

    recovered_private_raw = 0
    recovered_private_full = 0
    unresolved = []
    rebuilt_from_current_raw = 0
    try:
        with connect() as con:
            maps = con.execute("SELECT id,match_id,source_path,raw_json,team_id FROM maps").fetchall()
            for m in maps:
                raw_json = m["raw_json"] or ""
                should_rebuild = _cache_needs_rebuild(con, m["id"])

                # Raw JSON still present in the working DB is the preferred source,
                # but never treat malformed JSON as a valid source for rebuilding.
                if _valid_raw(raw_json):
                    rebuilt_from_current_raw += int(should_rebuild)
                else:
                    raw_json = ""
                    # If caches are already good, preserve them. This avoids touching
                    # historical scoreboards on every deploy.
                    if not should_rebuild:
                        continue

                    # New admin-imported maps are stored here; they are NOT copied into
                    # private_full.sqlite3 after its initial creation.
                    archived_raw = _raw_from_private_raw(m["match_id"], m["source_path"])
                    if archived_raw:
                        raw_json = archived_raw
                        recovered_private_raw += 1
                    else:
                        archived_raw = _raw_from_full(full_con, m["id"], m["match_id"])
                        if archived_raw:
                            raw_json = archived_raw
                            recovered_private_full += 1

                    if not raw_json:
                        unresolved.append({"map_id": m["id"], "match_id": m["match_id"], "source_path": m["source_path"]})
                        # Never overwrite a cache with zeros/[] when no source exists.
                        continue

                canonical = {
                    r["account_riot_id"]: r["canonical_name"]
                    for r in con.execute(
                        """SELECT pms.account_riot_id,p.canonical_name
                           FROM player_map_stats pms
                           JOIN players p ON p.id=pms.player_id
                           WHERE pms.map_id=?""",
                        (m["id"],),
                    ).fetchall()
                }
                upsert_map_caches(con, m["id"], raw_json, m["team_id"], canonical)
    finally:
        if full_con is not None:
            full_con.close()

    # Keep the original historical full/raw archive once it exists.
    if not FULL.exists():
        shutil.copy2(DB, FULL)

    with sqlite3.connect(DB) as con:
        con.execute("UPDATE maps SET raw_json='' WHERE raw_json<>''")
        con.commit()
        con.execute("VACUUM")

    print(json.dumps({
        "public_db_mb": round(DB.stat().st_size / 1024 / 1024, 2),
        "private_full_db_mb": round(FULL.stat().st_size / 1024 / 1024, 2),
        "rebuilt_from_current_raw": rebuilt_from_current_raw,
        "recovered_from_private_raw": recovered_private_raw,
        "recovered_from_private_full": recovered_private_full,
        "unresolved_scoreboards": unresolved,
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
