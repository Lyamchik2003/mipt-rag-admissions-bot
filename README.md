# MAX_hackaton RAG Bot

Ассистент для абитуриентов МФТИ на платформе VK/MAX. Отвечает на вопросы по поступлению, используя RAG (FAISS + LLM).

## Требования

- Python 3.11+
- OpenAI-совместимый API (ключ + опционально кастомный URL)

## Быстрый старт

```powershell
# 1. Создать окружение
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 2. Настроить keys.env (см. ниже)

# 3. Собрать индексы
python setup_rag.py

# 4. Запустить бота
python bot_dm.py      # ЛС с кнопками
python bot_group.py   # Групповой чат (упоминания)
```

## Настройка (keys.env)

```env
MAX_VK_BOT_TOKEN=ваш_токен
MAX_VK_BOT_USERNAME=username_бота
OPENAI_API_KEY=sk-...
OPENAI_API_BASE=https://api.openai.com/v1  # опционально
```

## Структура проекта

```
├── bot_dm.py           # Бот для ЛС (кнопки + FSM)
├── bot_group.py        # Бот для групп (упоминания)
├── rag_bot_new.py      # RAG-пайплайн (ленивая загрузка)
├── settings.py         # Единая конфигурация
├── common.py           # Общие компоненты (логирование, трекер)
├── setup_rag.py        # Сборка FAISS-индексов
├── data/
│   ├── faq.json        # FAQ вопросы
│   ├── rules2025.json  # Данные бакалавриата
│   └── rules2025_magistratura_only.json  # Данные магистратуры
├── faiss_index/        # Базовый индекс
├── faiss_index_bachelor/
├── faiss_index_master/
└── keys.env            # Секреты 
```

## Конфигурация (settings.py)

Все параметры в одном месте:

| Параметр | Описание | По умолчанию |
|----------|----------|--------------|
| `openai.model` | Модель LLM | `gpt-4o-mini` |
| `openai.embedding_model` | Модель эмбеддингов | `text-embedding-ada-002` |
| `rag.retriever_k` | Кол-во документов для поиска | `7` |
| `rag.max_question_length` | Макс. длина вопроса | `500` |

## Два режима работы

### bot_dm.py — Личные сообщения
- Кнопки для выбора уровня (бакалавриат/магистратура)
- FAQ с быстрыми вопросами
- FSM для навигации
- Не требует упоминания

### bot_group.py — Групповой чат
- Только через упоминание `@username`
- Без кнопок
- Фиксированный уровень: магистратура

## Логирование

```
2025-11-26 04:15:23 - MAIN - INFO - [НОВЫЙ] user_id=123 | Пользователей: 5 | Uptime: 2ч 15м
2025-11-26 04:15:25 - USER - INFO - [123] Вопрос (master): какие сроки...
2025-11-26 04:15:30 - RAG - WARNING - [НЕТ ИНФО] level=master | Вопрос: про общежитие
```

Уровни логгеров:
- `MAIN` — системные события (новые пользователи, ошибки)
- `USER` — действия пользователей
- `RAG` — предупреждения о недостатке информации в базе

## Сборка индексов

```powershell
# Стандартная сборка
python setup_rag.py

# С кастомными путями
python setup_rag.py --bachelor data/rules2025.json --master data/rules2025_magistratura_only.json
```

## FAQ (data/faq.json)

Редактируется без изменения кода:

```json
{
  "master": {
    "сроки": {
      "question": "Расскажи про сроки подачи документов...",
      "source": "https://pk.mipt.ru/master/",
      "source_name": "Приёмная комиссия"
    }
  }
}
```

## Архитектура

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  bot_dm.py  │────▶│ rag_bot_new │────▶│   FAISS     │
│ bot_group.py│     │   .py       │     │   Index     │
└─────────────┘     └──────┬──────┘     └─────────────┘
                           │
                    ┌──────▼──────┐
                    │   OpenAI    │
                    │     LLM     │
                    └─────────────┘
```

**Ленивая загрузка**: Индексы и модели инициализируются при первом запросе, не при импорте.


