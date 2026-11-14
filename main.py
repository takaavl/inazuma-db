# Vercel FastAPI entrypoint. Initialize the selected database on cold start.
from app.db import init_db

init_db(reset=False)

from app.main import app
