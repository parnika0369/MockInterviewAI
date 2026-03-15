import cv2
import mediapipe as mp
import os
import json
import time
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

mp_face_mesh = mp.solutions.face_mesh
mp_pose = mp.solutions.pose
mp_hands = mp.solutions.hands

def detect_emotion_from_landmarks(face_landmarks, frame_height, frame_width):
    lm = face_landmarks.landmark

    def get_point(index):
        return (lm[index].x * frame_width, lm[index].y * frame_height)

    mouth_left       = get_point(61)
    mouth_right      = get_point(291)
    upper_lip        = get_point(13)
    lower_lip        = get_point(14)
    mouth_center_y   = (upper_lip[1] + lower_lip[1]) / 2
    mouth_corners_y  = (mouth_left[1] + mouth_right[1]) / 2
    smile_score      = mouth_center_y - mouth_corners_y

    left_brow        = get_point(105)
    right_brow       = get_point(334)
    nose_tip         = get_point(1)
    brow_raise_score = ((nose_tip[1] - left_brow[1]) + (nose_tip[1] - right_brow[1])) / 2

    left_eye_top     = get_point(159)
    left_eye_bot     = get_point(145)
    eye_openness     = abs(left_eye_top[1] - left_eye_bot[1])

    if smile_score > 5:
        emotion = "happy"
    elif brow_raise_score > 70 and eye_openness > 12:
        emotion = "surprised"
    elif brow_raise_score > 60 and eye_openness < 10:
        emotion = "nervous"
    elif eye_openness < 7:
        emotion = "stressed"
    else:
        emotion = "neutral"

    return emotion

def analyze_frame(frame):
    results = {}
    frame_height, frame_width = frame.shape[:2]
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    with mp_face_mesh.FaceMesh(
        static_image_mode=True,
        max_num_faces=1,
        refine_landmarks=True
    ) as face_mesh:
        face_results = face_mesh.process(rgb_frame)
        face_detected = face_results.multi_face_landmarks is not None
        results["face_detected"] = face_detected

        if face_detected:
            landmarks = face_results.multi_face_landmarks[0]
            results["dominant_emotion"] = detect_emotion_from_landmarks(
                landmarks, frame_height, frame_width
            )
        else:
            results["dominant_emotion"] = "unknown"

    with mp_pose.Pose(static_image_mode=True) as pose:
        pose_results = pose.process(rgb_frame)
        results["pose_detected"] = pose_results.pose_landmarks is not None

        if pose_results.pose_landmarks:
            lm = pose_results.pose_landmarks.landmark
            left_shoulder  = lm[mp_pose.PoseLandmark.LEFT_SHOULDER]
            right_shoulder = lm[mp_pose.PoseLandmark.RIGHT_SHOULDER]
            shoulder_diff  = abs(left_shoulder.y - right_shoulder.y)
            results["shoulders_level"] = shoulder_diff < 0.05
        else:
            results["shoulders_level"] = False

    with mp_hands.Hands(static_image_mode=True, max_num_hands=2) as hands:
        hand_results = hands.process(rgb_frame)
        results["hands_detected"] = hand_results.multi_hand_landmarks is not None

    return results

def interpret_with_llm(frame_results: list) -> dict:
    prompt = f"""
    You are an expert body language analyst for job interviews.
    Here is frame-by-frame analysis data from a candidate's interview video.
    Each frame includes face detection, pose/posture data, hand detection,
    and emotion detected using MediaPipe facial landmarks.

    Emotions possible: happy, neutral, nervous, surprised, stressed, unknown

    Frame data:
    {json.dumps(frame_results, indent=2)}

    Based on this data, return ONLY a JSON object with absolutely no extra text,
    no explanation, no markdown, no code blocks, just raw JSON:
    {{
        "eye_contact_score": 0,
        "posture_score": 0,
        "confidence_score": 0,
        "nervousness_score": 0,
        "overall_body_language_score": 0,
        "emotions_detected": ["list of unique emotions detected"],
        "dominant_emotion": "most common emotion throughout",
        "feedback": "detailed body language feedback paragraph"
    }}

    Scoring guide:
    - eye_contact_score     : % of frames where face was detected
    - posture_score         : % of frames where shoulders were level
    - confidence_score      : based on emotions (happy/neutral = high, nervous/stressed = low)
    - nervousness_score     : how often nervous/stressed emotion appeared
    - overall_body_language_score : average of eye_contact, posture, confidence scores

    IMPORTANT: Return ONLY the raw JSON object. No text before or after. No ```json blocks.
    """

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )

    result = response.choices[0].message.content.strip()

    if result.startswith("```"):
        result = result.split("```")[1]
        if result.startswith("json"):
            result = result[4:]
        result = result.strip()

    return json.loads(result)

def analyze_video_from_webcam(duration_seconds: int = 10) -> dict:
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        raise Exception("Could not open webcam.")

    frame_results = []
    fps = 5
    interval = 1.0 / fps
    total_frames = duration_seconds * fps

    print(f"Recording for {duration_seconds} seconds at {fps} fps...")

    for i in range(total_frames):
        start_time = time.time()
        ret, frame = cap.read()
        if ret:
            result = analyze_frame(frame)
            result["frame_number"] = i + 1
            frame_results.append(result)
            print(f"Frame {i+1}/{total_frames} | emotion: {result.get('dominant_emotion')} | face: {result.get('face_detected')}")

        elapsed = time.time() - start_time
        time.sleep(max(0, interval - elapsed))

    cap.release()
    cv2.destroyAllWindows()

    print(f"\nAll {len(frame_results)} frames captured. Sending to LLM...")
    return interpret_with_llm(frame_results)