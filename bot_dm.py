"""Полная версия бота для личных сообщений. С кнопками и FSM."""
import json
import os

import aiomax
from aiomax import fsm
from aiomax.buttons import KeyboardBuilder, CallbackButton, LinkButton

from common import setup_logging, UserTracker
from rag_bot_new import answer_question
from settings import settings

main_logger, user_logger = setup_logging()
tracker = UserTracker()

if not settings.bot.token:
    raise RuntimeError("MAX_VK_BOT_TOKEN not found in keys.env")

bot = aiomax.Bot(settings.bot.token, default_format="markdown")

FAQ_PATH = os.path.join(os.path.dirname(__file__), "data", "faq.json")
with open(FAQ_PATH, encoding="utf-8") as f:
    FAQ_QUESTIONS = json.load(f)


def get_level_keyboard() -> KeyboardBuilder:
    """Клавиатура выбора уровня образования."""
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
    else:
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
    """Обработка входящих сообщений в ЛС."""
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
    """Обработка нажатий кнопок."""
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
    """Обработка свободных вопросов."""
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
