import os

import aiomax
from aiomax import fsm
from aiomax.buttons import KeyboardBuilder, CallbackButton, LinkButton
from dotenv import load_dotenv

from rag_bot import answer_question
from config import MAX_VK_BOT_USERNAME as BOT_USERNAME


load_dotenv("keys.env")


TOKEN = os.getenv("MAX_VK_BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("MAX_VK_BOT_TOKEN not found in keys.env")


bot = aiomax.Bot(TOKEN, default_format="markdown")


# ==================== КЛАВИАТУРЫ ====================

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


# ==================== FAQ ВОПРОСЫ ====================

FAQ_QUESTIONS = {
    "master": {
        "сроки": "Какие сроки подачи документов на магистратуру МФТИ в 2025 году?",
        "заявление": "Как подать заявление на поступление в магистратуру МФТИ?",
        "экзамен": "Какие вступительные испытания нужно сдавать в магистратуру МФТИ?",
        "приоритеты": "Как правильно расставить приоритеты направлений при поступлении в магистратуру?",
        "этапы": "Какие этапы поступления в магистратуру МФТИ?",
    },
    "bachelor": {
        "сроки": "Какие сроки подачи документов на бакалавриат МФТИ в 2025 году?",
        "документы": "Какие документы нужны для поступления на бакалавриат МФТИ?",
        "олимпиады": "Какие олимпиады дают льготы при поступлении в МФТИ?",
        "экзамен": "Какие вступительные испытания нужно сдавать на бакалавриат МФТИ?",
        "общежитие": "Как получить общежитие и стипендию в МФТИ?",
    }
}


# ==================== ОБРАБОТЧИКИ ====================

@bot.on_message()
async def handle_mention(message: aiomax.Message, cursor: fsm.FSMCursor):
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

    # Поддержка хэштегов выбора базы: #БАКАЛАВРИАТ / #БАКЛАВРИАТ / #МАГИСТРАТУРА (в начале текста)
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

        start_idx = s.lower().find(tag)
        if start_idx == -1:
            parts = s_strip.split(maxsplit=1)
            rest = parts[1] if len(parts) > 1 else ''
            return level, rest.strip()
        end_idx = start_idx + len(tag)
        rest = (s[:start_idx] + s[end_idx:]).strip()
        return level, rest

    level, cleaned = parse_level_and_text(cleaned)
    
    # Если уровень не указан в хэштеге, берём из FSM
    if level is None:
        data = cursor.get_data() or {}
        level = data.get("level")

    # Проверка на пустой запрос
    if not cleaned:
        await message.reply(
            "Задайте вопрос о поступлении в МФТИ после упоминания."
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
    
    # Добавляем клавиатуру после ответа
    kb = get_after_answer_keyboard(level or "master")
    await message.reply(reply_text, keyboard=kb)


@bot.on_bot_start()
async def on_bot_start(payload: aiomax.BotStartPayload, cursor: fsm.FSMCursor):
    """Приветственное сообщение при начале чата с ботом."""
    
    cursor.clear()  # Сбрасываем состояние
    
    kb = get_level_keyboard()
    await payload.send(
        "👋 Привет! Я бот-помощник по поступлению в МФТИ.\n\n"
        "Выбери уровень образования, чтобы я мог лучше помочь:",
        keyboard=kb
    )


@bot.on_button_callback()
async def handle_callback(callback: aiomax.Callback, cursor: fsm.FSMCursor):
    """Обрабатывает нажатия на кнопки."""
    
    payload = callback.payload
    
    # Выбор уровня образования
    if payload.startswith("level:"):
        level = payload.split(":")[1]
        cursor.change_data({"level": level})
        cursor.change_state("waiting_question")
        
        level_name = "Бакалавриат" if level == "bachelor" else "Магистратура"
        kb = get_faq_keyboard(level)
        
        await callback.answer(f"Выбран: {level_name}")
        await callback.send(
            f"✅ Выбран уровень: **{level_name}**\n\n"
            "Выбери частый вопрос или напиши свой:",
            keyboard=kb
        )
    
    # Смена уровня образования
    elif payload == "change_level":
        cursor.clear()
        kb = get_level_keyboard()
        
        await callback.answer("Смена уровня")
        await callback.send(
            "🔄 Выбери уровень образования:",
            keyboard=kb
        )
    
    # Быстрые FAQ вопросы
    elif payload.startswith("faq:"):
        parts = payload.split(":")
        level = parts[1]
        topic = parts[2]
        
        question = FAQ_QUESTIONS.get(level, {}).get(topic)
        if question:
            await callback.answer("Загрузка...")
            
            # Показываем индикатор набора
            await bot.post_action(callback.message.recipient.chat_id, "typing")
            
            # Получаем ответ
            reply_text = answer_question(question, level=level)
            kb = get_after_answer_keyboard(level)
            
            await callback.send(
                f"**Вопрос:** {question}\n\n{reply_text}",
                keyboard=kb
            )
        else:
            await callback.answer("Вопрос не найден")
    
    # Задать другой вопрос
    elif payload.startswith("more:"):
        level = payload.split(":")[1]
        kb = get_faq_keyboard(level)
        
        await callback.answer("Новый вопрос")
        await callback.send(
            "❓ Выбери частый вопрос или напиши свой:",
            keyboard=kb
        )
    
    else:
        await callback.answer("Неизвестная команда")


@bot.on_message(aiomax.filters.state("waiting_question"))
async def handle_free_question(message: aiomax.Message, cursor: fsm.FSMCursor):
    """Обрабатывает свободные вопросы в режиме ожидания (ЛС)."""
    
    text = (message.body.text or "").strip()
    
    # Пропускаем если это упоминание (обработается другим хэндлером)
    if f"@{BOT_USERNAME}" in text:
        return
    
    # Проверка на пустой запрос
    if not text:
        return
    
    # Проверка длины
    if len(text) > 500:
        await message.reply(
            "Ваш вопрос слишком длинный. Пожалуйста, сформулируйте его короче."
        )
        return
    
    data = cursor.get_data() or {}
    level = data.get("level", "master")
    
    # Показываем индикатор набора
    await bot.post_action(message.recipient.chat_id, "typing")
    
    # Получаем ответ
    reply_text = answer_question(text, level=level)
    kb = get_after_answer_keyboard(level)
    
    await message.reply(reply_text, keyboard=kb)


def main() -> None:
    print("Бот запущен на aiomax (VK/MAX API), ожидаю сообщения.")
    bot.run()


if __name__ == "__main__":
    main()