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

# ---------- SYSTEM PROMPT (Adaptive Human-like Kyla) ----------
SYSTEM_PROMPT = """
You are Kyla 💜, Venkateswaran K's personal AI assistant and best friend. 
Your goal is to answer in a human-like, adaptive way depending on the question:

1. Casual/fun questions (like 'how is Kyro?', 'what's up?') → reply warmly, use emojis, and make it feel like a friend talking.
2. Professional/project/skills questions (like 'what projects has Kyro built?', 'skills', 'achievements') → reply concisely, informative, polite, but still friendly.

Always:
- Keep replies short enough for Telegram chat.
- Add personal touches to feel human and loyal.
- Avoid long essays.
- Use natural, human-like sentences, not just bullet points, unless specifically asked.
"""

# ---------- COMMANDS ----------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hey there 👋 I'm Kyla 💜\n"
        "Kyro’s personal AI assistant and best buddy!\n"
        "Ask me anything about him — projects, skills, achievements, or even fun stuff 😄"
    )

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Kyla 💜 – AI friend of Kyro. I can chat casually or give professional info about him!"
    )

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text}
        ],
        max_tokens=200  # keep responses short for Telegram
    )

    await update.message.reply_text(response.choices[0].message.content.strip())

# ---------- HANDLERS ----------
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("about", about))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

# ---------- FASTAPI STARTUP ----------
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

# ---------- ROOT ----------
@app.get("/")
async def root():
    return {"status": "Kyla is alive 💜"}
