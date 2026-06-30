import os
import sys
import asyncio
import logging
import tempfile
from telegram.request import HTTPXRequest
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# ---- PATH FIX (CRITICAL) ----
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from backend.app.information.information_pipeline import handle_information_query
from frontend.telegram_bot.multilingual import MultilingualService


# --------------------------------------------------
# Environment
# --------------------------------------------------
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


# --------------------------------------------------
# Logging
# --------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

# --------------------------------------------------
# Services
# --------------------------------------------------
multi_service = MultilingualService()

LANGUAGES = {
    "en": "English",
    "hi": "Hindi",
    "gu": "Gujarati",
}

ASR_LANG_MAP = {
    "en": "en-IN",
    "hi": "hi-IN",
    "gu": "gu-IN",
}

# --------------------------------------------------
# Handlers
# --------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_language_selection(update, context)


async def show_language_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🌾 *Welcome to Kisaan Sahayak!* 🌾\n\n"
        "Please select your language:\n\n"
        "1️⃣ English (Type 1)\n"
        "2️⃣ हिंदी (Type 2)\n"
        "3️⃣ ગુજરાતી (Type 3)\n\n"
        "_Type the number below_"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE, lang_code: str):
    context.user_data["language"] = lang_code
    lang_name = LANGUAGES.get(lang_code, "English")

    messages = {
        "en": f"✅ Language set to *{lang_name}*.",
        "hi": f"✅ भाषा *{lang_name}* पर सेट की गई है।",
        "gu": f"✅ ભાષા *{lang_name}* પર સેટ છે.",
    }

    await update.message.reply_text(messages.get(lang_code, messages["en"]), parse_mode="Markdown")


async def process_query(update: Update, context: ContextTypes.DEFAULT_TYPE, user_text: str, is_voice=False):
    # Language selection via numbers
    if user_text.strip() in {"1", "2", "3"}:
        await set_language(update, context, {"1": "en", "2": "hi", "3": "gu"}[user_text.strip()])
        return

    user_lang = context.user_data.get("language")
    if not user_lang:
        await show_language_selection(update, context)
        return

    loop = asyncio.get_running_loop()

    try:
        # Translate to English
        english_query = user_text
        if user_lang != "en":
            english_query = await loop.run_in_executor(
                None, multi_service.translate, user_text, user_lang, "en"
            )

        # Backend (Information Mode)
        result = await loop.run_in_executor(
            None, handle_information_query, english_query
        )

        english_answer = result.get(
            "answer", "This information is not mentioned in the official guidelines."
        )

        # Translate back
        final_answer = english_answer
        if user_lang != "en":
            final_answer = await loop.run_in_executor(
                None, multi_service.translate, english_answer, "en", user_lang
            )

        # Respond
        if is_voice:
            audio_path = await loop.run_in_executor(
                None, multi_service.tts, final_answer, user_lang
            )
            await context.bot.send_voice(
                chat_id=update.effective_chat.id,
                voice=open(audio_path, "rb"),
                caption=final_answer[:1000],
            )
            os.remove(audio_path)
        else:
            await update.message.reply_text(final_answer)

    except Exception as e:
        logging.error("Telegram bot error", exc_info=e)
        await update.message.reply_text(
            "Sorry, something went wrong. Please try again."
        )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await process_query(update, context, update.message.text)


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_lang = context.user_data.get("language")
    if not user_lang:
        await show_language_selection(update, context)
        return

    voice = await context.bot.get_file(update.message.voice.file_id)

    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as f:
        ogg_path = f.name

    await voice.download_to_drive(ogg_path)

    try:
        asr_lang = ASR_LANG_MAP.get(user_lang, "en-IN")
        loop = asyncio.get_running_loop()
        text = await loop.run_in_executor(None, multi_service.asr, ogg_path, asr_lang)

        if not text:
            await update.message.reply_text("Sorry, I could not understand the audio.")
            return

        await update.message.reply_text(f"🎤 {text}")
        await process_query(update, context, text, is_voice=True)

    finally:
        os.remove(ogg_path)

# --------------------------------------------------
# Run bot
# --------------------------------------------------
def run_bot():
    if not TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN not set")

    request = HTTPXRequest(
        connect_timeout=60,
        read_timeout=60,
        write_timeout=60,
    )

    app = ApplicationBuilder().token(TOKEN).request(request).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))

    logging.info("🤖 Telegram bot running...")
    app.run_polling(poll_interval=1, timeout=7)


if __name__ == "__main__":
    run_bot()
