import json
import os

from openai import OpenAI


ROUTE_PROMPT = """
Ты определяешь, что пользователь хочет узнать о курсах бакалавриата НИУ ВШЭ.
Верни только JSON: {"intent": "...", "slots": {...}}.

Доступные intent:
- list_programs: список программ
- programs_by_language: программы, где есть курсы на указанном языке
- courses_by_language: курсы на указанном языке
- courses_for_program: курсы конкретной программы
- courses_by_status: курсы с указанным статусом
- course_teachers: кто ведет курс
- teacher_courses: какие курсы ведет преподаватель
- course_search: поиск курса по названию
- program_search: поиск программы по названию
- unknown: если непонятно

Правила:
- Не генерируй SQL.
- Если спрашивают "программы на английском", это programs_by_language.
- Язык хранится у курсов, не у программ.
- В slots клади только нужные поля: language, program, status, course, teacher, query.
""".strip()

ANSWER_PROMPT = """
Ты помощник по курсам бакалавриата НИУ ВШЭ.
Отвечай только на основе данных из базы.
Если информации нет — честно скажи что не знаешь.
Отвечай коротко и по делу, на русском языке.
""".strip()


def _format_openai_error(error: Exception) -> str:
    cause = getattr(error, "__cause__", None)
    if cause:
        return f"{type(error).__name__}: {cause}"
    return f"{type(error).__name__}: {error}"


def _client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")

    base_url = os.getenv("OPENAI_BASE_URL")
    client_kwargs = {"api_key": api_key, "timeout": 20}
    if base_url:
        client_kwargs["base_url"] = base_url

    return OpenAI(**client_kwargs)


def ask_route(user_question: str) -> dict:
    try:
        response = _client().chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o"),
            messages=[
                {"role": "system", "content": ROUTE_PROMPT},
                {"role": "user", "content": user_question},
            ],
            response_format={"type": "json_object"},
            temperature=0,
        )
    except Exception as error:
        raise RuntimeError(_format_openai_error(error)) from error

    content = response.choices[0].message.content or "{}"
    data = json.loads(content)
    if not isinstance(data, dict):
        return {"intent": "unknown", "slots": {}}

    slots = data.get("slots") or {}
    if not isinstance(slots, dict):
        slots = {}

    return {
        "intent": data.get("intent") or "unknown",
        "slots": slots,
    }


def ask_gpt(user_question: str, route: str, rows: list[dict]) -> str:
    context = json.dumps(rows, ensure_ascii=False, indent=2)
    user_content = f"Маршрут:\n{route}\n\nДанные:\n{context}\n\nВопрос: {user_question}"

    try:
        response = _client().chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o"),
            messages=[
                {"role": "system", "content": ANSWER_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=0.2,
        )
    except Exception as error:
        raise RuntimeError(_format_openai_error(error)) from error

    return response.choices[0].message.content or "Не удалось сформировать ответ."

