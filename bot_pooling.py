"""
Полная версия бота для личных сообщений.
С кнопками и FSM, без необходимости упоминания.
"""
import os
import logging
from datetime import datetime

import aiomax
from aiomax import fsm
from aiomax.buttons import KeyboardBuilder, CallbackButton, LinkButton
from dotenv import load_dotenv

from rag_bot import answer_question

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


def get_level_keyboard() -> KeyboardBuilder:
    """Клавиатура выбора уровня образования (бакалавриат/магистратура)."""
    kb = KeyboardBuilder()
    kb.add(
        CallbackButton("🎓 Бакалавриат", "level:bachelor"),
        CallbackButton("📚 Магистратура", "level:master")
    )
    return kb


def get_faq_keyboard(level: str) -> KeyboardBuilder:
    """Клавиатура с частыми вопросами для выбранного уровня."""
    kb = KeyboardBuilder()
    if level == "master":
        kb.add(CallbackButton("📅 Сроки подачи", f"faq:{level}:сроки"))
        kb.row(CallbackButton("📝 Как подать заявление", f"faq:{level}:заявление"))
        kb.row(CallbackButton("📚 Вступительные испытания", f"faq:{level}:экзамен"))
        kb.row(CallbackButton("🎯 Приоритеты направлений", f"faq:{level}:приоритеты"))
        kb.row(CallbackButton("📋 Этапы поступления", f"faq:{level}:этапы"))
    else:  # bachelor
        kb.add(CallbackButton("📅 Сроки подачи", f"faq:{level}:сроки"))
        kb.row(CallbackButton("📝 Необходимые документы", f"faq:{level}:документы"))
        kb.row(CallbackButton("🏆 Олимпиады и льготы", f"faq:{level}:олимпиады"))
        kb.row(CallbackButton("📚 Вступительные испытания", f"faq:{level}:экзамен"))
        kb.row(CallbackButton("💰 Общежитие и стипендии", f"faq:{level}:общежитие"))
    
    kb.row(CallbackButton("🔄 Сменить уровень", "change_level"))
    return kb


def get_after_answer_keyboard(level: str) -> KeyboardBuilder:
    """Клавиатура после ответа на вопрос."""
    kb = KeyboardBuilder()
    kb.add(CallbackButton("❓ Другой вопрос", f"more:{level}"))
    kb.row(CallbackButton("🔄 Сменить уровень", "change_level"))
    kb.row(LinkButton("📞 Приёмная комиссия", "https://pk.mipt.ru/"))
    return kb


def get_contact_keyboard() -> KeyboardBuilder:
    """Клавиатура с контактами."""
    kb = KeyboardBuilder()
    kb.add(LinkButton("📞 Приёмная комиссия", "https://pk.mipt.ru/"))
    kb.row(CallbackButton("🔙 Назад", "change_level"))
    return kb


FAQ_QUESTIONS = {
    "master": {
        "сроки": {
            "question": "Расскажи про сроки подачи документов на магистратуру МФТИ в 2025 году",
            "source": "https://pk.mipt.ru/master/",
            "source_name": "Приёмная комиссия — Магистратура"
        },
        "заявление": {
            "question": "Как подать заявление на поступление в магистратуру МФТИ? Какие документы нужны?",
            "source": "https://pk.mipt.ru/master/docs/",
            "source_name": "Документы для поступления"
        },
        "экзамен": {
            "question": "Расскажи про вступительные испытания в магистратуру МФТИ. Какой формат экзамена?",
            "source": "https://pk.mipt.ru/master/exams/",
            "source_name": "Вступительные испытания"
        },
        "приоритеты": {
            "question": "Как правильно расставить приоритеты направлений при поступлении в магистратуру МФТИ?",
            "source": "https://pk.mipt.ru/master/",
            "source_name": "Приёмная комиссия — Магистратура"
        },
        "этапы": {
            "question": "Расскажи про этапы поступления в магистратуру МФТИ. Что нужно делать на каждом этапе?",
            "source": "https://pk.mipt.ru/master/",
            "source_name": "Приёмная комиссия — Магистратура"
        },
    },
    "bachelor": {
        "сроки": {
            "question": "Расскажи про сроки подачи документов на бакалавриат МФТИ в 2025 году",
            "source": "https://pk.mipt.ru/bachelor/",
            "source_name": "Приёмная комиссия — Бакалавриат"
        },
        "документы": {
            "question": "Какие документы нужны для поступления на бакалавриат МФТИ?",
            "source": "https://pk.mipt.ru/bachelor/docs/",
            "source_name": "Документы для поступления"
        },
        "олимпиады": {
            "question": "Расскажи про олимпиады, которые дают льготы при поступлении в МФТИ. Какие БВИ?",
            "source": "https://pk.mipt.ru/bachelor/olympics/",
            "source_name": "Олимпиады и льготы"
        },
        "экзамен": {
            "question": "Расскажи про вступительные испытания на бакалавриат МФТИ. Какие предметы ЕГЭ нужны?",
            "source": "https://pk.mipt.ru/bachelor/exams/",
            "source_name": "Вступительные испытания"
        },
        "общежитие": {
            "question": "Расскажи про общежитие и стипендии в МФТИ. Как получить место в общежитии?",
            "source": "https://pk.mipt.ru/bachelor/dormitory/",
            "source_name": "Общежитие"
        },
    }
}

