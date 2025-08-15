#!/bin/bash

echo "🚀 Starting RevScan API in GitHub Codespaces"
echo "============================================="

# Set environment variables if not already set
export PYTHONUNBUFFERED=1

# Check if required environment variables are set
if [ -z "$UPSTASH_REDIS_REST_URL" ] || [ -z "$UPSTASH_REDIS_REST_TOKEN" ] || [ -z "$GEMINI_API_KEY" ]; then
    echo "⚠️  Environment variables not set. Loading from .env file..."
    if [ -f ".env" ]; then
        export $(cat .env | xargs)
        echo "✅ Environment variables loaded from .env"
    else
        echo "❌ No .env file found. Please create one with your credentials."
        exit 1
    fi
fi

echo "🔧 Environment check:"
echo "   Chrome: $(chromium --version 2>/dev/null || echo 'Not found')"
echo "   ChromeDriver: $(chromedriver --version 2>/dev/null || echo 'Not found')"
echo "   Python: $(python --version)"

echo ""
echo "🌐 Starting FastAPI server..."
echo "   Server will be available at: https://$CODESPACE_NAME-8000.app.github.dev"
echo "   Or locally at: http://localhost:8000"
echo ""

# Start the server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
