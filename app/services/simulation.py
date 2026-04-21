import os
import json
import threading
import asyncio
from groq import Groq
from dotenv import load_dotenv
from app.services.transcription import transcribe_from_mic
from app.services.video_analysis import record_frames_with_stop, interpret_with_llm
from app.services.answer_quality import evaluate_answer
from app.services.question_generator import generate_interview_questions
from app.services.tts import speak
from app.services.tts import speak
from app.services.avatar import show_avatar_with_question

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def say(text: str):
    """Helper to run async speak() from sync code."""
    print(f"\n🔊 Jenny: {text}\n")
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(speak(text))
        loop.close()
    except Exception as e:
        print(f"[TTS Error] {e}")


def run_simulation(job_roles: str, duration_minutes: int, extra_info: str = "") -> dict:
    print("\n" + "="*60)
    print("Welcome to MockInterviewAI — Full Mock Interview Mode!")
    print("="*60)
    print(f"Job Role(s): {job_roles}")
    print(f"Duration: {duration_minutes} minutes")
    print(f"Extra Info: {extra_info if extra_info else 'None'}")
    print("-"*60)

    # Welcome Message 
    say(f"Welcome. You are being interviewed for {job_roles}. Please ensure your mic and webcam are ready.")

    print("\nPress Enter to start the warm-up check...")
    input()

    import cv2
    import speech_recognition as sr

    # ── Webcam Check ─────────────────────────────────────────────
    cam = cv2.VideoCapture(0)
    if not cam.isOpened():
        say("I could not detect your webcam. Please check your camera and try again.")
        raise Exception("❌ Webcam not found!")
    cam.release()
    print("✅ Webcam — OK")

    # ── Microphone Check ─────────────────────────────────────────
    mic = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            mic.adjust_for_ambient_noise(source, duration=0.5)
        print("✅ Microphone — OK")
    except Exception as e:
        say("I could not detect your microphone. Please check your audio settings and try again.")
        raise Exception(f"❌ Microphone not found! Error: {e}")

    print("\n✅ All checks passed! Let's begin your interview.\n")

    say(
        "All systems are ready. "
        "After each question, press Enter when you are ready to answer, "
        "then speak your response, Press Enter again when you are finished. "
        "Best of luck!"
    )
    input()

    #Generate Questions 
    print("\nGenerating interview questions...")
    # say("Please wait a moment while I prepare your questions.")
    question_data = generate_interview_questions(job_roles, duration_minutes, extra_info)
    questions = question_data["questions"]

    say(f"I have prepared {len(questions)} questions for you today. Let us get started.")

    session_results = []

    for i, q in enumerate(questions):
        print(f"\n{'='*50}")
        print(f"Question {i+1} of {len(questions)} [{q['difficulty']}]")
        print(f"\n{q['question']}\n")

        #Speak the Question 
        show_avatar_with_question(q['question'], i+1, len(questions))
        say(
            f"Question {i+1} of. "
            f"Difficulty level: {q['difficulty']}. "
            f"Here is your question: {q['question']}"
        )

        print("Press Enter when you are ready to answer...")
        input()

        say("Please speak your answer now. Press Enter when you are done.")
        print("\n🎤 Speak your answer... Press ENTER when you are done.\n")

        stop_event    = threading.Event()
        voice_storage = {"transcript": ""}
        video_storage = {"frames": []}

        def run_voice(storage, event):
            try:
                storage["transcript"] = transcribe_from_mic(event)
            except Exception as e:
                print(f"Voice error: {e}")
                storage["transcript"] = ""

        def run_video(storage, event):
            try:
                storage["frames"] = record_frames_with_stop(event)
            except Exception as e:
                print(f"Video error: {e}")
                storage["frames"] = []

        voice_thread = threading.Thread(target=run_voice, args=(voice_storage, stop_event))
        video_thread = threading.Thread(target=run_video, args=(video_storage, stop_event))

        voice_thread.start()
        video_thread.start()

        input()
        stop_event.set()
        print("\n✅ Answer recorded! Processing...\n")

        voice_thread.join()
        video_thread.join()

        transcript = voice_storage["transcript"]
        print(f"📝 Transcript: {transcript if transcript else '(no speech detected)'}\n")

        say("Thank you for your answer. Let me analyze it for you.")

        #Analysis
        print("🔍 Analyzing body language...")
        video_analysis = interpret_with_llm(video_storage["frames"])

        print("📊 Evaluating answer quality...")
        answer_eval = evaluate_answer(
            q["question"],
            transcript if transcript else "No answer provided."
        )

        #Speak Feedback
        answer_score = answer_eval.get("overall_score", 0)
        body_score   = video_analysis.get("overall_body_language_score", 0)
        feedback     = answer_eval.get("feedback", "")
        strength     = answer_eval.get("what_you_did_well", "")
        improvement  = answer_eval.get("what_to_improve", "")

        feedback_speech = (
            f"Here is my feedback for question {i+1}. "
            f"Your answer score is {answer_score} out of 100, "
            f"and your body language score is {body_score} out of 100. "
        )
        if strength:
            feedback_speech += f"What you did well: {strength}. "
        if improvement:
            feedback_speech += f"What to improve: {improvement}. "

        say(feedback_speech)

        session_results.append({
            "question_number": i + 1,
            "question": q["question"],
            "difficulty": q["difficulty"],
            "transcript": transcript,
            "answer_evaluation": answer_eval,
            "video_analysis": video_analysis
        })

        print(f"✅ Question {i+1} done!\n")

        # ── Transition to next question 
        if i + 1 < len(questions):
            say(f"Let us move on to question {i+2}.")

    # ── Final Score Calculation
    total_score = 0
    for res in session_results:
        answer_score   = res["answer_evaluation"].get("overall_score", 0)
        body_score     = res["video_analysis"].get("overall_body_language_score", 0)
        question_score = (answer_score * 0.7) + (body_score * 0.3)
        total_score   += question_score

    session_score = round(total_score / len(session_results), 1)

    # ── Print Summary 
    print("\n" + "="*60)
    print("🎉 Interview Complete! Here is your Session Summary:")
    print("="*60)
    for res in session_results:
        q_num   = res["question_number"]
        a_score = res["answer_evaluation"].get("overall_score", 0)
        b_score = res["video_analysis"].get("overall_body_language_score", 0)
        print(f"Q{q_num}: Answer Score: {a_score}/100 | Body Language: {b_score}/100")
    print("-"*60)
    print(f"🏆 Overall Session Score: {session_score}/100")
    print("="*60 + "\n")

    # ── Speak Final Summary 
    if session_score >= 80:
        performance = "Excellent work! You performed outstandingly."
    elif session_score >= 60:
        performance = "Good effort! You have a solid foundation with room to grow."
    else:
        performance = "Keep practicing! Every interview makes you stronger."

    say(
        f"Congratulations on completing your mock interview! "
        f"Your overall session score is {session_score} out of 100. "
        f"{performance} "
        f"I am now generating your detailed report. "
        f"Thank you for using Mock Interview AI. Best of luck with your real interview!"
    )

    # ── Generate Report ──────────────────────────────────────────
    result = {
        "job_roles": job_roles,
        "duration_minutes": duration_minutes,
        "total_questions": len(questions),
        "overall_session_score": session_score,
        "session_results": session_results
    }

    from app.services.report_generator import generate_report
    generate_report(result)

    return result









