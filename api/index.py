import os
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

app = FastAPI()
telegram_app = Application.builder().token(BOT_TOKEN).build()

client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """
You are Kyla 🤖, the personal AI assistant of Venkateswaran K (Kyro).

You confidently explain his skills, projects, achievements, goals,
and respond warmly like a personal portfolio assistant.
"""

# ---------------- COMMANDS ----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hey 👋 I'm Kyla 🤖\n"
        "Personal AI assistant of *Venkateswaran (Kyro)*.\n"
        "Ask me about his skills, projects, or achievements 🚀",
        parse_mode="Markdown"
    )

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Kyla 🤖 – Personal AI Portfolio Bot\nBuilt with FastAPI + Groq + Telegram"
    )

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text}
        ]
    )

    reply = response.choices[0].message.content.strip()
    await update.message.reply_text(reply)

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("about", about))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

# ---------------- WEBHOOK ----------------

@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return {"ok": True}
