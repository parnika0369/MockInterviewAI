# MockInterview AI

An AI-powered mock interview coaching platform that analyzes voice, body language, and answer quality to help candidates prepare for job interviews.

## What it does
- Records voice and transcribes it in real time
- Analyzes filler words, grammar, and fluency
- Evaluates answer quality with AI scoring
- Analyzes body language and posture via webcam
- Generates personalized feedback and improvement tips

## Tech Stack
- **Backend** — FastAPI
- **AI / LLM** — Groq LLaMA 3.3 70B
- **Voice** — SpeechRecognition + PyAudio
- **Video** — OpenCV + MediaPipe
- **Database** — PostgreSQL + Redis (Phase 6)
- **Deployment** — Docker + AWS + Nginx (Phase 7)

## Project Progress
- Phase 1 — Foundation (FastAPI server, environment setup) — Complete
- Phase 2 — Voice Pipeline (mic recording, transcription) — Complete
- Phase 3 — Text Analysis (filler words, fluency, grammar) — Complete
- Phase 4 — Answer Quality (AI scoring and feedback) — Complete
- Phase 5 — Video Analysis (body language, posture) — In Progress
- Phase 6 — Database + Auth (PostgreSQL + Redis + JWT) — Upcoming
- Phase 7 — Cloud Deployment (Docker + AWS + Nginx) — Upcoming

## API Endpoints
| Endpoint | Method | What it does |
|----------|--------|-------------|
| /health | GET | Check server status |
| /transcribe | POST | Record voice and transcribe |
| /analyze | POST | Analyze transcript quality |
| /evaluate | POST | Evaluate answer quality |
| /analyze-video | POST | Analyze body language |

## How to Run
```bash
git clone https://github.com/parnika0369/MockInterviewAI.git
cd MockInterviewAI

python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt

# Create .env file and add your keys
GROQ_API_KEY=your_key_here
APP_ENV=development

python -m uvicorn app.main:app --reload
```
