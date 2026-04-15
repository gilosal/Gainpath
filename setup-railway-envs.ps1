# ── Backend Configuration ───────────────────────────────────────────────────
Write-Host "Configuring Backend Service..." -ForegroundColor Cyan

# Enter backend directory to target the backend service
cd backend

# Required secrets (replace these placeholders or they'll be set as is)
railway variables set SECRET_KEY="replace-this-with-a-random-32-char-string"
railway variables set APP_PASSWORD="your-gym-password"
railway variables set OPENROUTER_API_KEY="sk-or-v1-..."

# Default settings
railway variables set AI_MODEL="anthropic/claude-3-5-sonnet"
railway variables set AI_FALLBACK_MODEL="openai/gpt-4o-mini"
railway variables set APP_NAME="PaceForge"

# ── Frontend Configuration ──────────────────────────────────────────────────
Write-Host "`nConfiguring Frontend Service..." -ForegroundColor Cyan

# Move to frontend directory
cd ../frontend

# You must set this to your backend service's URL (e.g., https://backend-production.up.railway.app)
# Tip: Use 'railway status' to find your backend's domain
railway variables set NEXT_PUBLIC_API_URL="https://your-backend-url.up.railway.app"

Write-Host "`nEnvironment variables set! Your services will redeploy automatically." -ForegroundColor Green
cd ..
