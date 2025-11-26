"""
Лайт-версия бота для групповых чатов.
Взаимодействие только через упоминание @username.
Без кнопок и FSM.
"""
import os
import logging
from datetime import datetime

import aiomax
from dotenv import load_dotenv

from rag_bot import answer_question
from config import MAX_VK_BOT_USERNAME as BOT_USERNAME

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
main_logger = logging.getLogger('MAIN')
user_logger = logging.getLogger('USER')
logging.getLogger('aiomax').setLevel(logging.WARNING)
logging.getLogger('aiohttp').setLevel(logging.WARNING)


class UserTracker:
    """Трекер уникальных пользователей за сессию."""
    
    def __init__(self):
        self.active_users: set[int] = set()
        self.start_time: datetime = datetime.now()
    
    def add_user(self, user_id: int) -> bool:
        """Регистрирует пользователя. Возвращает True если новый."""
        is_new = user_id not in self.active_users
        self.active_users.add(user_id)
        return is_new
    
    @property
    def count(self) -> int:
        return len(self.active_users)
    
    def get_stats(self) -> str:
        uptime = datetime.now() - self.start_time
        h, rem = divmod(int(uptime.total_seconds()), 3600)
        m, s = divmod(rem, 60)
        return f"Пользователей: {self.count} | Uptime: {h}ч {m}м"


tracker = UserTracker()

load_dotenv("keys.env")
TOKEN = os.getenv("MAX_VK_BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("MAX_VK_BOT_TOKEN not found in keys.env")

bot = aiomax.Bot(TOKEN, default_format="markdown")

WELCOME_MESSAGE = """👋 **Привет! Я бот-помощник по поступлению в магистратуру МФТИ.**

🎓 Я помогу тебе разобраться с:
• Сроками и этапами поступления
• Подачей документов и заявлений
• Вступительными испытаниями
• Выбором направлений и приоритетов

📚 Я знаю правила приёма в **магистратуру** МФТИ 2025 года.

💬 Чтобы задать вопрос, упомяни меня: @{bot_username} <твой вопрос>

Например: @{bot_username} какие сроки подачи документов?
""".format(bot_username=BOT_USERNAME)

LEVEL = "master"


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
        await message.reply("Ваш вопрос слишком длинный. Пожалуйста, сформулируйте его короче (до 500 символов).")
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
    main_logger.info("=" * 50)
    main_logger.info(f"[ЗАПУСК] Групповой бот | @{BOT_USERNAME} | level={LEVEL}")
    main_logger.info("=" * 50)
    bot.run()


if __name__ == "__main__":
    main()
