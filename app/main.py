from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

class TranscriptInput(BaseModel):
    transcript: str

class AnswerInput(BaseModel):
    question: str
    answer: str

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "environment": os.getenv("APP_ENV")
    }

@app.post("/transcribe")
def transcribe():
    try:
        from app.services.transcription import transcribe_from_mic
        text = transcribe_from_mic()
        return {"transcript": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze")
def analyze(input: TranscriptInput):
    try:
        from app.services.analysis import analyze_transcript
        result = analyze_transcript(input.transcript)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/evaluate")
def evaluate(input: AnswerInput):
    try:
        from app.services.answer_quality import evaluate_answer
        result = evaluate_answer(input.question, input.answer)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))