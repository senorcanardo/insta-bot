FROM python:3.11-slim

# bust cache 2
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip3 install -r requirements.txt

RUN pip3 install --upgrade yt-dlp gallery-dl

COPY . .

CMD ["python3", "bot.py"]