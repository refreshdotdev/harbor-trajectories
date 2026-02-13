"""Vercel Python entrypoint for Harbor Viewer."""

import importlib.metadata
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "harbor" / "src"))

_real_version = importlib.metadata.version


def _safe_version(name: str) -> str:
    """Fallback when local source tree is not an installed package."""
    if name == "harbor":
        try:
            return _real_version(name)
        except importlib.metadata.PackageNotFoundError:
            return "0.0.0"
    return _real_version(name)


importlib.metadata.version = _safe_version

from harbor.viewer.server import create_app

app = create_app(
    jobs_dir=ROOT / "jobs",
    static_dir=ROOT / "harbor" / "viewer" / "build" / "client",
)
