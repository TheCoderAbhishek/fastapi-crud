from fastapi import FastAPI, Depends
from pydantic import BaseModel
from typing import List, Annotated
from app import models
from app.database import engine, SessionLocal
from sqlalchemy.orm import Session

app = FastAPI()
models.Base.metadata.create_all(bind=engine)

class ChoiceRequest(BaseModel):
    choice_text: str
    is_correct: bool

class QuestionRequest(BaseModel):
    question: str
    choices: List[ChoiceRequest]

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

@app.post("/questions/")
async def create_question(question: QuestionRequest, db: Session = Depends(get_db)):
    db_question = models.Question(question_text=question.question)
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    for choice in question.choices:
        db_choice = models.Choices(
            choice_text=choice.choice_text,
            is_correct=choice.is_correct,
            question_id=db_question.id,
        )
        db.add(db_choice)
    db.commit()
    return {"message": "Question and choices created successfully"}