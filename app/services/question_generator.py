import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Questions per duration
DURATION_TO_QUESTIONS = {
    20: 4,
    40: 8,
    60: 12,
    120: 20
}

def generate_interview_questions(job_roles: str, duration_minutes: int, extra_info: str = "") -> dict:
    total_questions = DURATION_TO_QUESTIONS.get(duration_minutes, 8)

    prompt = f"""
    You are an expert technical interviewer at a top tech company.
    Generate exactly {total_questions} interview questions for a candidate applying for: {job_roles}
    Additional context about the candidate: {extra_info if extra_info else "No additional context provided"}

    Rules:
    - Mix difficulties: roughly 40% Easy, 40% Medium, 20% Hard
    - Cover all the job roles/fields the candidate mentioned
    - Each question must have a difficulty tag: Easy, Medium, or Hard
    - Questions should feel like real interview questions from top companies
    - Mix theoretical, practical, and problem solving questions
    - Use the additional context to personalize the questions
      for example if candidate is a fresher ask more basic questions,
      if they have experience ask more advanced questions,
      if they mention a specific company focus on that company's interview style
    - Do NOT number the questions yourself

    Return ONLY a JSON object with no extra text, no markdown, no code blocks:
    {{
        "questions": [
            {{
                "id": 1,
                "question": "question text here",
                "difficulty": "Easy"
            }}
        ]
    }}

    IMPORTANT: Return ONLY the raw JSON. No text before or after. No ```json blocks.
    """

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )

    result = response.choices[0].message.content.strip()

    if result.startswith("```"):
        result = result.split("```")[1]
        if result.startswith("json"):
            result = result[4:]
        result = result.strip()

    parsed = json.loads(result)

    return {
        "job_roles": job_roles,
        "duration_minutes": duration_minutes,
        "total_questions": total_questions,
        "extra_info": extra_info if extra_info else None,
        "questions": parsed["questions"]
    }