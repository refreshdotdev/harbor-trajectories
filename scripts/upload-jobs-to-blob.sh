#!/usr/bin/env bash
set -euo pipefail

# Packages ./jobs into a tarball, uploads it to Vercel Blob, and updates
# JOBS_TAR_URL for production/preview/development in the linked project.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if ! command -v vercel >/dev/null 2>&1; then
  echo "Error: vercel CLI is required." >&2
  exit 1
fi

if [ ! -f ".vercel/project.json" ]; then
  echo "Error: repo is not linked to a Vercel project. Run: vercel link" >&2
  exit 1
fi

if [ ! -d "jobs" ]; then
  echo "Error: jobs/ directory not found." >&2
  exit 1
fi

if [ -z "${BLOB_READ_WRITE_TOKEN:-}" ]; then
  if [ ! -f ".env.vercel.local" ]; then
    vercel env pull .env.vercel.local >/dev/null
  fi
  if [ -f ".env.vercel.local" ]; then
    BLOB_READ_WRITE_TOKEN="$(
      grep '^BLOB_READ_WRITE_TOKEN=' .env.vercel.local \
        | head -n 1 \
        | cut -d '=' -f 2- \
        | sed 's/^"//; s/"$//'
    )"
    export BLOB_READ_WRITE_TOKEN
  fi
fi

if [ -z "${BLOB_READ_WRITE_TOKEN:-}" ]; then
  echo "Error: BLOB_READ_WRITE_TOKEN not found." >&2
  echo "Link a Blob store and run: vercel env pull .env.vercel.local" >&2
  exit 1
fi

tmp_base="$(mktemp /tmp/jobs-XXXXXX)"
tmp_tgz="${tmp_base}.tgz"
mv "$tmp_base" "$tmp_tgz"
trap 'rm -f "$tmp_tgz"' EXIT

echo "Creating jobs archive..."
tar -czf "$tmp_tgz" jobs

echo "Uploading archive to Vercel Blob..."
blob_output="$(
  vercel blob put "$tmp_tgz" \
    --rw-token "$BLOB_READ_WRITE_TOKEN" \
    --add-random-suffix true \
    --pathname jobs/jobs.tgz \
    2>&1
)"
blob_url="$(printf '%s\n' "$blob_output" | grep -Eo 'https://[^[:space:]]+' | tail -n 1 | tr -d '\r')"

if ! printf '%s' "$blob_url" | grep -qE '^https?://'; then
  echo "Error: could not parse Blob URL from output:" >&2
  echo "$blob_output" >&2
  exit 1
fi

echo "Blob URL: $blob_url"
echo

echo "Updating JOBS_TAR_URL env var on Vercel..."
for env in production preview development; do
  printf '%s' "$blob_url" | vercel env add JOBS_TAR_URL "$env" --yes --force >/dev/null
done

echo "Done. JOBS_TAR_URL updated for production/preview/development."
