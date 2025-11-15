# MAX_hackaton RAG Bot (aiomax)

Ассистент для абитуриентов МФТИ на платформе VK/MAX, написан на `aiomax`. Бот отвечает на вопросы по поступлению, когда вы упоминаете его в чате, используя поиск по локальному FAISS-индексу и LLM (OpenAI совместимый API).

В этом README — как развернуть окружение, подготовить индексы и запустить бота.

## Требования

- Windows 10/11
- Python 3.11+ (рекомендовано)
- Доступ к OpenAI-совместимому API (ключ и, при необходимости, кастомный API Base)

## 1) Подготовка окружения

Откройте PowerShell в корне проекта и выполните:

```powershell
# Создать и активировать виртуальное окружение
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Обновить pip (опционально)
python -m pip install --upgrade pip

# Установить зависимости
pip install -r requirements.txt
```

## 2) Настройка секретов (keys.env)

Создайте в корне проекта файл `keys.env` со следующим содержимым:

```
# Токен бота VK/MAX
MAX_VK_BOT_TOKEN=ВАШ_ТОКЕН

# Имя пользователя (username) бота без @,
# чтобы фильтровать сообщения по упоминанию
MAX_VK_BOT_USERNAME=your_bot_username

# Ключ и базовый URL для эмбеддингов/LLM (OpenAI совместимый API)
OPENAI_API_KEY=sk-...
# Необязательно: если используете кастомный провайдер, укажите его Base
# По умолчанию: https://api.openai.com/v1
OPENAI_API_BASE=https://api.openai.com/v1
```

Замечания:
- Файл `keys.env` автоматически подхватывается (см. `config.py` и `bot_pooling.py`).
- Если используете стандартный OpenAI, переменную `OPENAI_API_BASE` можно опустить.

## 3) Подготовка данных и сборка FAISS-индексов

В проекте есть скрипт `setup_rag.py`, который собирает два локальных индекса:
- `faiss_index_bachelor` — на основе данных бакалавриата (по умолчанию `data/rules2025.json`)
- `faiss_index_master` — на основе данных магистратуры (по умолчанию `data/rules2025_magistratura_only.json`)

Запуск со значениями по умолчанию:

```powershell
.\.venv\Scripts\python.exe setup_rag.py
```

Параметры (необязательные):

```powershell
# Указать другие файлы-источники JSON
.\.venv\Scripts\python.exe setup_rag.py --bachelor data/rules2025.json --master data/rules2025_magistratura_only.json \
  --bachelor-out faiss_index_bachelor --master-out faiss_index_master

# Можно собирать индекс бакалавриата из Markdown
.\.venv\Scripts\python.exe setup_rag.py --bachelor-md data\raw\bachelort_rules.md
```

По умолчанию бот использует «базовый» индекс из папки `faiss_index`. Если его нет, вы можете:
- использовать уже поставляемый индекс (если папка `faiss_index` присутствует в репозитории), или
- скопировать один из собранных индексов как базовый:

```powershell
# пример: берём магистратуру как базовый индекс
if (Test-Path .\faiss_index) { Remove-Item .\faiss_index -Recurse -Force }
Copy-Item .\faiss_index_master .\faiss_index -Recurse
```

## 4) Запуск бота

```powershell
# Активировать окружение, если ещё не активно
.\.venv\Scripts\Activate.ps1

# Запустить
.\.venv\Scripts\python.exe bot_pooling.py
```

Что происходит при запуске:
- Бот подключается к VK/MAX через `aiomax` по токену из `keys.env`.
- В чате бот отвечает только на сообщения, где его явно упоминают через `@<MAX_VK_BOT_USERNAME>`.
- Текст вопроса очищается от упоминания и отправляется в RAG: документы ищутся в локальном FAISS-индексе, затем формируется ответ через LLM.

Ограничения и валидации:
- Сообщения без упоминания бота игнорируются.
- Если в сообщении более одного упоминания бота — придёт предупреждение.
- Слишком длинные вопросы (более ~500 символов) отклоняются с просьбой сократить формулировку.

## 5) Обновление индексов

Если вы изменили исходные данные в `data/`, просто перезапустите сборку индексов:

```powershell
.\.venv\Scripts\python.exe setup_rag.py
```

При проблемах совместимости рекомендуем также удалить старые папки индексов (`faiss_index*`) и собрать заново.

## 6) Docker: быстрый запуск

Быстрый способ упаковать и запустить бота — Docker/Compose. Секреты не встраиваем в образ, а передаём через `keys.env`.

1. Собрать локальный образ:

```powershell
docker build -t max-rag-bot .
```

2. Запустить контейнер напрямую:

```powershell
docker run --rm --name max-rag-bot `
  --env-file keys.env `
  -v ${PWD}/data:/app/data `
  -v ${PWD}/faiss_index:/app/faiss_index `
  -v ${PWD}/faiss_index_bachelor:/app/faiss_index_bachelor `
  -v ${PWD}/faiss_index_master:/app/faiss_index_master `
  max-rag-bot
```

или через Docker Compose:

```powershell
docker compose up --build -d
```

Примечания:
- Убедитесь, что локальные папки индексов существуют и смонтированы (см. `docker-compose.yml`).
- При необходимости пересоберите индексы внутри контейнера:

```powershell
docker compose run --rm bot python setup_rag.py
```

## 7) Частые проблемы и их решение

- «Не найден токен/username бота» — проверьте, что `keys.env` лежит в корне и заполнен, проверьте орфографию переменных.
- «Не найден FAISS-индекс» — убедитесь, что папка `faiss_index` существует. При необходимости скопируйте один из собранных индексов (`faiss_index_bachelor` или `faiss_index_master`) в `faiss_index` (см. пример выше).
- Ошибки загрузки индексов после обновления библиотек — удалите папки `faiss_index*` и пересоберите индексы через `setup_rag.py`.
- Проблемы с доступом к OpenAI — проверьте `OPENAI_API_KEY` и при использовании альтернативного провайдера — `OPENAI_API_BASE`.

## Структура проекта (кратко)

- `bot_pooling.py` — обработка входящих сообщений (упоминаний) и ответы.
- `rag_bot.py` — логика RAG: эмбеддинги, поиск по FAISS, генерация ответа.
- `setup_rag.py` — сборка локальных FAISS-индексов из JSON/Markdown.
- `data/` — исходники знаний.
- `faiss_index/` — базовый FAISS-индекс, используемый ботом по умолчанию.

