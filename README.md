# Harbor Trajectories

Interesting agent trajectories from Harbor computer use evaluations.

This repo is deployed to Vercel using a Blob-backed jobs archive so we can keep
large Harbor job data without hitting Vercel's serverless function bundle size
limit.

## How It Works

1. The app runs as a Python function at `api/index.py`.
2. Viewer UI assets are served from vendored Harbor static files in `vendor/`.
3. Job data is loaded from one of these sources, in order:
   - `JOBS_TAR_URL` environment variable (preferred)
   - `config/jobs_tar_url.txt` fallback
   - local `jobs/` folder (mainly local dev fallback)
4. On first request (cold start), the function downloads `jobs.tgz` from Blob,
   extracts it to `/tmp/harbor-jobs`, and serves data from there.

## Why This Setup

Vercel serverless functions have an unzipped size limit. Bundling `jobs/` (and
the full Harbor dependency tree) can exceed it. This setup avoids that by:

1. Excluding heavy local folders from deploy uploads via `.vercelignore`.
2. Loading data from Vercel Blob at runtime.
3. Vendoring only the Harbor viewer code/assets needed at runtime in `vendor/`.

## Repository Files Used In Deploy

- `api/index.py`: runtime entrypoint and Blob download/extract logic.
- `vercel.json`: rewrites all routes to Python function and includes `vendor/**`.
- `.vercelignore`: excludes `jobs/`, local `harbor/`, and local-only files.
- `scripts/upload-jobs-to-blob.sh`: uploads new jobs tarball and updates env vars.
- `config/jobs_tar_url.txt`: Blob URL fallback if env var is missing.

## Prerequisites

- Node + npm/bun (for local tooling if needed)
- Python 3.12+
- Vercel CLI (`npm i -g vercel`)
- Vercel account with project access

## One-Time Setup

1. Login to Vercel:

```bash
vercel login
```

2. Link this folder to your Vercel project:

```bash
vercel link
```

3. Create and link a Blob store to the project (only once):

```bash
vercel blob store add harbor-trajectories-jobs
```

When prompted, choose to link it to the project and select environments.

4. Pull env vars locally (script also does this when needed):

```bash
vercel env pull .env.vercel.local
```

5. Upload jobs data and set Blob URL env vars:

```bash
bash scripts/upload-jobs-to-blob.sh
```

This script does all of the following:

1. Tarballs `jobs/` to a temporary `.tgz`
2. Uploads it to Vercel Blob
3. Updates `config/jobs_tar_url.txt`
4. Sets `JOBS_TAR_URL` for production, preview, and development

6. Deploy:

```bash
vercel deploy --prod
```

## Updating Data Later

Any time `jobs/` changes, run:

```bash
bash scripts/upload-jobs-to-blob.sh
vercel deploy --prod
```

## Verify Deployment

Check these endpoints:

```bash
curl -s https://<your-domain>/api/health
curl -s https://<your-domain>/api/config
curl -s 'https://<your-domain>/api/jobs?page=1&page_size=1'
```

Expected:

1. `/api/health` returns `{"status":"ok"}`
2. `/api/config` shows jobs dir under `/tmp/harbor-jobs/...`
3. `/api/jobs` returns real jobs, not an empty list

## Troubleshooting

### "No jobs in /var/task/jobs"

Cause: deployment is not using Blob URL (wrong project/domain, missing env var,
or old commit).

Fix:

1. Confirm you are opening the correct deployment/project URL.
2. Run `bash scripts/upload-jobs-to-blob.sh`.
3. Redeploy: `vercel deploy --prod`.
4. Re-check `/api/config`.

### "Serverless Function exceeded 250 MB"

Cause: large files got included in deploy artifact.

Fix:

1. Ensure `.vercelignore` is present and includes `/jobs` and `/harbor`.
2. Keep `jobs/` in Blob only (do not include in function bundle).
3. Redeploy.

### Blob commands say token is missing

Fix:

1. Ensure Blob store is linked to the Vercel project.
2. Run `vercel env pull .env.vercel.local`.
3. Re-run upload script.

## Security Note

`.env.vercel.local` can contain secrets and is ignored via `.gitignore`.
Do not commit it.
