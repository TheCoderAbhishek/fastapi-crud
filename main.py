from fastapi import FastAPI, Depends, HTTPException
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

@app.get("/")
def read_root():
    return {"message": "Hello, World"}

@app.get("/getQuestion/{question_id}")
async def get_question(question_id: int, db: Session = Depends(get_db)):
    try:
        question = db.query(models.Question).filter(models.Question.id == question_id).first()
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")

        choices = (
            db.query(models.Choices)
            .filter(models.Choices.question_id == question_id)
            .all()
        )

        return {"question": question, "choices": choices}

    except Exception as e:
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.post("/questions/")
async def create_question(question: QuestionRequest, db: Session = Depends(get_db)):
    try:
        # Create the question model
        db_question = models.Question(question_text=question.question)
        db.add(db_question)
        db.commit()
        db.refresh(db_question)

        # Add choices for the question
        for choice in question.choices:
            db_choice = models.Choices(
                choice_text=choice.choice_text,
                is_correct=choice.is_correct,
                question_id=db_question.id,
            )
            db.add(db_choice)
        db.commit()

        return {"message": "Question and choices created successfully"}

    except Exception as e:
        # Handle any unexpected exceptions
        print(f"An error occurred: {e}")
        db.rollback()  # Revert any database changes in case of an error
        raise HTTPException(status_code=500, detail="Internal Server Error")