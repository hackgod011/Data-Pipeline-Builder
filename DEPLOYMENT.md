# 🌍 Free Deployment Guide (Render + Vercel)

Deploy PipeForge live for **$0** with automatic CI/CD — every `git push` to `main`
redeploys both the backend and the frontend. No credit card required on either platform.

| Piece | Platform | Free-tier behavior |
|---|---|---|
| FastAPI backend (Docker) | [Render](https://render.com) | Sleeps after 15 min idle; **auto-wakes in ~50s** on the next visit |
| React frontend (static) | [Vercel](https://vercel.com) | Always on, 24×7, global CDN |

---

## Step 0 — Push the deployment configs

Make sure `render.yaml` (repo root) and `frontend/vercel.json` are committed and pushed to GitHub.

## Step 1 — Deploy the backend on Render

1. Go to [render.com](https://render.com) → **Sign up with GitHub** (free, no card).
2. Click **New → Blueprint** and select the `Data-Pipeline-Builder` repo.
3. Render reads `render.yaml` and asks for the three secrets it can't guess:
   - `GROQ_API_KEY` — your key from [console.groq.com](https://console.groq.com) (free)
   - `ENCRYPTION_KEY` — generate locally:
     `python -c "import secrets, base64; print(base64.b64encode(secrets.token_bytes(32)).decode())"`
   - `CORS_ORIGINS` — put a placeholder for now (e.g. `http://localhost:5173`); you'll update it in Step 3.
4. Click **Apply**. First build takes a few minutes.
5. Note your backend URL, e.g. `https://pipeforge-backend.onrender.com`.
   Verify: open `https://pipeforge-backend.onrender.com/health` — you should see a JSON response.

## Step 2 — Deploy the frontend on Vercel

1. Go to [vercel.com](https://vercel.com) → **Sign up with GitHub** (free Hobby plan).
2. **Add New → Project** → import `Data-Pipeline-Builder`.
3. Set **Root Directory** to `frontend` (Vercel auto-detects Vite).
4. Under **Environment Variables**, add (using your real Render URL from Step 1):
   - `VITE_API_BASE_URL` = `https://pipeforge-backend.onrender.com`
   - `VITE_WS_BASE_URL` = `wss://pipeforge-backend.onrender.com`  ← note **wss**, not ws
5. Click **Deploy**. You'll get a URL like `https://data-pipeline-builder.vercel.app`.

## Step 3 — Connect the two (CORS)

1. Back in Render → your service → **Environment** → set
   `CORS_ORIGINS` = your Vercel URL (e.g. `https://data-pipeline-builder.vercel.app`) — no trailing slash.
2. Render redeploys automatically. Done — the app is live.

## Step 4 (optional) — Keep the backend awake 24×7

The Render free tier gives **750 instance-hours/month** — enough to run one service
around the clock. It only sleeps because of inactivity, so a periodic ping keeps it warm:

1. Sign up at [uptimerobot.com](https://uptimerobot.com) (free).
2. Add an HTTP(S) monitor for `https://pipeforge-backend.onrender.com/health`, interval **10 minutes**.

Skip this if the ~50s cold start on first visit is acceptable — the app always wakes on its own.

---

## How CI/CD works after deployment

```
git push origin main
   ├─ GitHub Actions  → lint + 77 tests + type-check + Docker build
   ├─ Render          → rebuilds & redeploys the backend automatically
   └─ Vercel          → rebuilds & redeploys the frontend automatically
```

You never redo the setup above — it's one-time. Pull requests even get free
preview URLs on Vercel before you merge.

## Free-tier caveats

- **Ephemeral storage:** the free Render instance has no persistent disk, so the SQLite DB,
  registered users, and uploaded files reset whenever the service redeploys or restarts.
  Fine for a resume/demo project. If you later want persistence, add a free Postgres
  database from [Neon](https://neon.tech) or [Supabase](https://supabase.com).
- **Cold start:** without the UptimeRobot ping, the first request after 15 idle minutes
  takes ~50 seconds while Render boots the container. Subsequent requests are instant.
- **Groq free tier** has rate limits — the configured `LLM_FALLBACKS` already cushion this.
