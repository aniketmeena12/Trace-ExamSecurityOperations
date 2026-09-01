# Trace — Deployment Guide

This guide covers deploying Trace to production. The live setup is **Netlify**
(frontend) + **Render** (backend + PostgreSQL) — see the Render section below.
The Vercel/Railway walkthrough further down is kept as an alternative.

## Prerequisites

1. GitHub account (for CI/CD)
2. Vercel account (https://vercel.com - free tier is fine)
3. Railway account (https://railway.app - $5/month credit)
4. PostgreSQL database (Railway provides this)

## 🟣 Deploy the Backend on Render (current setup)

The repo ships a Blueprint at [`render.yaml`](render.yaml) that provisions the
FastAPI service *and* its PostgreSQL database in one step. The frontend stays on
Netlify (see [`netlify.toml`](netlify.toml)).

### Step 1 — Create the Blueprint

1. Push this repo to GitHub.
2. Render dashboard → **New → Blueprint**.
3. Pick the `Trace-ExamSecurityOperations` repo. Render reads `render.yaml`
   from the repo root and shows a `trace-backend` web service plus a
   `trace-db` PostgreSQL instance.
4. Render prompts for the one variable it cannot generate:
   `TRACE_FRONTEND_ORIGIN` → your Netlify origin, e.g.
   `https://your-site.netlify.app` (scheme + host, **no trailing slash**).
5. **Apply**. First build takes a few minutes.

Everything else is wired by the Blueprint:

| Variable | Source |
|---|---|
| `TRACE_SECRET_KEY` | generated once by Render, stable across deploys |
| `TRACE_DB_URL` | internal connection string of `trace-db` |
| `TRACE_FRONTEND_ORIGIN` | you, at Blueprint apply time |
| `PORT` | injected by Render; `start.sh` reads it |

### Step 2 — Point the frontend at the new backend

The service URL is `https://<service-name>.onrender.com`. If the name
`trace-backend` was already taken, Render appends a suffix — copy the real URL
from the dashboard and make sure both of these match it:

- `netlify.toml` → `[build.environment] VITE_API_URL`
- `frontend/.env.production` → `VITE_API_URL`

`VITE_API_URL` is baked in at build time, so **redeploy the Netlify site** after
changing it. A stale value shows up as requests still hitting the old host.

### Step 3 — Verify

```bash
curl https://<your-service>.onrender.com/health
# {"status":"ok","service":"trace","version":"0.2.0"}
```

Then load the Netlify site and sign in. A CORS error in the browser console
means `TRACE_FRONTEND_ORIGIN` doesn't exactly match the origin the browser
sends — the API allows that single origin and nothing else.

### Free-tier caveats

- The web service **sleeps after ~15 min idle**; the next request takes ~50s to
  wake it. Upgrade the instance, or ping `/health` on a schedule, to avoid it.
- Free PostgreSQL instances **expire after 30 days**. Move to a paid plan
  before then or the data goes away.
- The filesystem is ephemeral. Do not fall back to SQLite here — without
  `TRACE_DB_URL` the app writes `trace.db` to disk and loses it on every deploy.

### Rotating `TRACE_SECRET_KEY`

It signs JWTs *and* derives the wrapping key for released paper keys. Changing
it logs everyone out **and** makes already-released paper keys undecryptable.
Treat it as permanent for the life of the database.

---

## 📦 Build Frontend for Production

```bash
cd frontend
npm run build
# Creates optimized dist/ folder
```

## 🚀 Deployment Option 1: Vercel + Railway (Recommended)

### Step 1: Deploy Frontend on Vercel

#### A. Push to GitHub
Ensure your code is pushed to GitHub:
```bash
git add .
git commit -m "Production deployment"
git push origin main
```

#### B. Import on Vercel
1. Go to https://vercel.com/new
2. Click "Import Git Repository"
3. Select your GitHub repository
4. **Framework Preset**: Select "Vite"
5. **Root Directory**: Set to `frontend`
6. Click "Deploy"

**That's it!** Vercel auto-deploys on every push to `main`.

### Step 2: Deploy Backend on Railway

#### A. Create Railway Project
1. Go to https://railway.app
2. Click "New Project"
3. Select "Deploy from GitHub"
4. Select your repository
5. Choose "Python" service type

#### B. Configure Environment Variables
In Railway dashboard, go to Variables and set:

```
TRACE_SECRET_KEY=<generate-strong-key>
TRACE_DB_URL=${{Postgres.DATABASE_URL}}
TRACE_FRONTEND_ORIGIN=https://your-frontend.vercel.app
TRACE_TOKEN_TTL_MIN=720
PYTHONUNBUFFERED=1
```

**To generate `TRACE_SECRET_KEY`:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

#### C. Add PostgreSQL Database
1. In Railway, click "Add Service" → "PostgreSQL"
2. It auto-connects and provides `DATABASE_URL`
3. The `TRACE_DB_URL` environment variable automatically uses it

#### D. Configure Build & Start
In Railway project settings:
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT trace.api.app:app`

#### E. Deploy
Click the "Deploy" button. Railway watches your GitHub and auto-deploys on push.

### Step 3: Link Frontend to Backend

In Vercel frontend project:
1. Go to Settings → Environment Variables
2. Add:
   ```
   VITE_API_URL=https://your-railway-backend.railway.app
   ```
3. Redeploy

## 🐳 Deployment Option 2: Docker + Any Cloud Provider

### Test Locally First
```bash
docker-compose up
# Frontend: http://localhost:5173
# Backend: http://localhost:8000
# Database: PostgreSQL at localhost:5432
```

### Deploy to AWS, DigitalOcean, Google Cloud, etc.

#### A. Build Docker Image
```bash
cd backend
docker build -t trace-backend:latest .
```

#### B. Push to Registry
```bash
# Docker Hub
docker tag trace-backend:latest your-username/trace-backend:latest
docker push your-username/trace-backend:latest
```

#### C. Run on Server
```bash
docker run \
  -e TRACE_DB_URL=postgresql://user:pass@db-host:5432/trace \
  -e TRACE_SECRET_KEY=your-secret-key \
  -e TRACE_FRONTEND_ORIGIN=https://your-frontend.com \
  -p 8000:8000 \
  your-username/trace-backend:latest
```

## 🔐 Production Security Checklist

- [ ] Change `TRACE_SECRET_KEY` to a strong random string
- [ ] Use PostgreSQL (not SQLite)
- [ ] Set `TRACE_FRONTEND_ORIGIN` to your actual frontend URL
- [ ] Use HTTPS for all connections
- [ ] Enable CORS only for your frontend domain
- [ ] Rotate JWT secret periodically
- [ ] Set up database backups
- [ ] Monitor logs and health endpoint (`/health`)
- [ ] Use strong database passwords

## 📊 Monitoring

### Health Check Endpoint
```bash
curl https://your-backend.railway.app/health
# Response: {"status":"ok","service":"trace","version":"0.2.0"}
```

### API Documentation
Swagger UI available at: `https://your-backend.railway.app/docs`

## 🆘 Troubleshooting

### Database Connection Issues
```bash
# Test connection string
psql postgresql://user:password@host:5432/database
```

### Backend Not Starting
```bash
# Check logs in Railway dashboard
# Verify environment variables are set
# Ensure Python version is 3.10+
```

### Frontend API Errors
1. Check VITE_API_URL in Vercel environment variables
2. Ensure backend CORS allows frontend origin
3. Check browser console for CORS errors

### Missing Database Tables
The backend auto-creates tables on startup. If tables are missing:
```bash
# Manual bootstrap (one-time)
python -c "from trace.bootstrap import bootstrap; bootstrap()"
```

## 🔄 CI/CD Pipeline

Both Vercel and Railway watch your GitHub repository:

1. **Push to GitHub** → Automatic deployment
2. **Pull Request** → Preview deployment (Vercel)
3. **Merge to main** → Production deployment

## 💰 Cost Estimate

| Service | Cost | Notes |
|---------|------|-------|
| Vercel Frontend | $0-20/mo | Free tier covers most cases |
| Railway Backend | $5+ /mo | Includes free credits ($5/mo) |
| PostgreSQL DB | Included | Railway includes DB in pricing |
| **Total** | **$5-25/mo** | Scale-as-you-grow pricing |

## 📝 Next Steps

1. Generate a strong `TRACE_SECRET_KEY`
2. Create GitHub, Vercel, and Railway accounts
3. Push code to GitHub
4. Deploy frontend to Vercel
5. Deploy backend to Railway with PostgreSQL
6. Link them with environment variables
7. Test end-to-end

## 🆘 Support

- Vercel Docs: https://vercel.com/docs
- Railway Docs: https://docs.railway.app
- FastAPI Docs: https://fastapi.tiangolo.com/deployment/
