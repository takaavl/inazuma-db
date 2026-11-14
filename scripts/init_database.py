from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.db import init_db, using_turso

if __name__ == "__main__":
    init_db(reset=False)
    print("INAZUMA database ready: Turso Cloud" if using_turso() else "INAZUMA database ready: data/inazuma.sqlite3")
