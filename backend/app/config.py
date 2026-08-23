"""Application configuration loading.

Loads backend/.env from a deterministic path so server startup does not
depend on the shell's current working directory.
"""

from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[1]
ENV_PATH = BACKEND_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH, override=False)
