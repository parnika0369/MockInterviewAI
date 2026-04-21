import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def evaluate_answer(question: str, answer: str) -> dict:
    """
    Evaluates the quality of an interview answer using Groq LLaMA 3.
    """
    prompt = f"""
    You are an expert technical interviewer. Evaluate this interview answer and return ONLY a JSON object with no extra text:

    Question: "{question}"
    Answer: "{answer}"

    Return this exact JSON format:
    {{
        "relevance_score": 0,
        "completeness_score": 0,
        "technical_score": 0,
        "communication_score": 0,
        "overall_score": 0,
        "strengths": ["list of things done well"],
        "weaknesses": ["list of things to improve"],
        "ideal_answer_summary": "brief summary of what a perfect answer looks like",
        "feedback": "detailed personalized feedback"
    }}

    All scores are out of 100.
    relevance_score = how relevant the answer is to the question
    completeness_score = how completely the question was answered
    technical_score = how technically accurate and deep the answer is
    communication_score = how clearly and confidently it was communicated
    overall_score = average of all four scores
    IMPORTANT: Return ONLY the raw JSON. No text before or after. No ```json blocks.
    """

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        result = response.choices[0].message.content.strip()

        if not result:
            raise ValueError("Empty response from Groq")

        if result.startswith("```"):
            result = result.split("```")[1]
            if result.startswith("json"):
                result = result[4:]
            result = result.strip()

        return json.loads(result)

    except Exception as e:
        print(f"[evaluate_answer error] {e}")
        return {
            "relevance_score": 0,
            "completeness_score": 0,
            "technical_score": 0,
            "communication_score": 0,
            "overall_score": 0,
            "strengths": [],
            "weaknesses": ["Could not evaluate answer."],
            "ideal_answer_summary": "N/A",
            "feedback": f"Evaluation failed: {str(e)}"
        }