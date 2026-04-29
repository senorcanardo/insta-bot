import logging
import os
import re
import asyncio
import urllib.request
from pathlib import Path
from telegram import Update, InputMediaPhoto, InputMediaVideo
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes
from telegram.constants import ParseMode
from downloader import download_instagram_media, cleanup

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ["BOT_TOKEN"]
ALLOWED_USER_ID = int(os.environ.get("ALLOWED_USER_ID", "0"))

# Cookies setup
cookies_url = os.environ.get("COOKIES_URL")
if cookies_url:
    try:
        urllib.request.urlretrieve(cookies_url, "cookies.txt")
        logger.info("Cookies downloaded from COOKIES_URL.")
    except Exception as e:
        logger.warning(f"Failed to download cookies: {e}")

def is_authorized(update: Update) -> bool:
    if ALLOWED_USER_ID == 0:
        return True
    return update.effective_user.id == ALLOWED_USER_ID


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        return
    await update.message.reply_text(
        "👋 Send me an Instagram post or reel link and I'll download it for you."
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        await update.message.reply_text("⛔ Unauthorized.")
        return

    text = update.message.text or ""
    match = INSTAGRAM_PATTERN.search(text)

    if not match:
        await update.message.reply_text("❓ Please send a valid Instagram URL.")
        return

    url = match.group(0).split("?")[0]  # strip query params
    status_msg = await update.message.reply_text("⏳ Downloading...")

    files = []
    try:
        files = await asyncio.to_thread(download_instagram_media, url)

        if not files:
            await status_msg.edit_text("❌ Couldn't download. The post may be private or unavailable.")
            return

        await status_msg.edit_text(f"📤 Sending {len(files)} file(s)...")

        # Split into chunks of 10 (Telegram album limit)
        chunks = [files[i:i+10] for i in range(0, len(files), 10)]

        for chunk in chunks:
            if len(chunk) == 1:
                path = chunk[0]
                if path.suffix.lower() in (".mp4", ".mov", ".webm"):
                    await update.message.reply_video(video=open(path, "rb"))
                else:
                    await update.message.reply_photo(photo=open(path, "rb"))
            else:
                media_group = []
                for path in chunk:
                    if path.suffix.lower() in (".mp4", ".mov", ".webm"):
                        media_group.append(InputMediaVideo(media=open(path, "rb")))
                    else:
                        media_group.append(InputMediaPhoto(media=open(path, "rb")))
                await update.message.reply_media_group(media=media_group)

        await status_msg.delete()

    except Exception as e:
        logger.error(f"Error processing {url}: {e}")
        await status_msg.edit_text(f"❌ Error: {str(e)[:200]}")
    finally:
        cleanup(files)


def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("Bot started.")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
