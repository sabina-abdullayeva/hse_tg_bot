import os

import httpx
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Привет! Я помогу ответить на вопросы о курсах бакалавриата НИУ ВШЭ.\n\n"
        "Просто напишите вопрос обычным текстом, например:\n"
        "Какие курсы есть на программе Экономика?\n"
        "Кто ведёт курс Python?\n"
        "Какие курсы на английском языке?"
    )


async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Команды не нужны. Просто напишите вопрос о курсах.")


async def answer_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    question = update.message.text.strip()
    thinking = await update.message.reply_text("Думаю...")

    try:
        api_url = os.getenv("API_URL", "http://127.0.0.1:8000")
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(f"{api_url}/ask", json={"question": question})
            response.raise_for_status()
            answer = response.json()["answer"]
    except Exception as error:
        answer = f"Не получилось ответить: {error}"

    await thinking.edit_text(answer)


def run() -> None:
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN is not set")

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.COMMAND, unknown_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, answer_question))
    app.run_polling()
