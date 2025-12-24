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

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

app = FastAPI()

telegram_app = Application.builder().token(BOT_TOKEN).build()
client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """
You are Kyla 🤖, the personal AI assistant of Venkateswaran K (Kyro).
Answer confidently about his skills, projects, achievements, and goals.
"""

# ---------- COMMANDS ----------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hey 👋 I'm Kyla 🤖\n"
        "Personal AI assistant of Venkateswaran (Kyro).\n"
        "Ask me about skills, projects, or achievements 🚀"
    )

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Kyla 🤖 – AI-powered personal portfolio bot"
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

    await update.message.reply_text(response.choices[0].message.content.strip())

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("about", about))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

# ---------- FASTAPI STARTUP (🔥 FIX) ----------

@app.on_event("startup")
async def startup():
    await telegram_app.initialize()

# ---------- WEBHOOK ----------

@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return {"ok": True}

# ---------- OPTIONAL ROOT ----------

@app.get("/")
async def root():
    return {"status": "Kyla is alive 🤖"}
