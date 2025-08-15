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

# Check where chromium-driver is installed and create symlink if needed
RUN which chromium && which chromedriver || (find /usr -name "chromedriver" -o -name "chromium-driver" 2>/dev/null && ln -sf /usr/lib/chromium-browser/chromedriver /usr/bin/chromedriver)

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

RUN pip install torch --index-url https://download.pytorch.org/whl/cpu

RUN mkdir /app/tmp

COPY . .

EXPOSE 8000

# Set environment variables for Chrome
ENV DISPLAY=:99
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMIUM_FLAGS="--no-sandbox --disable-dev-shm-usage"

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
