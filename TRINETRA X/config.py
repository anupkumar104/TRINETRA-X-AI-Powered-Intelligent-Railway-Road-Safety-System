from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

DATABASE_PATH = BASE_DIR / "database" / "safety_system.db"

SNAPSHOT_DIR = BASE_DIR / "snapshots"
VIDEO_DIR = BASE_DIR / "videos"
MODEL_DIR = BASE_DIR / "models"

DEFAULT_MODE = "railway"

CONFIDENCE_THRESHOLD = 0.40

ALERT_COOLDOWN_SECONDS = 10

EVENT_TIME_WINDOW_SECONDS = 15