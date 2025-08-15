FROM python:3.12-slim

WORKDIR /app

# Install system dependencies including Chromium
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libffi-dev \
    libssl-dev \
    curl \
    git \
    wget \
    unzip \
    chromium \
    chromium-driver \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Ensure ChromeDriver is executable and verify installation
RUN chmod +x /usr/bin/chromedriver || true

# Verify Chrome and ChromeDriver are working
RUN chromium --version && chromedriver --version

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

RUN pip install torch --index-url https://download.pytorch.org/whl/cpu

RUN mkdir /app/tmp

# Copy .env file first for environment variables
COPY .env .

COPY . .

EXPOSE 8000

# Set environment variables for Chrome
ENV DISPLAY=:99
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMIUM_FLAGS="--no-sandbox --disable-dev-shm-usage"
ENV PYTHONUNBUFFERED=1

# Create startup script
RUN echo '#!/bin/bash\n\
set -e\n\
echo "=== Container Startup Debug ==="\n\
echo "Starting application..."\n\
echo "Chrome version: $(chromium --version)"\n\
echo "ChromeDriver version: $(chromedriver --version)"\n\
echo "Python version: $(python --version)"\n\
echo "Working directory: $(pwd)"\n\
echo "Files in /app:"\n\
ls -la /app/\n\
echo "Environment variables:"\n\
printenv | grep -E "(REDIS|GEMINI|PYTHON)" || true\n\
echo "Testing Python imports..."\n\
python -c "import fastapi; print(\"FastAPI OK\")"\n\
python -c "from selenium import webdriver; print(\"Selenium OK\")"\n\
python -c "import torch; print(\"PyTorch OK\")"\n\
echo "Starting FastAPI server..."\n\
exec uvicorn main:app --host 0.0.0.0 --port 8000 --log-level debug' > /app/start.sh && \
    chmod +x /app/start.sh

CMD ["/app/start.sh"]
