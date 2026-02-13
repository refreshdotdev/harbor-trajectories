"""Vercel Python entrypoint for Harbor Viewer."""

from __future__ import annotations

import importlib.metadata
import os
import shutil
import sys
import tarfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor"))

_real_version = importlib.metadata.version


def _safe_version(name: str) -> str:
    if name == "harbor":
        try:
            return _real_version(name)
        except importlib.metadata.PackageNotFoundError:
            return "0.1.44"
    return _real_version(name)


importlib.metadata.version = _safe_version

import harbor.viewer
from harbor.viewer.server import create_app

STATIC_DIR = Path(harbor.viewer.__file__).resolve().parent / "static"
CACHE_ROOT = Path("/tmp/harbor-jobs")
ARCHIVE_PATH = CACHE_ROOT / "jobs.tgz"
MARKER_PATH = CACHE_ROOT / ".source-url"
EXTRACT_DIR = CACHE_ROOT / "jobs"
FALLBACK_URL_PATH = ROOT / "config" / "jobs_tar_url.txt"


def _download_file(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=60) as response, destination.open(
        "wb"
    ) as out:
        shutil.copyfileobj(response, out)


def _safe_extract(tar: tarfile.TarFile, destination: Path) -> None:
    destination_abs = destination.resolve()
    for member in tar.getmembers():
        member_target = (destination / member.name).resolve()
        if destination_abs not in (member_target, *member_target.parents):
            raise RuntimeError(f"Refusing unsafe archive path: {member.name}")
    tar.extractall(destination)


def _prepare_jobs_dir() -> Path:
    jobs_tar_url = os.getenv("JOBS_TAR_URL", "").strip()
    if not jobs_tar_url and FALLBACK_URL_PATH.exists():
        jobs_tar_url = FALLBACK_URL_PATH.read_text().strip()
    if not jobs_tar_url:
        return ROOT / "jobs"

    marker = MARKER_PATH.read_text().strip() if MARKER_PATH.exists() else ""
    if marker == jobs_tar_url and EXTRACT_DIR.exists():
        nested_jobs_dir = EXTRACT_DIR / "jobs"
        return nested_jobs_dir if nested_jobs_dir.exists() else EXTRACT_DIR

    if EXTRACT_DIR.exists():
        shutil.rmtree(EXTRACT_DIR)

    tmp_archive = ARCHIVE_PATH.with_suffix(".download")
    _download_file(jobs_tar_url, tmp_archive)

    EXTRACT_DIR.mkdir(parents=True, exist_ok=True)
    with tarfile.open(tmp_archive, "r:*") as tar:
        _safe_extract(tar, EXTRACT_DIR)
    tmp_archive.replace(ARCHIVE_PATH)
    MARKER_PATH.write_text(jobs_tar_url)
    nested_jobs_dir = EXTRACT_DIR / "jobs"
    return nested_jobs_dir if nested_jobs_dir.exists() else EXTRACT_DIR


jobs_dir = _prepare_jobs_dir()

app = create_app(
    jobs_dir=jobs_dir,
    static_dir=STATIC_DIR if STATIC_DIR.exists() else None,
)
