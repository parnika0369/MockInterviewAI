import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def analyze_transcript(transcript: str) -> dict:
    """
    Sends transcript to Groq LLaMA 3 and returns analysis.
    """
    prompt = f"""
    You are an expert interview coach. Analyze this interview answer and return ONLY a JSON object with no extra text:

    Transcript: "{transcript}"

    Return this exact JSON format:
    {{
        "filler_words": ["list of filler words found"],
        "filler_word_count": 0,
        "grammar_issues": ["list of grammar issues found"],
        "fluency_score": 0,
        "confidence_score": 0,
        "grammar_score": 0,
        "vocabulary_score": 0,
        "overall_score": 0,
        "suggestions": ["list of improvement suggestions"]
    }}

    All scores are out of 100.
    fluency_score = how smoothly they spoke
    confidence_score = how confident they sounded
    grammar_score = how grammatically correct they were
    vocabulary_score = how rich and varied their vocabulary was
    overall_score = average of all scores
    """

    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    result = response.choices[0].message.content
    return json.loads(result)