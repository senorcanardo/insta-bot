# Instagram → Telegram Bot — Setup Guide

## What you need
- A Telegram account
- A GitHub account
- A Railway account (free, sign up at railway.app)
- ~15 minutes

---

## Step 1: Create the Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send `/newbot`
3. Choose a name (e.g. `My Insta Archiver`)
4. Choose a username ending in `bot` (e.g. `my_insta_archiver_bot`)
5. BotFather gives you a token like:
   ```
   1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
   ```
   **Save this — it's your `BOT_TOKEN`.**

---

## Step 2: Get your Telegram User ID

1. Search for **@userinfobot** on Telegram
2. Send `/start`
3. It replies with your numeric ID like `987654321`
   **Save this — it's your `ALLOWED_USER_ID`.**
   (This locks the bot so only you can use it.)

---

## Step 3: Get Instagram Cookies (important)

Instagram now requires authentication even for public posts.
You need to export your session cookies from a browser.

1. Install the **"Get cookies.txt LOCALLY"** Chrome extension
   (search for it in the Chrome Web Store)
2. Log into Instagram in your browser
3. Go to instagram.com
4. Click the extension → Export cookies for this site
5. Save the file as `cookies.txt`
6. Keep it handy — you'll upload it to Railway in Step 5

---

## Step 4: Push code to GitHub

```bash
cd insta-bot
git init
git add .
git commit -m "initial bot"
# Create a new repo on github.com, then:
git remote add origin https://github.com/YOUR_USERNAME/insta-bot.git
git push -u origin main
```

---

## Step 5: Deploy on Railway

1. Go to **railway.app** and sign in with GitHub
2. Click **New Project → Deploy from GitHub repo**
3. Select your `insta-bot` repo
4. Once it appears, go to your service → **Variables** tab
5. Add these environment variables:
   ```
   BOT_TOKEN      = (your token from Step 1)
   ALLOWED_USER_ID = (your user ID from Step 2)
   ```
6. For cookies — go to **Settings → Volumes** or simply use the
   Railway CLI to upload `cookies.txt`:
   ```bash
   npm install -g @railway/cli
   railway login
   railway up
   ```
   Then go to your service shell and you can `cat` to verify it's there.

   **Alternative:** Base64-encode the cookies and pass as an env var:
   ```bash
   base64 cookies.txt | tr -d '\n'
   ```
   Add as `COOKIES_B64` env var, and add this snippet to `bot.py` startup:
   ```python
   import base64
   if b64 := os.environ.get("COOKIES_B64"):
       with open("cookies.txt", "wb") as f:
           f.write(base64.b64decode(b64))
   ```

7. Railway auto-deploys. Check the **Logs** tab — you should see:
   ```
   Bot started.
   ```

---

## Step 6: Test it

1. Open Telegram, find your bot by its username
2. Send `/start`
3. Paste an Instagram post or reel URL
4. You should receive the media within ~10-20 seconds

---

## Troubleshooting

| Problem | Fix |
|---|---|
| "No media files downloaded" | Cookies may be expired — re-export and redeploy |
| File over 50MB | Reels longer than ~3-4min may hit Telegram's limit |
| Bot doesn't respond | Check Railway logs for errors |
| yt-dlp error | Update yt-dlp: add `yt-dlp --update` to Railway build cmd |

---

## Keeping it updated

yt-dlp updates frequently to keep up with Instagram changes.
Railway redeploys automatically when you push to GitHub, so to update:

```bash
# bump the version in requirements.txt if needed, then:
git commit -am "update yt-dlp"
git push
```

Railway picks it up automatically.
