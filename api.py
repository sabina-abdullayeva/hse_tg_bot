from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel

import qa


load_dotenv(override=True)

app = FastAPI(title="HSE Courses Bot API")


class QuestionRequest(BaseModel):
    question: str


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/ask")
def ask(request: QuestionRequest) -> dict:
    answer = qa.answer(request.question)
    return {"answer": answer}
