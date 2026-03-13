import cv2
import mediapipe as mp
import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

mp_face_mesh = mp.solutions.face_mesh
mp_pose = mp.solutions.pose
mp_hands = mp.solutions.hands

def analyze_frame(frame):
    results = {}
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    with mp_face_mesh.FaceMesh(
        static_image_mode=True,
        max_num_faces=1
    ) as face_mesh:
        face_results = face_mesh.process(rgb_frame)
        results["face_detected"] = face_results.multi_face_landmarks is not None

    with mp_pose.Pose(
        static_image_mode=True
    ) as pose:
        pose_results = pose.process(rgb_frame)
        results["pose_detected"] = pose_results.pose_landmarks is not None

    with mp_hands.Hands(
        static_image_mode=True,
        max_num_hands=2
    ) as hands:
        hand_results = hands.process(rgb_frame)
        results["hands_detected"] = hand_results.multi_hand_landmarks is not None

    return results

def interpret_with_llm(frame_results: list) -> dict:
    prompt = f"""
    You are an expert body language analyst for job interviews.
    Here is frame-by-frame analysis data from a candidate's interview video:

    {json.dumps(frame_results)}

    Based on this data, return ONLY a JSON object with no extra text:
    {{
        "eye_contact_score": 0,
        "posture_score": 0,
        "confidence_score": 0,
        "nervousness_score": 0,
        "overall_body_language_score": 0,
        "emotions_detected": ["list of emotions detected"],
        "feedback": "detailed body language feedback"
    }}

    All scores are out of 100.
    eye_contact_score = how well they maintained eye contact
    posture_score = how good their posture was
    confidence_score = how confident their body language was
    nervousness_score = how nervous they appeared
    overall_body_language_score = average of eye contact, posture and confidence
    """

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    result = response.choices[0].message.content
    return json.loads(result)

def analyze_video_from_webcam(duration_seconds: int = 10) -> dict:
    cap = cv2.VideoCapture(0)
    frame_results = []

    print(f"Recording for {duration_seconds} seconds...")

    for i in range(duration_seconds):
        ret, frame = cap.read()
        if ret:
            result = analyze_frame(frame)
            result["second"] = i + 1
            frame_results.append(result)
            print(f"Frame {i+1}/{duration_seconds} analyzed")

        cv2.waitKey(1000)

    cap.release()
    cv2.destroyAllWindows()

    print("Analyzing with LLM...")
    return interpret_with_llm(frame_results)