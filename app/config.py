from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "inazuma.sqlite3"
PROJECT_NAME = "INAZUMA"
TEAM_NAME = os.environ.get("TEAM_NAME", "Inazuma")
