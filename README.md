# HSE Courses Telegram Bot

Небольшой учебный проект для ответов на вопросы о курсах бакалавриата НИУ ВШЭ.

В проекте есть:

- Telegram-бот
- FastAPI backend
- SQLite база `hse.db`
- данные о программах, курсах и преподавателях

## Что умеет бот

Бот принимает обычный текстовый вопрос и отвечает по данным из базы.

Примеры вопросов:

- Какие есть программы?
- Кто ведет курс Python?
- Какие курсы есть на английском?

## Установка

```bash
pip install -r requirements.txt
```

## Настройка

Нужно создать файл `.env` по примеру `.env.example`:

```env
BOT_TOKEN=your_token_here
API_URL=http://127.0.0.1:8000
OPENAI_API_KEY=sk-your_openai_key_here
OPENAI_MODEL=gpt-4o
OPENAI_BASE_URL=https://api.openai.com/v1
```

База `hse.db` должна лежать в корне проекта.

## Что внутри базы

В `hse.db` лежат данные о бакалаврских программах ВШЭ:

- `programs` — названия программ, ссылки на страницы и количество курсов
- `courses` — курсы внутри программ, их статус и языки преподавания
- `teachers` — преподаватели, которые привязаны к конкретным курсам

Эта база нужна, чтобы бот мог искать программы, курсы и преподавателей и отвечать на вопросы по ним.

## Запуск через Docker Compose

```bash
docker compose -f deploy/docker-compose.yml up --build
```

Так сразу запустятся Telegram-бот и FastAPI.

## Запуск Telegram-бота

```bash
python3 main.py
```

## Запуск FastAPI

```bash
uvicorn api:app --reload
```

После запуска API будет доступен на:

```text
http://127.0.0.1:8000
```

## Эндпоинты

Проверка работы:

```http
GET /health
```

Ответ на вопрос:

```http
POST /ask
```

Пример тела запроса:

```json
{
  "question": "Какие курсы есть на английском?"
}
```

## Структура

- `main.py` — запуск Telegram-бота
- `bot.py` — обработчики Telegram
- `api.py` — FastAPI backend
- `qa.py` — логика ответа на вопрос
- `db.py` — запросы к SQLite
- `openai_api.py` — работа с OpenAI
- `hse.db` — заполненная база данных
