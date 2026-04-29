FROM python:3.11-slim

# Install ffmpeg and yt-dlp system dependency
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip3 install -r requirements.txt

# Install latest yt-dlp directly
RUN pip3 install yt-dlp

COPY . .

CMD ["python3", "bot.py"]