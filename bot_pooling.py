import os

import aiomax
from dotenv import load_dotenv

from rag_bot import answer_question
from config import MAX_VK_BOT_USERNAME as BOT_USERNAME


load_dotenv("keys.env")


TOKEN = os.getenv("MAX_VK_BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("MAX_VK_BOT_TOKEN not found in keys.env")


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

    # Поддержка хэштегов выбора базы: #БАКАЛАВРИАТ / #БАКЛАВРИАТ / #МАГИСТРАТУРА (в начале текста) - пока не работает
    def parse_level_and_text(s: str):
        s_strip = s.lstrip()
        lowered = s_strip.lower()
        level = None
        tag = None
        if lowered.startswith('#бакалавриат') or lowered.startswith('#баклавриат'):
            level = 'bachelor'
            tag = '#бакалавриат' if lowered.startswith('#бакалавриат') else '#баклавриат'
        elif lowered.startswith('#магистратура'):
            level = 'master'
            tag = '#магистратура'

        if level is None:
            return None, s

        # Отрезаем найденный тег в начале (с учётом реального регистра/пробелов)
        # Находим индекс начала тега в исходной строке s
        start_idx = s.lower().find(tag)
        if start_idx == -1:
            # fallback: просто удалим первое слово как тег
            parts = s_strip.split(maxsplit=1)
            rest = parts[1] if len(parts) > 1 else ''
            return level, rest.strip()
        end_idx = start_idx + len(tag)
        rest = (s[:start_idx] + s[end_idx:]).strip()
        return level, rest

    level, cleaned = parse_level_and_text(cleaned)

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

    # Получаем и отправляем ответ из RAG-бота (с учётом выбранной базы)
    reply_text = answer_question(cleaned, level=level)
    await message.reply(reply_text)


@bot.on_bot_start()
async def on_bot_start(payload: aiomax.BotStartPayload):
    """Приветственное сообщение при начале чата с ботом."""

    await payload.send(
        "Привет! Я бот-помощник поступления в МФТИ.\n"
        f"Чтобы выбрать базу знаний, начни вопрос с хэштега: #БАКАЛАВРИАТ (или #БАКЛАВРИАТ) либо #МАГИСТРАТУРА.\n"
        f"Если хэштега нет — отвечу из базовой базы.\n\n"
        f"В чате упомяни меня через @{BOT_USERNAME} и задай вопрос."
    )


def main() -> None:
    print("Бот запущен на aiomax (VK/MAX API), ожидаю сообщения с упоминанием.")
    bot.run()


if __name__ == "__main__":
    main()