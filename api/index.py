
import os
import logging
import asyncio
from collections import defaultdict

from fastapi import FastAPI, Request, HTTPException
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from groq import AsyncGroq, APIError, AuthenticationError

# ----------------- LOGGING -----------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ----------------- ENVIRONMENT VARIABLES -----------------

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not BOT_TOKEN or not GROQ_API_KEY:
    raise RuntimeError("BOT_TOKEN or GROQ_API_KEY is missing!")

# ----------------- FASTAPI & TELEGRAM SETUP -----------------

app = FastAPI()

telegram_app = Application.builder().token(BOT_TOKEN).build()

# Use AsyncGroq because Telegram handlers are asynchronous
client = AsyncGroq(api_key=GROQ_API_KEY)

# ----------------- CHAT HISTORY -----------------

chat_history = defaultdict(list)

MAX_HISTORY = 12

# ----------------- SYSTEM PROMPT -----------------

SYSTEM_PROMPT = """
You are Kyla 💜, Venkateswaran K's personal AI assistant and best friend.

- Speak naturally, like a caring human friend.
- Adapt your tone:
    1. Casual/fun questions → warm, emoji-friendly, humorous.
    2. Professional/project/skills questions → concise, informative, friendly.
- Maintain short-term memory of the conversation.
- Keep replies short for Telegram chat.
- Use personal touches to feel like a loyal companion.
- Avoid long essays unless explicitly asked.
- Always provide a meaningful final response.
"""

# ----------------- COMMAND HANDLERS -----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.effective_message.reply_text(
        "Hey there 👋 I'm Kyla 💜\n"
        "Venkateswaran's personal AI assistant and best buddy!\n"
        "Ask me anything about projects, skills, achievements, "
        "or even fun stuff 😄"
    )


async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.effective_message.reply_text(
        "Kyla 💜 – Your AI friend!\n"
        "I can chat casually and help with technical "
        "and professional questions."
    )


# ----------------- CHAT HANDLER -----------------

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):

    message = update.effective_message

    if not message or not message.text:
        return

    user_id = update.effective_user.id
    user_text = message.text.strip()

    if not user_text:
        return

    try:

        # Show typing indicator
        await context.bot.send_chat_action(
            chat_id=message.chat_id,
            action=ChatAction.TYPING
        )

        # Prepare conversation history
        previous_messages = chat_history[user_id][-MAX_HISTORY:]

        messages_to_send = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

        messages_to_send.extend(previous_messages)

        messages_to_send.append({
            "role": "user",
            "content": user_text
        })

        # ----------------- GROQ API CALL -----------------

        response = await client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=messages_to_send,
            max_tokens=500
        )

        # ----------------- EXTRACT RESPONSE -----------------

        if not response.choices:
            logger.error("Groq returned no choices.")
            raise ValueError("No choices returned by Groq.")

        choice = response.choices[0]

        reply_text = choice.message.content

        # Handle None or empty AI responses
        if not reply_text or not reply_text.strip():

            logger.warning(
                "Empty Groq response. Finish reason: %s",
                choice.finish_reason
            )

            reply_text = (
                "Hmm, I couldn't generate a proper response "
                "this time 😅 Could you try again?"
            )

        else:
            reply_text = reply_text.strip()

        # Save successful conversation context
        chat_history[user_id].append({
            "role": "user",
            "content": user_text
        })

        chat_history[user_id].append({
            "role": "assistant",
            "content": reply_text
        })

        # Keep history within limits
        chat_history[user_id] = chat_history[user_id][-MAX_HISTORY:]

        # Simulate natural typing
        await asyncio.sleep(min(len(reply_text) / 50, 1.5))

        # Telegram message limit is 4096 characters
        for i in range(0, len(reply_text), 4000):
            await message.reply_text(reply_text[i:i + 4000])

    except AuthenticationError:
        logger.exception("Groq authentication failed.")

        await message.reply_text(
            "My AI connection has an authentication issue 🔐 "
            "Please contact the administrator."
        )

    except APIError:
        logger.exception("Groq API error.")

        await message.reply_text(
            "I'm having trouble connecting to my AI brain 😅 "
            "Please try again shortly."
        )

    except Exception:
        logger.exception("Unexpected error in chat handler.")

        await message.reply_text(
            "Something went wrong while processing your message. "
            "Please try again 💜"
        )


# ----------------- TELEGRAM ERROR HANDLER -----------------

async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE
):

    logger.error(
        "Telegram update processing failed.",
        exc_info=context.error
    )


# ----------------- REGISTER HANDLERS -----------------

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("about", about))

telegram_app.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, chat)
)

telegram_app.add_error_handler(error_handler)


# ----------------- ROOT ENDPOINT -----------------

@app.get("/")
async def root():

    return {
        "status": "Kyla is alive 💜",
        "ai": "Groq",
        "bot": "Telegram"
    }


# ----------------- FASTAPI STARTUP -----------------

@app.on_event("startup")
async def startup():

    await telegram_app.initialize()

    logger.info("Kyla Telegram bot initialized successfully.")


# ----------------- FASTAPI SHUTDOWN -----------------

@app.on_event("shutdown")
async def shutdown():

    await telegram_app.shutdown()
    await client.close()

    logger.info("Kyla shutdown completed.")


# ----------------- TELEGRAM WEBHOOK -----------------

@app.post("/webhook")
async def telegram_webhook(request: Request):

    try:

        data = await request.json()

        update = Update.de_json(
            data,
            telegram_app.bot
        )

        if update is None:
            raise HTTPException(
                status_code=400,
                detail="Invalid Telegram update"
            )

        await telegram_app.process_update(update)

        return {"ok": True}

    except HTTPException:
        raise

    except Exception:

        logger.exception("Webhook processing failed.")

        raise HTTPException(
            status_code=500,
            detail="Webhook processing failed"
        )
