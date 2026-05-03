from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

STATIC_DIR = BASE_DIR / "frontend" / "dist"

print("STATIC DIR:", STATIC_DIR)
print("EXISTS:", STATIC_DIR.exists())

app = Flask(
    __name__,
    static_folder=str(STATIC_DIR),
    static_url_path=""
)