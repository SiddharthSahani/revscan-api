# GitHub Codespaces Deployment

## Quick Start

1. **Open in Codespaces:**
   - Go to your GitHub repository
   - Click the green "Code" button
   - Select "Codespaces" tab
   - Click "Create codespace on docker-deployment"

2. **Start the API:**
   ```bash
   ./start-codespace.sh
   ```

3. **Access your API:**
   - The URL will be shown in the terminal output
   - Format: `https://{codespace-name}-8000.app.github.dev`
   - GitHub will automatically forward port 8000

## Environment Variables

Make sure your `.env` file contains:
```
UPSTASH_REDIS_REST_URL=https://leading-boxer-59220.upstash.io
UPSTASH_REDIS_REST_TOKEN=AedUAAIjcDFjMGNmYTAzODYwMmM0ZGRiOGNjYTQzYTJhM2FmZTc1YnAxMA
GEMINI_API_KEY=AIzaSyCUr4oNrSyst0ynK3KFWYFkkon550xPTGI
```

## API Endpoints

- **Health Check:** `GET /`
- **API Docs:** `GET /docs`
- **Scrape Reviews:** `POST /reviews/`

## Features

- ✅ Chromium + ChromeDriver pre-installed
- ✅ All Python dependencies included
- ✅ Anti-bot detection measures
- ✅ ML models for sentiment analysis
- ✅ Redis caching integration
- ✅ Port forwarding configured
- ✅ Hot reload enabled

## Free Tier Limits

- 60 hours/month for free accounts
- 180 hours/month for Pro accounts
- Auto-sleep after 30 minutes of inactivity
