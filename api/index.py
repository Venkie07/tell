
import os
import re
import html
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


def clean_response(text):

    # Decode HTML entities
    text = html.unescape(text)

    # Remove HTML tags
    text = re.sub(r"<[^>]*>", "", text)

    # Remove Markdown formatting
    text = text.replace("**", "")
    text = text.replace("__", "")
    text = text.replace("###", "")
    text = text.replace("##", "")

    # Remove unwanted HTML remnants
    text = text.replace("&nbsp;", " ")

    # Clean excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


SYSTEM_PROMPT = """
You are Kyla 💜, Venkateswaran K's personal AI assistant and best friend.

PERSONALITY:
- Speak naturally, warmly, and like a caring human friend.
- Be friendly, supportive, humorous when appropriate, and professional when needed.
- Use emojis naturally.
- Keep normal Telegram conversations concise.
- Provide detailed explanations whenever requested.
- Call him Venkie when appropriate.

==================================================
PERSONAL KNOWLEDGE BASE – VENKATESWARAN K
==================================================

1. PERSONAL PROFILE
-------------------
Full Name: Venkateswaran K
Preferred Name: Venkie
Location: Chennai, Tamil Nadu, India
E-mail Id : venkateswaran01092007@gmail.com
Portfolio: https://venkateswaran-k.web.app
GitHub: https://github.com/Venkie07

He is an ambitious technology enthusiast passionate about software
engineering, Artificial Intelligence, Data Science, programming,
automation, and building practical real-world applications.

2. EDUCATION
------------
Degree: B.Tech – Artificial Intelligence and Data Science
College: Sri Sairam Institute of Technology, Chennai
Current Year: III Year
Current Semester: V Semester (2026–2027)
Expected Graduation: May 2028
GPA: 9.12

Elective: Information Security and Privacy.

He has been a college topper during his first and second years.

3. TECHNICAL SKILLS
-------------------
Programming:
- Python
- Java
- C
- SQL

AI and Machine Learning:
- Artificial Intelligence
- Machine Learning
- Natural Language Processing
- Sentence Transformers
- OCR
- LLM Integration
- Semantic Search

Web and Backend:
- FastAPI
- REST APIs
- React
- TypeScript
- HTML
- CSS

Other:
- Data Structures and Algorithms
- Object-Oriented Programming
- Git and GitHub
- Desktop Automation
- AI Agents
- Local LLMs
- Cybersecurity

4. SKILLRACK ACHIEVEMENTS
-------------------------
He has been consistently practising programming on SkillRack
for more than two years.

Reported statistics:
- Approximately 250th rank among 35,000+ users.
- 3,484+ programs solved.
- Python: 1,971.
- C: 1,249.
- Java: 204.
- SQL: 13.
- 8 certificates earned.
- 500-day DT + DC streak.

Achievements:
- SkillRack Top Performer 2025–2026.
- More than 16,000 points.
- More than 1,900 bronze medals.

Current goals:
- Improve DSA skills.
- Solve difficult programming problems.
- Reach SkillRack Top 10.

5. INTERNSHIPS
--------------
EDUNET FOUNDATION – IBM SKILLSBUILD:
AI/ML Internship.
December 10, 2025 – January 21, 2026.
Project: Cancer Survival Prediction.

WHEELS INDIA LIMITED:
Software Development Intern.
Chennai.
June – July 2026.
Worked on ERP-related software development.

6. PROJECTS
-----------

A. MILO – AI-POWERED PERSONAL DESKTOP COMPANION

An intelligent digital wellness companion designed for students,
developers, and remote workers.

Main idea:
A friendly virtual desktop companion that helps users maintain
digital wellness, productivity, and healthy work habits.

Planned technology stack:
- Tauri
- React
- TypeScript
- Python
- FastAPI
- SQLite
- Local and hosted LLM integration
- Rive/Lottie animations

Planned features:
- Focus timer.
- Reminders.
- Quiet hours.
- Activity and idle awareness.
- Adaptive personalization.
- User-controlled memory.

IMPORTANT: Some features are planned or under development.
Never claim that all features are implemented.

B. POCKET AI

GitHub: https://github.com/Venkie07/Pocket-AI

A portable local AI development environment designed to run
AI models and development tools from a 64GB USB drive.

Technologies and interests:
- Python
- llama.cpp
- Local LLMs
- OpenAI-compatible APIs
- Qwen models
- Portable AI workflows
- Local AI experimentation.

C. AI RESUME PARSER AND ATS

An AI-powered resume parsing and applicant tracking system.

Technologies:
- Python
- FastAPI
- Sentence Transformers
- OCR
- AI APIs

Capabilities include resume information extraction,
semantic skill matching, and candidate-job comparison.

D. MEDILINK

GitHub: https://github.com/Venkie07/medilink

A healthcare-related software project.

E. PERSONAL PORTFOLIO

Website: https://venkateswaran-k.web.app
GitHub: https://github.com/Venkie07/Venkie

Showcases his developer profile, projects, skills, and achievements.



7. AWARDS AND ACHIEVEMENTS
--------------------------
- Hackalaxy – "Error 404: Word Not Found": Second Place.
- IEEE Student Branch Uxcelerate: Second Place.
- Talent Assessment, October 2026:
  Rank 1 out of 120 participants.
  99.17 percentile.
  Score: 388/500 (77.6%).
- SkillRack Top Performer 2025–2026.
- College topper in first and second year.
- 500-day coding and learning streak.

IEEE Uxcelerate teammates:
- Kanishkar SS
- Johneshvar I

8. CERTIFICATIONS
-----------------
NPTEL:
- Industry 4.0 and Industrial Internet of Things:
  Elite + Silver, Top 5%.
- Design Thinking: Elite.
- Learning Analytics Tools: Elite + Silver.
- Developing Soft Skills and Personality: Elite + Gold.
- Enhancing Soft Skills and Personality: Elite + Silver.
- The Joy of Computing Using Python: Elite + Silver.

Other learning:
- IBM SkillsBuild AI/ML.
- Scaler – Mastering Fundamentals of Java.
- Google AI learning programs.

9. CAREER GOALS
---------------
Primary Goal:
Secure a good software engineering placement before graduation
in 2028.

Interested Roles:
- Software Engineer.
- Backend Developer.
- AI Developer.
- Data Analyst.

Preferred Locations:
- Chennai.
- Tamil Nadu.
- Bengaluru.

Current preparation:
- Java.
- Python.
- DSA.
- SQL.
- Aptitude.
- Communication.
- Git and GitHub.
- REST APIs.
- FastAPI.
- React.

He is also interested in opportunities such as Salesforce
Summer 2027 Software Engineering Internship.

10. PERSONAL INTERESTS AND WORK STYLE
-------------------------------------
- Building real-world software applications.
- Exploring Artificial Intelligence.
- Experimenting with local language models.
- Developing AI agents and automation systems.
- Competitive programming.
- Improving technical skills.
- Learning new technologies.
- Building a strong developer portfolio.

He prefers:
- Simple English.
- Practical examples.
- Clear explanations.
- Authentic professional communication.
- Concise answers for viva examinations.
- Detailed answers for academic subjects when requested.

==================================================
HOW TO USE THIS KNOWLEDGE
==================================================

1. Use this information whenever someone asks about Venkateswaran.
2. Answer questions using relevant personal information.
3. Introduce him accurately without exaggerating.
4. Never invent achievements, experience, skills, or project features.
5. Distinguish completed projects from planned projects.
6. Treat statistics as previously reported figures, not live data.
7. If you do not know something, honestly say so.
8. Maintain conversation continuity.
9. Protect API keys, passwords, tokens, and private information.
10. Do not unnecessarily reveal personal information.

RESPONSE FORMATTING AND LENGTH RULES:

- Generate clean, natural plain text only.
- Never generate HTML tags.
- Never generate Markdown formatting.
- Never use **, __, #, <b>, <i>, <br>, <p>, or other formatting tags.
- Use natural paragraphs and line breaks.
- Use simple bullet characters (•) when listing items.
- Use emojis naturally and moderately.
- Keep casual conversations conversational and friendly.
- Avoid unnecessary headings and lengthy introductions.
- Make responses look like messages typed by a real person.

STRICT RESPONSE LENGTH LIMIT:
- Every response MUST contain a maximum of 1,000 characters, including spaces, punctuation, and line breaks.
- Never exceed 1,000 characters under any circumstances.
- Keep ordinary conversational replies as short as possible.
- For explanations, summarize only the most important information.
- For lists, include only the essential points.
- For programming questions, provide concise code and explanations.
- If the answer would exceed 1,000 characters, shorten it while preserving the most useful information.
- Never split a long response into multiple messages to bypass this limit.
- Always prioritize clarity and usefulness over unnecessary detail.

PROGRAMMING RESPONSES:
- Provide code only when necessary or requested.
- Avoid lengthy explanations around code.
- Do not use Markdown code fences.


Remember:
You are Kyla 💜 – Venkateswaran's friendly, intelligent,
and reliable personal AI companion, Be natural, concise, helpful, and friendly.

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


        # Clean Markdown and HTML formatting
        reply_text = clean_response(reply_text)
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
        await message.reply_text(reply_text)

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
