"""Лайт-версия бота для групповых чатов. Только упоминания, без кнопок."""
import aiomax

from common import setup_logging, UserTracker
from rag_bot_new import answer_question
from settings import settings
from tests import run_startup_tests

main_logger, user_logger = setup_logging()
tracker = UserTracker()

BOT_USERNAME = settings.bot.username
LEVEL = "master"

if not settings.bot.token:
    raise RuntimeError("MAX_VK_BOT_TOKEN not found in keys.env")

bot = aiomax.Bot(settings.bot.token, default_format="markdown")

WELCOME_MESSAGE = f"""👋 **Привет! Я бот-помощник по поступлению в магистратуру МФТИ.**

🎓 Я помогу тебе разобраться с:
• Сроками и этапами поступления
• Подачей документов и заявлений
• Вступительными испытаниями
• Выбором направлений и приоритетов

📚 Я знаю правила приёма в **магистратуру** МФТИ 2025 года.

💬 Чтобы задать вопрос, упомяни меня: @{BOT_USERNAME} <твой вопрос>

Например: @{BOT_USERNAME} какие сроки подачи документов?
"""


@bot.on_message()
async def handle_message(message: aiomax.Message):
    """Обработка сообщений с упоминанием бота."""
    text = (message.body.text or "").strip()

    if f"@{BOT_USERNAME}" not in text:
        return
    
    user_id = message.sender.user_id
    
    if tracker.add_user(user_id):
        main_logger.info(f"[НОВЫЙ] user_id={user_id} | {tracker.get_stats()}")
    
    user_logger.info(f"[{user_id}] Сообщение: {text[:100]}...")

    if text.count(f"@{BOT_USERNAME}") > 1:
        user_logger.info(f"[{user_id}] Множественные упоминания")
        await message.reply("⚠️ Пожалуйста, упоминайте меня только один раз в сообщении.")
        return

    cleaned = text.replace(f"@{BOT_USERNAME}", "").strip()

    if not cleaned:
        user_logger.info(f"[{user_id}] Пустой запрос")
        await message.reply(WELCOME_MESSAGE)
        return

    if len(cleaned) > 500:
        user_logger.info(f"[{user_id}] Слишком длинный ({len(cleaned)} симв.)")
        await message.reply("📝 Вопрос слишком длинный. Пожалуйста, сформулируйте короче (до 500 символов).")
        return
    
    user_logger.info(f"[{user_id}] Вопрос: {cleaned[:100]}...")
    
    try:
        reply_text = answer_question(cleaned, level=LEVEL)
        user_logger.info(f"[{user_id}] Ответ: {len(reply_text)} симв.")
        await message.reply(reply_text)
    except Exception as e:
        main_logger.error(f"[ОШИБКА] user_id={user_id} | {type(e).__name__}: {e}")
        await message.reply("Произошла ошибка при обработке запроса. Попробуйте позже.")


@bot.on_bot_start()
async def on_bot_start(payload: aiomax.BotStartPayload):
    """Обработка команды /start."""
    user_id = payload.user.user_id
    if tracker.add_user(user_id):
        main_logger.info(f"[НОВЫЙ] user_id={user_id} | {tracker.get_stats()}")
    user_logger.info(f"[{user_id}] /start")
    await payload.send(WELCOME_MESSAGE)


@bot.on_bot_add()
async def on_bot_add(chat: aiomax.Chat):
    """Приветствие при добавлении бота в чат."""
    main_logger.info(f"[ДОБАВЛЕН] chat_id={chat.chat_id}")
    await bot.send_message(chat_id=chat.chat_id, text=WELCOME_MESSAGE)


def main() -> None:
    run_startup_tests()
    main_logger.info("=" * 50)
    main_logger.info(f"[ЗАПУСК] Групповой бот | @{BOT_USERNAME} | level={LEVEL}")
    main_logger.info("=" * 50)
    bot.run()


if __name__ == "__main__":
    main()
