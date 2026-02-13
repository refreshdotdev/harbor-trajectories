"""Vercel Python entrypoint for Harbor Viewer."""

from pathlib import Path

import harbor.viewer
from harbor.viewer.server import create_app

ROOT = Path(__file__).resolve().parents[1]
STATIC_DIR = Path(harbor.viewer.__file__).resolve().parent / "static"

app = create_app(
    jobs_dir=ROOT / "jobs",
    static_dir=STATIC_DIR if STATIC_DIR.exists() else None,
)
