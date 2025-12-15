#!/usr/bin/env python3
"""
Telegram File Server Bot (MongoDB + Force Join)

Features:
- Only works via deep links: https://t.me/<BOT_USERNAME>?start=<mapping>
- mapping -> MongoDB lookup -> message_id
- Copies file from STORAGE_CHANNEL to user
- Force Join enabled:
  * Checks if user joined F_SUB_CHANNEL_ID
  * If not, shows two buttons:
      - Join Now ✅ (channel link)
      - Join & Get File ♻️ (re-check)

Bot does NOT accept any files or commands except /start.
"""

import os
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from pymongo import MongoClient
from pymongo.errors import PyMongoError

# ---------------- CONFIG ----------------
load_dotenv()

BOT_TOKEN = os.getenv("FILE_SERVER_BOT_TOKEN")
BOT_USERNAME = os.getenv("BOT_USERNAME")
STORAGE_CHANNEL_ID = int(os.getenv("STORAGE_CHANNEL_ID"))

F_SUB_CHANNEL_ID = int(os.getenv("F_SUB_CHANNEL_ID"))
F_SUB_CHANNEL_LINK = os.getenv("F_SUB_CHANNEL_LINK")

MONGO_URI = os.getenv("MONGODB_URI")
MONGO_DB = os.getenv("MONGO_DB_NAME")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "mappings")

# ---------------- LOGGING ----------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Disable verbose logs from libraries
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)
logging.getLogger("apscheduler").setLevel(logging.WARNING)

# ---------------- MONGODB ----------------
try:
    mongo_client = MongoClient(MONGO_URI)
    mongo_db = mongo_client[MONGO_DB]
    mappings_col = mongo_db[MONGO_COLLECTION]
    logger.info("✅ MongoDB connected successfully")
except PyMongoError as e:
    logger.error(f"❌ MongoDB connection failed: {e}")
    raise RuntimeError(f"MongoDB connection failed: {e}")

# ---------------- UTIL ----------------
async def is_user_joined(bot, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(F_SUB_CHANNEL_ID, user_id)
        return member.status in ("member", "administrator", "creator")
    except Exception:
        return False


def join_keyboard(mapping: str):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Join Now ✅", url=F_SUB_CHANNEL_LINK)],
        [InlineKeyboardButton("Join & Get File ♻️", url=f"https://t.me/{BOT_USERNAME}?start={mapping}")]
    ])

# ---------------- START HANDLER ----------------
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"
    
    if not context.args:
        logger.warning(f"⚠️ Invalid access attempt by user {user_id} (@{username}) - No mapping provided")
        await update.message.reply_text(
            "❌ Invalid access.\nUse a valid file link."
        )
        return

    mapping = context.args[0]

    # Force Join Check
    joined = await is_user_joined(context.bot, user_id)
    if not joined:
        logger.info(f"📌 Force Join triggered for user {user_id} (@{username}) - mapping: {mapping}")
        await update.message.reply_text(
            "⚠️ You have not joined the main channel yet.\nTo access this file, please join the main channel first 👇",
            reply_markup=join_keyboard(mapping),
            disable_web_page_preview=True,
        )
        return

    # MongoDB Lookup
    doc = mappings_col.find_one({"mapping": mapping})
    if not doc or "message_id" not in doc:
        logger.warning(f"⚠️ File not found for mapping: {mapping} (user: {user_id})")
        await update.message.reply_text("❌ File not found or link expired.")
        return

    message_id = int(doc["message_id"])

    try:
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action=ChatAction.UPLOAD_DOCUMENT,
        )

        await context.bot.copy_message(
            chat_id=update.effective_chat.id,
            from_chat_id=STORAGE_CHANNEL_ID,
            message_id=message_id,
        )
        
        logger.info(f"✅ File sent successfully to user {user_id} (@{username}) - message_id: {message_id}")

    except Exception as e:
        logger.error(f"❌ Failed to copy message for user {user_id} (@{username}): {str(e)}")
        await update.message.reply_text("❌ File not found or access denied.")


# ---------------- MAIN ----------------
def main():
    if not all([
        BOT_TOKEN,
        STORAGE_CHANNEL_ID,
        F_SUB_CHANNEL_ID,
        F_SUB_CHANNEL_LINK,
        MONGO_URI,
    ]):
        logger.error("❌ Missing required .env configuration")
        raise RuntimeError("Missing required .env configuration")

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_handler))

    logger.info("🚀 File Server Bot (Force Join + MongoDB) running...")
    app.run_polling()


if __name__ == "__main__":
    main()