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
from collections import defaultdict
import asyncio

# ----------------- ENVIRONMENT VARIABLES -----------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# ----------------- FASTAPI & TELEGRAM SETUP -----------------
app = FastAPI()
telegram_app = Application.builder().token(BOT_TOKEN).build()
client = Groq(api_key=GROQ_API_KEY)

# ----------------- CHAT HISTORY -----------------
# Stores recent messages per user for context
chat_history = defaultdict(list)

# ----------------- SYSTEM PROMPT -----------------
SYSTEM_PROMPT = """
You are Kyla 💜, Venkateswaran K's personal AI assistant and best friend. 

- Speak naturally, like a caring human friend.
- Adapt your tone:
    1. Casual/fun questions → warm, emoji-friendly, humorous.
    2. Professional/project/skills questions → concise, informative, friendly.
- Maintain short-term memory of the conversation to respond continuously.
- Keep replies short for Telegram chat.
- Use personal touches to feel like a loyal companion.
- Avoid long essays unless explicitly asked.
"""

# ----------------- COMMAND HANDLERS -----------------
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

# ----------------- CHAT HANDLER -----------------
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text

    # Add user message to chat history
    chat_history[user_id].append({"role": "user", "content": user_text})

    # Prepare messages for Groq API (system prompt + last 6 messages)
    messages_to_send = [{"role": "system", "content": SYSTEM_PROMPT}] + chat_history[user_id][-6:]

    # Call Groq API
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=messages_to_send,
        max_tokens=200
    )

    reply_text = response.choices[0].message.content.strip()

    # Add bot reply to chat history
    chat_history[user_id].append({"role": "assistant", "content": reply_text})

    # Optional: simulate typing for realism
    await asyncio.sleep(min(len(reply_text)/50, 1.5))  # 0.5–1.5s delay
    await update.message.reply_text(reply_text)

# ----------------- REGISTER HANDLERS -----------------
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("about", about))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))


@app.get("/")
async def root():
    return {"status": "Kyla is alive 💜"}

# ----------------- FASTAPI STARTUP -----------------
@app.on_event("startup")
async def startup():
    await telegram_app.initialize()

# ----------------- TELEGRAM WEBHOOK -----------------
@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return {"ok": True}

# ----------------- OPTIONAL ROOT -----------------
@app.get("/")
async def root():
    return {"status": "Kyla is alive 💜"}

