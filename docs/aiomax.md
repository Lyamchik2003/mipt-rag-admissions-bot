# aiomax Library Reference

_Этот документ переоформлен из исходного `documentation.txt` и структурирован для удобной навигации._

## Введение

`aiomax` — асинхронная библиотека для разработки ботов во «ВКонтакте / MAX» платформе. Основная точка входа — класс `aiomax.Bot`, который комбинирует маршрутизацию событий, работу с long polling и вспомогательные инструменты (FSM, фильтры, клавиатуры).

## Содержание

- [Инициализация бота](#инициализация-бота)
  - [Создание бота](#создание-бота)
  - [Основные атрибуты](#основные-атрибуты)
  - [Методы](#методы)
  - [Примеры](#примеры)
- [FSM (Finite State Machine)](#fsm-finite-state-machine)
- [Декораторы и обработчики событий](#декораторы-и-обработчики-событий)
- [Клавиатуры](#клавиатуры)
- [Логирование](#логирование)
- [Роутеры](#роутеры)
- [Фильтры](#фильтры)
- [Приложения и вложения](#приложения-и-вложения)

---

## Инициализация бота

### Создание бота

```python
import aiomax

bot = aiomax.Bot(
    access_token="TOKEN",
    command_prefixes="/",
    mention_prefix=True,
    case_sensitive=True,
    default_format="markdown",
    max_messages_cached=10000,
    debug=False,
)
```

| Параметр              | Тип                       | Значение по умолчанию | Описание |
|----------------------|---------------------------|-----------------------|----------|
| `access_token`       | `str`                     | —                     | Токен, полученный в @MasterBot. |
| `command_prefixes`   | `str \| List[str]`        | `/`                   | Префикс для команд. |
| `mention_prefix`     | `bool`                    | `True`                | Реагировать ли на упоминание `@username`. |
| `case_sensitive`     | `bool`                    | `True`                | Учитывать регистр команд. |
| `default_format`     | `'markdown' \| 'html'`    | `None`                | Форматирование по умолчанию. |
| `max_messages_cached`| `int`                     | `10000`               | Количество сообщений в кэше для событий редактирования/удаления. |
| `debug`              | `bool`                    | `False`               | Подробный лог при ошибках. |

### Основные атрибуты

- `Bot.storage: FSMStorage` — хранилище состояний.

### Методы

Разделены на категории.

#### Методы управления ботом

| Метод | Возвращает | Описание |
|-------|------------|----------|
| `Bot.get_me()` | `User` | Информация о текущем боте. |
| `Bot.patch_me(name, description, commands, photo)` | `User` | Обновление профиля бота. |
| `Bot.run()` | — | Синоним `asyncio.run(bot.start_polling())`. |
| `Bot.start_polling(session=None)` | `Coroutine` | Запускает long polling. Можно передать внешнюю `aiohttp.ClientSession`. |
| `Bot.get_chats(count=None, marker=None)` | `Chat` | Список чатов бота. |
| `Bot.chat_by_link(link)` | `Chat` | Получение чата по ссылке. |
| `Bot.get_chat(chat_id)` | `Chat` | Получение информации о чате. |
| `Bot.get_pin(chat_id)` | `Message \| None` | Закреплённое сообщение. |
| `Bot.pin(chat_id, message_id, notify=True)` | — | Закрепляет сообщение. |
| `Bot.delete_pin(chat_id)` | — | Удаляет закреплённое сообщение. |
| `Bot.my_membership(chat_id)` | `User` | Информация о боте в чате. |
| `Bot.leave_chat(chat_id)` | — | Покидает чат. |
| `Bot.get_admins(chat_id)` | `List[User]` | Администраторы чата. |
| `Bot.get_members(chat_id, count_per_iter=100)` | `AsyncIterator[User]` | Итератор участников. |
| `Bot.get_memberships(chat_id, user_ids)` | `List[User] \| User \| None` | Информация о выбранных пользователях. |
| `Bot.add_members(chat_id, users)` | — | Добавляет пользователей в чат. |
| `Bot.kick_member(chat_id, user_id, block=False)` | — | Удаляет пользователя. |
| `Bot.patch_chat(chat_id, icon=None, title=None, pin=None, notify=None)` | `Chat` | Обновляет свойства чата. |
| `Bot.post_action(chat_id, action)` | — | Отправляет “typing”, “mark_seen” и прочие действия. |

#### Работа с вложениями

| Метод | Возвращает | Описание |
|-------|------------|----------|
| `Bot.upload_image(data)` | `PhotoAttachment` |
| `Bot.upload_video(data)` | `VideoAttachment` |
| `Bot.upload_audio(data)` | `AudioAttachment` |
| `Bot.upload_file(data, filename=None)` | `FileAttachment` |

#### Работа с сообщениями

| Метод | Возвращает | Описание |
|-------|------------|----------|
| `Bot.get_message(id)` | `Message` | Получение сообщения по ID. |
| `Bot.send_message(...)` | `Message` | Отправка сообщения. |
| `Bot.edit_message(...)` | `Message` | Редактирование сообщения. |
| `Bot.delete_message(message_id)` | — | Удаление сообщения. |

### Примеры

#### Простейший эхо-бот

```python
import aiomax

bot = aiomax.Bot('TOKEN')

@bot.on_message()
async def echo(message: aiomax.Message):
    await message.reply(message.body.text)

bot.run()
```

#### Random-бот

```python
import aiomax
import random

bot = aiomax.Bot('TOKEN', default_format='markdown')

@bot.on_command('random', aliases=['rnd'])
async def gen(ctx: aiomax.CommandContext):
    try:
        min_num = int(ctx.args[0])
        max_num = int(ctx.args[1])
    except Exception:
        await ctx.reply('❌ Неверные аргументы: /random <мин> <макс>')
        return

    number = random.randint(min_num, max_num)
    await ctx.reply(f'Ваше число: **{number}**')

@bot.on_bot_start()
async def on_bot_start(payload: aiomax.BotStartPayload):
    await payload.send('Команда: /random <min> <max>')

@bot.on_ready()
async def send_commands():
    await bot.patch_me(commands=[
        aiomax.BotCommand('random', 'Генерирует случайное число')
    ])

bot.run()
```

#### FSM пример

```python
import aiomax
from aiomax import fsm

bot = aiomax.Bot('TOKEN')

@bot.on_bot_start()
async def start(payload: aiomax.BotStartPayload, cursor: fsm.FSMCursor):
    await payload.send('Как вас зовут?')
    cursor.change_state('name')

@bot.on_message(aiomax.filters.state('name'))
async def get_name(message: aiomax.Message, cursor: fsm.FSMCursor):
    cursor.change_data({'name': message.content})
    await message.reply('Введите фамилию')
    cursor.change_state('surname')

@bot.on_message(aiomax.filters.state('surname'))
async def get_surname(message: aiomax.Message, cursor: fsm.FSMCursor):
    data = cursor.get_data()
    await message.reply(f"Здравствуйте, {data['name']} {message.content}")
    cursor.clear()

bot.run()
```

Дополнительные примеры: эхо-бот с фильтром по чату, счётчик с кнопками, загрузка файлов, работа с прокси, роутеры.

---

## FSM (Finite State Machine)

- `FSMStorage` — общее хранилище состояний/данных.
- Методы: `get_state`, `get_data`, `change_state`, `change_data`, `clear_state`, `clear_data`, `clear`.
- `FSMCursor` — обёртка для конкретного пользователя. Передаётся как аргумент `cursor` в обработчики (кроме `on_button_chat_create`).

---

## Декораторы и обработчики событий

`Bot` и `Router` предоставляют декораторы для подписки на события.

| Декоратор | Описание |
|-----------|----------|
| `@bot.on_message(filter=None, detect_commands=False)` | Обработка входящих сообщений. Поддерживает фильтры / строки. |
| `@bot.on_message_edit(filter=None)` | Редактирование сообщений. |
| `@bot.on_message_delete(filter=None)` | Удаление сообщений. |
| `@bot.on_bot_start()` | Пользователь нажал «Начать» в ЛС. |
| `@bot.on_ready()` | Бот готов к работе (перед запуском polling). |
| `@bot.on_command(name=None, aliases=None, as_message=False)` | Обработка команд с префиксом. |
| `@bot.on_button_callback(filter=None)` | Нажатия callback-кнопок. |
| `@bot.on_button_chat_create()` | Создание чата через кнопку `ChatButton`. |
| `@bot.on_bot_add()` | Добавление бота в чат. |
| `@bot.on_bot_remove()` | Удаление бота из чата. |
| `@bot.on_user_add()` | Пользователь вошёл в чат. |
| `@bot.on_user_remove()` | Пользователь вышел из чата. |
| `@bot.on_chat_title_change()` | Изменено название чата. |

Каждый обработчик (кроме `on_button_chat_create`) получает `cursor: FSMCursor`.

### Объекты событий

- `Message`
- `CommandContext`
- `Callback`
- `BotStartPayload`
- `Chat`, `ChatCreatePayload`
- `MessageDeletePayload`
- `ChatTitleEditPayload`
- `User`, `UserMembershipPayload`

---

## Клавиатуры

Для работы с кнопками используйте `aiomax.buttons.KeyboardBuilder`.

```python
kb = aiomax.buttons.KeyboardBuilder()
kb.add(aiomax.buttons.CallbackButton('Тап', 'tap'))
kb.row(aiomax.buttons.CallbackButton('Сброс', 'reset'))

await ctx.reply('Выбор:', keyboard=kb)
```

Методы конструктора:

- `add(*buttons)` — добавить кнопки в текущую строку.
- `row(*buttons)` — начать новую строку.
- `table(in_row, *buttons)` — заполнить строки по `in_row` кнопок.
- `to_list()` — вернуть список списков кнопок.

Поддерживаемые типы кнопок:

- `CallbackButton(text, payload, intent='default')`
- `LinkButton(text, url)`
- `GeolocationButton(text, quick=False)`
- `ContactButton(text)`
- `ChatButton(text, title, description=None, payload=None, uuid=None)`
- `WebAppButton(text, bot)`
- `MessageButton(text)`

---

## Логирование

Используйте стандартный модуль `logging`.

```python
import logging

logging.basicConfig(level=logging.INFO)
```

- `INFO` — стандартный режим.
- `DEBUG` — расширенные логи (обработанные события и ошибки).

---

## Роутеры

`aiomax.Router` позволяет группировать обработчики.

```python
import aiomax

bot = aiomax.Bot('TOKEN')
router = aiomax.Router()

@router.on_message()
async def echo(message: aiomax.Message):
    await message.reply(message.content)

bot.add_router(router)
bot.run()
```

- `router.bot` — ссылка на родительский бот.
- Можно добавлять дочерние роутеры `router.add_router(child)`. Удаление — `bot.remove_router(router)`.
- Поддержка глобальных фильтров: `add_message_filter`, `add_message_edit_filter`, `add_message_delete_filter`, `add_button_callback_filter`.

---

## Фильтры

Фильтры облегчают выбор условных обработчиков. Есть встроенные и пользовательские варианты.

### Встроенные фильтры (`aiomax.filters`)

| Фильтр | Описание |
|--------|----------|
| `equals(content)` | Сообщение равно строке `content`. |
| `has(content)` | Сообщение содержит подстроку `content`. |
| `startswith(prefix)` | Сообщение начинается с `prefix`. |
| `endswith(suffix)` | Сообщение заканчивается на `suffix`. |
| `regex(pattern)` | Соответствие регулярному выражению. |
| `papaya` | Проверяет, что предпоследнее слово — «папайя». |
| `state(state)` | Состояние пользователя равно `state` (FSM). |

Фильтры можно комбинировать (`mode='or'`, операторы `&` и `|`).

### Пользовательские фильтры

- Лямбда: `@bot.on_message(lambda message: message.recipient.chat_type == 'dialog')`
- Функция:
  ```python
  def in_dialog(message):
      return message.recipient.chat_type == 'dialog'

  @bot.on_message(in_dialog)
  async def handler(message):
      ...
  ```
- Класс:
  ```python
  class ChatTypeFilter:
      def __init__(self, chat_type):
          self.chat_type = chat_type

      def __call__(self, message):
          return message.recipient.chat_type == self.chat_type

  @bot.on_message(ChatTypeFilter('dialog'))
  async def handler(message): ...
  ```

---

## Приложения и вложения

### Attachment (базовый класс)

Подклассы:

- `PhotoAttachment(url=None, token=None, photo_id=None)`
- `VideoAttachment(token, url=None, thumbnail=None, width=None, height=None, duration=None)`
- `AudioAttachment(token, transcription=None)`
- `FileAttachment(token, url=None, filename=None, size=None)`
- `StickerAttachment(code, url=None, width=None, height=None)`
- `ContactAttachment(name=None, contact_id=None, vcf_info=None, vcf_phone=None, max_info=None)`
- `ShareAttachment(url, token=None, title=None, description=None, image_url=None)`
- `LocationAttachment(latitude, longitude)`
- `InlineKeyboardAttachment(payload)`

### Message

Содержит информацию о сообщении.

- `recipient: MessageRecipient`
- `body: MessageBody`
- `sender: User`
- `timestamp`
- `link: LinkedMessage`
- `views`
- `url`
- `id`
- `user_locale`

Методы: `resolve_mention`, `send`, `reply`, `edit`, `delete`.

### MessageRecipient

- `chat_id`
- `chat_type`, `user_id`

### MessageBody

- `message_id`
- `seq`
- `text`
- `attachments`
- `markup` (список `Markup`)

### Markup

Типы: `strong`, `emphasized`, `monospaced`, `link`, `strikethrough`, `underline`, `user_mention`, `heading`, `highlighted`.

Содержит `type`, `start`, `length`, опционально `user_link`, `user_id`, `url`.

### LinkedMessage

Отражает пересланное/ответное сообщение. Поля: `type`, `sender`, `message`, `chat_id`.

### BotStartPayload

Передаётся в `@bot.on_bot_start()`.

- `chat_id`
- `user`
- `payload`
- `user_locale`
- Метод `send(...)`

### CommandContext

- `message`
- `sender`
- `recipient`
- `command_name`
- `args`
- `args_raw`
- Методы: `send`, `reply`

### Callback

- `timestamp`
- `callback_id`
- `user`
- `message`
- `payload`
- `user_locale`
- Методы: `answer`, `send`, `reply`

---

