from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[1]

# Local development can use the same Turso database as Vercel by placing
# TURSO_DATABASE_URL and TURSO_AUTH_TOKEN in a private .env file.
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    pass

DATA_DIR = ROOT / "data"
# Vercel's function filesystem is ephemeral/read-only. This is only a temporary
# fallback for the initial deployment before Turso Cloud is connected.
DB_PATH = Path("/tmp/inazuma.sqlite3") if os.getenv("VERCEL") else DATA_DIR / "inazuma.sqlite3"
PROJECT_NAME = "INAZUMA"
TEAM_NAME = os.environ.get("TEAM_NAME", "Inazuma")
