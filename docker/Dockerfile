FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y build-essential python3-dev libffi-dev libssl-dev curl git wget unzip

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

RUN pip install torch --index-url https://download.pytorch.org/whl/cpu

RUN wget https://dl.google.com/linux/deb/pool/main/g/google-chrome-stable/google-chrome-stable_138.0.7204.183-1_amd64.deb

RUN apt install -y ./google-chrome-stable_138.0.7204.183-1_amd64.deb

RUN rm google-chrome-stable_138.0.7204.183-1_amd64.deb

RUN mkdir /app/tmp

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
