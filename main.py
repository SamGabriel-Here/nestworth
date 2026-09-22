"""Entry point: `python main.py` serves the app on http://localhost:7860."""

import os

import uvicorn

from src.api.app import app

if __name__ == "__main__":
    # Pass the app object, not "src.api.app:app": the string form hangs on HF Spaces.
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 7860)))
