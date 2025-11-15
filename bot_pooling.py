import os

import aiomax
from dotenv import load_dotenv

from rag_bot import answer_question


load_dotenv("keys.env")


TOKEN = os.getenv("MAX_VK_BOT_TOKEN")
BOT_USERNAME = os.getenv("MAX_VK_BOT_USERNAME")

if not TOKEN:
    raise RuntimeError("MAX_VK_BOT_TOKEN not found in keys.env")

if not BOT_USERNAME:
    raise RuntimeError("MAX_VK_BOT_USERNAME not found in keys.env")


bot = aiomax.Bot(TOKEN, default_format="markdown")


@bot.on_message()
async def handle_mention(message: aiomax.Message):
    """Обрабатывает сообщения с упоминанием бота и отвечает через RAG."""

    text = (message.body.text or "").strip()

    # Если в сообщении нет упоминания бота — просто игнорируем
    if f"@{BOT_USERNAME}" not in text:
        return

    # Проверка на множественные упоминания
    mention_count = text.count(f"@{BOT_USERNAME}")
    if mention_count > 1:
        await message.reply(
            "⚠️ Пожалуйста, упоминайте меня только один раз в сообщении.⚠️"
        )
        return

    # Удаляем упоминание из текста
    cleaned = text.replace(f"@{BOT_USERNAME}", "").strip()

    # Проверка на пустой запрос
    if not cleaned:
        await message.reply(
            "Задайте вопрос о поступлении в магистратуру МФТИ после упоминания."
        )
        return

    # Проверка длины запроса
    if len(cleaned) > 500:
        await message.reply(
            "Ваш вопрос слишком длинный. Пожалуйста, сформулируйте его короче."
        )
        return

    # Получаем и отправляем ответ из RAG-бота
    reply_text = answer_question(cleaned)
    await message.reply(reply_text)


@bot.on_bot_start()
async def on_bot_start(payload: aiomax.BotStartPayload):
    """Приветственное сообщение при начале чата с ботом."""

    await payload.send(
        "Привет! Я бот, который помогает с вопросами о поступлении в магистратуру МФТИ.\n"
        f"Просто упомяни меня через @{BOT_USERNAME} и задай вопрос."
    )


def main() -> None:
    print("Бот запущен на aiomax (VK/MAX API), ожидаю сообщения с упоминанием.")
    bot.run()


if __name__ == "__main__":
    main()
