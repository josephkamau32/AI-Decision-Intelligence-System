# 🚀 Fly.io Deployment Guide

Quick step-by-step guide to deploy your FastAPI backend to Fly.io.

## Prerequisites

- Fly.io account (sign up at https://fly.io)
- Fly.io CLI installed
- Git repository access

## Step 1: Install Fly.io CLI

**Windows (PowerShell):**
```powershell
powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"
```

**After installation, restart your terminal** to use the `fly` command.

## Step 2: Login to Fly.io

```bash
fly auth login
```

This will open your browser to authenticate.

## Step 3: Navigate to Backend Directory

```bash
cd "c:\Users\HP\Documents\Projects\AI Decision Intelligence system\backend"
```

## Step 4: Create Fly.io App

```bash
fly launch --no-deploy
```

When prompted:
- **App name**: Press Enter to accept `decisera-backend` (or choose your own)
- **Region**: Choose the closest to you or press Enter for default
- **PostgreSQL**: Say **No** (we'll use file-based storage for now)
- **Redis**: Say **No** (optional for later)

## Step 5: Set Environment Secrets

```bash
# Generate secure keys
fly secrets set SECRET_KEY="$(openssl rand -hex 32)"
fly secrets set JWT_SECRET_KEY="$(openssl rand -hex 32)"

# Set your API keys
fly secrets set OPENAI_API_KEY="your-openai-api-key-here"
# or if using Google Gemini:
fly secrets set GOOGLE_API_KEY="your-google-api-key-here"
```

**Important**: Replace `your-openai-api-key-here` with your actual API key!

## Step 6: Create Persistent Volume

```bash
fly volumes create decisera_data --size 1
```

This creates 1GB storage for your models and datasets.

## Step 7: Deploy!

```bash
fly deploy
```

This will:
1. Build your Docker image
2. Push to Fly.io registry
3. Deploy to your app
4. Start the service

**Deployment takes 3-5 minutes** ⏱️

## Step 8: Verify Deployment

```bash
# Check status
fly status

# View logs
fly logs

# Open in browser
fly open
```

Your backend URL will be: **https://decisera-backend.fly.dev**

## Step 9: Test the API

```bash
# Test health endpoint
curl https://decisera-backend.fly.dev/health

# View API docs
# Open in browser: https://decisera-backend.fly.dev/docs
```

## Step 10: Update Frontend

Update your frontend environment variable on Vercel:

1. Go to Vercel dashboard
2. Select your `decisera` project
3. Go to **Settings** → **Environment Variables**
4. Update `REACT_APP_API_URL` to: `https://decisera-backend.fly.dev`
5. Redeploy frontend

## Useful Commands

```bash
# View app status
fly status

# View real-time logs
fly logs -a decisera-backend

# SSH into your app
fly ssh console

# Scale app (change VM size)
fly scale vm shared-cpu-1x --memory 512

# View secrets
fly secrets list

# Restart app
fly apps restart decisera-backend

# Destroy app (careful!)
fly apps destroy decisera-backend
```

## Troubleshooting

### Build fails
```bash
# Check Dockerfile
cat Dockerfile

# Try building locally first
docker build -t test .
```

### App crashes
```bash
# View logs
fly logs

# Common issues:
# - Missing environment variables (check fly secrets list)
# - Port mismatch (should be 8000)
# - Memory issues (scale up if needed)
```

### Can't connect to backend
```bash
# Check if app is running
fly status

# Check health endpoint
fly checks list

# View HTTP logs
fly logs --http
```

### Update environment variables
```bash
# Set new secret
fly secrets set NEW_VAR="value"

# Unset secret
fly secrets unset OLD_VAR
```

## Cost Monitoring

Fly.io free tier includes:
- 3 shared-cpu VMs (256MB RAM each)
- 3GB persistent storage
- 160GB/month outbound transfer

Check your usage:
```bash
fly dashboard
```

## Next Steps

After successful deployment:
1. ✅ Test all API endpoints via `/docs`
2. ✅ Register a test user
3. ✅ Upload a small dataset
4. ✅ Test AI Copilot (if API key configured)
5. ✅ Update frontend and test end-to-end

---

**Need help?** Check Fly.io docs: https://fly.io/docs
