import db
from openai_api import ask_gpt, ask_route


LANGUAGE_BY_WORD = {
    "англ": "английский",
    "english": "английский",
    "рус": "русский",
    "испан": "испанский",
    "итал": "итальянский",
    "нем": "немецкий",
    "тур": "турецкий",
    "фран": "французский",
}

STATUS_BY_WORD = {
    "обяз": "Обязательный",
    "выбор": "По выбору",
    "факульт": "Факультатив",
    "общефак": "Дисциплина общефакультетского пула",
}


def _normalize_language(value: str) -> str:
    value = value.strip().lower()
    for word, language in LANGUAGE_BY_WORD.items():
        if word in value:
            return language
    return value


def _normalize_status(value: str) -> str:
    value = value.strip().lower()
    for word, status in STATUS_BY_WORD.items():
        if word in value:
            return status
    return value


def _find_rows(intent: str, slots: dict, question: str) -> list[dict]:
    if intent == "list_programs":
        return db.get_programs(per_page=20)

    if intent == "programs_by_language":
        language = _normalize_language(slots.get("language", question))
        return db.search_programs_by_language(language)

    if intent == "courses_by_language":
        language = _normalize_language(slots.get("language", question))
        return db.search_courses_by_language(language)

    if intent == "courses_for_program":
        return db.get_courses_for_program(slots.get("program", question))

    if intent == "courses_by_status":
        status = _normalize_status(slots.get("status", question))
        return db.search_courses_by_status(status)

    if intent == "course_teachers":
        return db.search_course_teachers(slots.get("course", question))

    if intent == "teacher_courses":
        return db.search_teachers(slots.get("teacher", question))

    if intent == "program_search":
        return db.search_programs(slots.get("query", question))

    return db.search_courses(slots.get("query", question))


def answer(question: str) -> str:
    question = question.strip()
    if not question:
        return "Напишите вопрос о курсах."

    route = ask_route(question)
    intent = route["intent"]
    slots = route["slots"]
    rows = _find_rows(intent, slots, question)
    route_text = f"{intent}: {slots}"
    return ask_gpt(question, route_text, rows)
