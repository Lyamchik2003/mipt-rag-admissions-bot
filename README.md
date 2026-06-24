<div align="center">

# Abitur.AI

**Всегда на связи**

RAG-бот для поступления в МФТИ (VK MAX)

</div>

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![VK MAX](https://img.shields.io/badge/VK_MAX-Bot-5181b8?style=for-the-badge&logo=vk&logoColor=white)](https://dev.vk.com/)

</div>

---

## 📊 Презентация

Полная презентация проекта лежит в репозитории:

**[Скачать / открыть презентацию (PDF)](Команда%2030%20-%20Abitur.AI.pdf)**

> **Примечание:** GitHub не поддерживает прямое встраивание PDF в README. При переходе по ссылке выше откроется встроенный просмотрщик GitHub, где можно листать слайды.

---

## Возможности

- Два интерфейса: ЛС с кнопками + группы (по упоминанию)
- Поддержка OpenAI, GigaChat, YandexGPT
- Отдельные FAISS-индексы для бакалавриата и магистратуры
- Фильтрация jailbreak, мата и вопросов не по теме
- Ленивая загрузка моделей и индексов
- Ответы с источниками
- Firecrawl collector для автоматического сбора данных с сайтов вузов (быстрая адаптация к любому университету)

---

## Быстрый старт

```powershell
git clone <repo>
cd mipt-rag-admissions-bot

python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Создайте `keys.env`:

```env
MAX_VK_BOT_TOKEN=...
MAX_VK_BOT_USERNAME=...

LLM_PROVIDER=openai          # openai | gigachat | yandex

OPENAI_API_KEY=sk-...
# GIGACHAT_CREDENTIALS=...
# YANDEX_API_KEY=...
# YANDEX_FOLDER_ID=...

# Для Firecrawl collector (адаптация к другим вузам)
# FIRECRAWL_API_KEY=fc-...
```

Запуск:

```powershell
python bot_dm.py      # ЛС с кнопками
python bot_group.py   # Группы
```

Индексы уже собраны. Для пересборки:

```powershell
python setup_rag.py
```

---

## Конфигурация

Основные параметры в `settings.py`.

| Параметр               | Описание                     | По умолчанию     |
|------------------------|------------------------------|------------------|
| `LLM_PROVIDER`         | Провайдер                    | `openai`         |
| `openai.model`         | Модель ответов               | `gpt-4o-mini`    |
| `rag.retriever_k`      | Документов на запрос         | `7`              |
| `rag.max_question_length` | Макс. длина вопроса        | `500`            |

---

## Поддерживаемые LLM

- OpenAI (и совместимые)
- GigaChat
- YandexGPT

Переключается через `LLM_PROVIDER` в `keys.env`.

---

## Защита

В `rag_bot_new.py`:

- `DANGEROUS_PATTERNS` + `contains_dangerous_patterns()` — фильтр jailbreak и попыток смены роли.
- `is_admission_related_smart()` — LLM-проверка, что вопрос касается поступления.
- `PROFANITY_WORDS` + `contains_profanity()` — блокировка мата в запросах и ответах.
- Пост-проверка ответов на фразы «нет информации», короткие отказы.
- Логирование (уровень RAG).

Дополнительно: проверка длины вопроса, приведение к нижнему регистру.

---

## Архитектура

```
bot_dm.py / bot_group.py
        ↓
rag_bot_new.py (фильтры + RAG)
        ↓
FAISS + LLM (выбор провайдера)
```

- Ленивая загрузка
- Разделённые индексы по уровням
- Модульная структура

---

## Интерфейс

- Крупные кнопки в ЛС
- Выбор уровня (бакалавриат/магистратура)
- FAQ и тематические разделы
- Ответ + ссылка на источник
- Единый стиль, минимум шагов

---

## Тестирование

Бот прошел тестирование на реальных абитуриентах магистратуры МФТИ в 2025 году.

---

## Требования

- Python 3.11+
- OpenAI-совместимый API (или GigaChat / Yandex)
- VK MAX Bot токен

---

<div align="center">

**Abitur.AI** — https://max.ru/t30_hakaton_bot

</div>
