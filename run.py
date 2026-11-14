import uvicorn
from app.db import init_db

if __name__ == "__main__":
    init_db(reset=False)
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=False)
