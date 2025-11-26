"""
Полная версия бота для личных сообщений.
С кнопками и FSM, без необходимости упоминания.
"""
import os

import aiomax
from aiomax import fsm
from aiomax.buttons import KeyboardBuilder, CallbackButton, LinkButton
from dotenv import load_dotenv

from rag_bot import answer_question


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

# Структура: { topic: { "question": текст запроса, "source": ссылка на источник } }
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


# ==================== ПРИВЕТСТВЕННОЕ СООБЩЕНИЕ ====================

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


# ==================== ОБРАБОТЧИКИ ====================

@bot.on_message()
async def handle_message(message: aiomax.Message, cursor: fsm.FSMCursor):
    """Обрабатывает все входящие сообщения в ЛС."""

    text = (message.body.text or "").strip()
    
    # Проверяем, новый ли это пользователь (нет состояния)
    current_state = cursor.get_state()
    
    # Если пользователь новый — показываем приветствие
    if current_state is None:
        kb = get_level_keyboard()
        cursor.change_state("greeted")
        await message.reply(WELCOME_MESSAGE, keyboard=kb)
        return
    
    # Если пользователь только поприветствован, но не выбрал уровень — напоминаем
    if current_state == "greeted":
        kb = get_level_keyboard()
        await message.reply(
            "👆 Сначала выбери уровень образования с помощью кнопок выше.",
            keyboard=kb
        )
        return
    
    # Если пользователь не в состоянии ожидания вопроса — пропускаем
    # (обработается в handle_free_question)
    if current_state != "waiting_question":
        return


@bot.on_bot_start()
async def on_bot_start(payload: aiomax.BotStartPayload, cursor: fsm.FSMCursor):
    """Приветственное сообщение при начале чата с ботом."""
    
    cursor.clear()  # Сбрасываем состояние
    cursor.change_state("greeted")
    
    kb = get_level_keyboard()
    await payload.send(WELCOME_MESSAGE, keyboard=kb)

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
        
        faq_data = FAQ_QUESTIONS.get(level, {}).get(topic)
        if faq_data:
            await callback.answer("Загрузка...")
            
            # Получаем данные FAQ
            question = faq_data["question"]
            source_url = faq_data.get("source", "")
            source_name = faq_data.get("source_name", "Источник")
            
            # Получаем ответ от RAG
            reply_text = answer_question(question, level=level)
            
            # Формируем клавиатуру с источником
            kb = KeyboardBuilder()
            kb.add(CallbackButton("❓ Другой вопрос", f"more:{level}"))
            if source_url:
                kb.row(LinkButton(f"📎 {source_name}", source_url))
            kb.row(CallbackButton("🔄 Сменить уровень", "change_level"))
            
            await callback.send(
                f"{reply_text}\n\n"
                f"---\n"
                f"💡 *Подробнее смотри в источнике ниже*",
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
    
    # Получаем ответ
    reply_text = answer_question(text, level=level)
    kb = get_after_answer_keyboard(level)
    
    await message.reply(reply_text, keyboard=kb)


def main() -> None:
    print("Бот запущен на aiomax (VK/MAX API), ожидаю сообщения.")
    bot.run()


if __name__ == "__main__":
    main()