WELCOME_MESSAGE = """👋 **Привет! Я бот-помощник по поступлению в МФТИ.**

🎓 Я помогу тебе разобраться с:
• Сроками и этапами поступления
• Подачей документов и заявлений
• Вступительными испытаниями
• Выбором направлений и приоритетов
• Олимпиадами и льготами
• Общежитием и стипендиями

📚 Я знаю правила приёма на **бакалавриат** и **магистратуру** МФТИ 2025 года.

Выбери уровень образования, чтобы я мог лучше помочь:"""


@bot.on_message()
async def handle_message(message: aiomax.Message, cursor: fsm.FSMCursor):
    """Обработка входящих сообщений в ЛС. Направляет пользователя по FSM."""
    text = (message.body.text or "").strip()
    user_id = message.sender.user_id
    current_state = cursor.get_state()

    if current_state is None:
        if tracker.add_user(user_id):
            main_logger.info(f"[НОВЫЙ] user_id={user_id} | {tracker.get_stats()}")
        user_logger.info(f"[{user_id}] Первое сообщение")
        cursor.change_state("greeted")
        await message.reply(WELCOME_MESSAGE, keyboard=get_level_keyboard())
        return
    
    tracker.add_user(user_id)

    if current_state == "greeted":
        user_logger.info(f"[{user_id}] Не выбрал уровень")
        await message.reply("👆 Сначала выбери уровень образования с помощью кнопок выше.", keyboard=get_level_keyboard())
        return

    if current_state != "waiting_question":
        return


@bot.on_bot_start()
async def on_bot_start(payload: aiomax.BotStartPayload, cursor: fsm.FSMCursor):
    """Обработка команды /start."""
    user_id = payload.user.user_id
    if tracker.add_user(user_id):
        main_logger.info(f"[НОВЫЙ] user_id={user_id} | {tracker.get_stats()}")
    user_logger.info(f"[{user_id}] /start")
    cursor.clear()
    cursor.change_state("greeted")
    await payload.send(WELCOME_MESSAGE, keyboard=get_level_keyboard())

@bot.on_button_callback()
async def handle_callback(callback: aiomax.Callback, cursor: fsm.FSMCursor):
    """Обработка нажатий кнопок: выбор уровня, FAQ, навигация."""
    payload = callback.payload
    user_id = callback.user.user_id
    user_logger.info(f"[{user_id}] Callback: {payload}")

    if payload.startswith("level:"):
        level = payload.split(":")[1]
        cursor.change_data({"level": level})
        cursor.change_state("waiting_question")
        level_name = "Бакалавриат" if level == "bachelor" else "Магистратура"
        user_logger.info(f"[{user_id}] Уровень: {level_name}")
        await callback.answer(f"Выбран: {level_name}")
        await callback.send(f"✅ Выбран уровень: **{level_name}**\n\nВыбери частый вопрос или напиши свой:", keyboard=get_faq_keyboard(level))

    elif payload == "change_level":
        cursor.clear()
        await callback.answer("Смена уровня")
        await callback.send("🔄 Выбери уровень образования:", keyboard=get_level_keyboard())

    elif payload.startswith("faq:"):
        parts = payload.split(":")
        level, topic = parts[1], parts[2]
        faq_data = FAQ_QUESTIONS.get(level, {}).get(topic)
        if faq_data:
            await callback.answer("Загрузка...")
            reply_text = answer_question(faq_data["question"], level=level)
            kb = KeyboardBuilder()
            kb.add(CallbackButton("❓ Другой вопрос", f"more:{level}"))
            if faq_data.get("source"):
                kb.row(LinkButton(f"📎 {faq_data.get('source_name', 'Источник')}", faq_data["source"]))
            kb.row(CallbackButton("🔄 Сменить уровень", "change_level"))
            await callback.send(f"{reply_text}\n\n---\n💡 *Подробнее смотри в источнике ниже*", keyboard=kb)
        else:
            await callback.answer("Вопрос не найден")

    elif payload.startswith("more:"):
        level = payload.split(":")[1]
        await callback.answer("Новый вопрос")
        await callback.send("❓ Выбери частый вопрос или напиши свой:", keyboard=get_faq_keyboard(level))

    else:
        await callback.answer("Неизвестная команда")


@bot.on_message(aiomax.filters.state("waiting_question"))
async def handle_free_question(message: aiomax.Message, cursor: fsm.FSMCursor):
    """Обработка свободных вопросов от пользователя."""
    text = (message.body.text or "").strip()
    user_id = message.sender.user_id

    if not text:
        return

    if len(text) > 500:
        await message.reply("Ваш вопрос слишком длинный. Пожалуйста, сформулируйте его короче.")
        return

    data = cursor.get_data() or {}
    level = data.get("level", "master")
    user_logger.info(f"[{user_id}] Вопрос ({level}): {text[:100]}...")

    try:
        reply_text = answer_question(text, level=level)
        user_logger.info(f"[{user_id}] Ответ: {len(reply_text)} симв.")
        await message.reply(reply_text, keyboard=get_after_answer_keyboard(level))
    except Exception as e:
        main_logger.error(f"[ОШИБКА] user_id={user_id} | {type(e).__name__}: {e}")
        await message.reply("Произошла ошибка при обработке запроса. Попробуйте позже.")


def main() -> None:
    main_logger.info("=" * 50)
    main_logger.info("[ЗАПУСК] Бот для ЛС (с кнопками и FSM)")
    main_logger.info("=" * 50)
    bot.run()


if __name__ == "__main__":
    main()