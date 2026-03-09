# YASHA Railway Deployment Guide

## Prerequisites
1. GitHub account
2. Railway.app account (free tier available)

## Deployment Steps

### 1. Prepare GitHub Repository
```bash
cd /Users/macbook/.gemini/antigravity/scratch/fitness_bot
git init
git add .
git commit -m "Initial commit - YASHA v2.0"
git branch -M main
git remote add origin YOUR_GITHUB_REPO_URL
git push -u origin main
```

### 2. Deploy to Railway

1. Go to https://railway.app
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your YASHA repository
5. Railway will auto-detect the project

### 3. Configure Environment Variables

In Railway dashboard, add these variables:

**Required:**
- `BOT_TOKEN` - Your Telegram bot token
- `GEMINI_API_KEY` - Your Gemini API key
- `ADMIN_ID` - Your Telegram user ID
- `JWT_SECRET` - Random secret key (generate with: `openssl rand -hex 32`)

**Optional:**
- `PAYMENT_PROVIDER_TOKEN` - Telegram payment token
- `BOT_USERNAME` - Your bot username (without @)

### 4. Get Your Deployment URL

After deployment:
1. Railway will provide a public URL (e.g., `https://yasha-production.up.railway.app`)
2. Copy this URL
3. Use it for your Telegram Mini App

### 5. Update Telegram Bot Settings

In [@BotFather](https://t.me/botfather):
```
/setmenubutton
Select your bot
Send the Railway URL: https://your-app.up.railway.app
```

## Database

Railway automatically provides persistent storage. Your SQLite database will be preserved across deployments.

For PostgreSQL (recommended for production):
1. Add PostgreSQL service in Railway
2. Update `backend/database.py` DATABASE_URL to use `$DATABASE_URL` environment variable

## Monitoring

- Railway provides logs in the dashboard
- View backend logs and bot logs separately
- Auto-restarts on crashes

## Costs

Free tier includes:
- $5/month usage credit
- Sufficient for small-medium bots
- Upgrade if needed

## Support

If deployment fails, check:
1. All environment variables are set
2. requirements.txt is complete
3. Railway logs for errors

---

**Ready to deploy?** Push your code to GitHub and connect to Railway!
