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

    # Mouth points
    mouth_left      = get_point(61)
    mouth_right     = get_point(291)
    upper_lip       = get_point(13)
    lower_lip       = get_point(14)
    mouth_center_y  = (upper_lip[1] + lower_lip[1]) / 2
    mouth_corners_y = (mouth_left[1] + mouth_right[1]) / 2
    smile_score     = mouth_center_y - mouth_corners_y

    # Normalize by face height
    forehead    = get_point(10)
    chin        = get_point(152)
    face_height = abs(chin[1] - forehead[1])
    smile_score_normalized    = (smile_score / face_height) * 100

    # Eyebrow points
    left_brow         = get_point(105)
    right_brow        = get_point(334)
    nose_tip          = get_point(1)
    brow_raise_score  = ((nose_tip[1] - left_brow[1]) + (nose_tip[1] - right_brow[1])) / 2
    brow_raise_normalized = (brow_raise_score / face_height) * 100

    # Eye openness (average both eyes)
    left_eye_top  = get_point(159)
    left_eye_bot  = get_point(145)
    right_eye_top = get_point(386)
    right_eye_bot = get_point(374)
    eye_openness  = ((abs(left_eye_top[1] - left_eye_bot[1])) + (abs(right_eye_top[1] - right_eye_bot[1]))) / 2
    eye_openness_normalized = (eye_openness / face_height) * 100

    # Brow furrow (confused)
    left_inner_brow    = get_point(107)
    right_inner_brow   = get_point(336)
    brow_furrow_dist   = abs(left_inner_brow[0] - right_inner_brow[0])
    brow_furrow_normalized = (brow_furrow_dist / frame_width) * 100

    # Decide emotion
    if smile_score_normalized > 3:
        emotion = "happy"
    elif brow_raise_normalized > 55 and eye_openness_normalized > 4:
        emotion = "surprised"
    elif brow_furrow_normalized < 8 and eye_openness_normalized < 3.5:
        emotion = "confused"
    elif brow_raise_normalized > 48 and eye_openness_normalized < 3:
        emotion = "nervous"
    elif eye_openness_normalized < 2.5:
        emotion = "stressed"
    else:
        emotion = "neutral"

    return emotion


def analyze_posture(face_landmarks, pose_landmarks, frame_height, frame_width):
    """
    Analyzes 4 posture signals and returns individual scores + overall posture score.

    1. Shoulder level     — are shoulders even?
    2. Head tilt          — is head straight?
    3. Head centered      — is face in center of frame?
    4. Distance           — is candidate at proper distance from camera?
    """
    posture = {}

    # ---------------------------------------------------------------
    # 1. SHOULDER LEVEL (from pose landmarks)
    # ---------------------------------------------------------------
    if pose_landmarks:
        lm = pose_landmarks.landmark
        left_shoulder  = lm[mp_pose.PoseLandmark.LEFT_SHOULDER]
        right_shoulder = lm[mp_pose.PoseLandmark.RIGHT_SHOULDER]
        shoulder_diff  = abs(left_shoulder.y - right_shoulder.y)

        # shoulder_diff is 0 to 1 (fraction of frame height)
        # 0.00 = perfectly level = 100 score
        # 0.05 = slightly uneven = 80 score
        # 0.10 = very uneven    = 50 score
        shoulder_score = max(0, 100 - (shoulder_diff * 1000))
        posture["shoulder_level_score"] = round(shoulder_score, 1)
        posture["shoulders_level"]      = shoulder_diff < 0.05
    else:
        posture["shoulder_level_score"] = 0
        posture["shoulders_level"]      = False

    # ---------------------------------------------------------------
    # 2. HEAD TILT (from face landmarks)
    # ---------------------------------------------------------------
    # We compare the Y position of left ear (234) and right ear (454)
    # If they are at the same height = head is straight
    # If one is higher = head is tilted
    if face_landmarks:
        lm = face_landmarks.landmark

        def get_point(index):
            return (lm[index].x * frame_width, lm[index].y * frame_height)

        left_ear  = get_point(234)
        right_ear = get_point(454)

        # Ear Y difference normalized by frame height
        ear_diff            = abs(left_ear[1] - right_ear[1])
        ear_diff_normalized = (ear_diff / frame_height) * 100

        # 0  = perfectly straight = 100 score
        # 5  = slight tilt        = 75 score
        # 10 = strong tilt        = 50 score
        head_tilt_score = max(0, 100 - (ear_diff_normalized * 5))
        posture["head_tilt_score"] = round(head_tilt_score, 1)
        posture["head_tilt_deg"]   = round(ear_diff_normalized, 2)

        # ---------------------------------------------------------------
        # 3. HEAD CENTERED (is face in the middle of the frame?)
        # ---------------------------------------------------------------
        # Nose tip X position tells us where face is horizontally
        # 0 = far left, 0.5 = center, 1 = far right
        nose_x = lm[1].x  # already 0-1

        # Distance from center (0.5)
        center_offset = abs(nose_x - 0.5)

        # 0.00 = perfectly centered = 100 score
        # 0.10 = slightly off       = 80 score
        # 0.25 = very off center    = 50 score
        centered_score = max(0, 100 - (center_offset * 200))
        posture["head_centered_score"] = round(centered_score, 1)
        posture["head_offset"]         = round(center_offset, 3)

        # ---------------------------------------------------------------
        # 4. DISTANCE FROM CAMERA (face size in frame)
        # ---------------------------------------------------------------
        # We measure face width using cheek landmarks (left=234, right=454)
        face_width = abs(right_ear[0] - left_ear[0])
        face_width_percent = (face_width / frame_width) * 100

        # Ideal face width = 25% to 45% of frame width
        # Too small (< 20%) = too far away
        # Too large (> 50%) = too close
        if 25 <= face_width_percent <= 45:
            distance_score = 100
            distance_status = "good"
        elif face_width_percent < 20:
            distance_score = max(0, face_width_percent * 3)
            distance_status = "too_far"
        elif face_width_percent > 50:
            distance_score = max(0, 100 - ((face_width_percent - 45) * 5))
            distance_status = "too_close"
        else:
            distance_score = 85
            distance_status = "acceptable"

        posture["distance_score"]  = round(distance_score, 1)
        posture["distance_status"] = distance_status
        posture["face_width_pct"]  = round(face_width_percent, 1)

    else:
        posture["head_tilt_score"]     = 0
        posture["head_centered_score"] = 0
        posture["distance_score"]      = 0
        posture["distance_status"]     = "unknown"

    # ---------------------------------------------------------------
    # OVERALL POSTURE SCORE
    # Weighted average of all 4 signals
    # Shoulders = 30%, Head tilt = 25%, Centered = 25%, Distance = 20%
    # ---------------------------------------------------------------
    overall_posture = (
        posture.get("shoulder_level_score", 0) * 0.30 +
        posture.get("head_tilt_score", 0)      * 0.25 +
        posture.get("head_centered_score", 0)  * 0.25 +
        posture.get("distance_score", 0)       * 0.20
    )
    posture["overall_posture_score"] = round(overall_posture, 1)

    return posture


def analyze_frame(frame):
    results = {}
    frame_height, frame_width = frame.shape[:2]
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    face_landmarks_data = None

    # Face mesh
    with mp_face_mesh.FaceMesh(
        static_image_mode=True,
        max_num_faces=1,
        refine_landmarks=True
    ) as face_mesh:
        face_results = face_mesh.process(rgb_frame)
        face_detected = face_results.multi_face_landmarks is not None
        results["face_detected"] = face_detected

        if face_detected:
            face_landmarks_data = face_results.multi_face_landmarks[0]
            results["dominant_emotion"] = detect_emotion_from_landmarks(
                face_landmarks_data, frame_height, frame_width
            )
        else:
            results["dominant_emotion"] = "looking_away"

    # Pose
    pose_landmarks_data = None
    with mp_pose.Pose(static_image_mode=True) as pose:
        pose_results = pose.process(rgb_frame)
        if pose_results.pose_landmarks:
            pose_landmarks_data = pose_results.pose_landmarks

    # Posture analysis (combines face + pose data)
    posture = analyze_posture(
        face_landmarks_data,
        pose_landmarks_data,
        frame_height,
        frame_width
    )
    results["posture"] = posture

    # Hands
    with mp_hands.Hands(static_image_mode=True, max_num_hands=2) as hands:
        hand_results = hands.process(rgb_frame)
        results["hands_detected"] = hand_results.multi_hand_landmarks is not None

    return results


def interpret_with_llm(frame_results: list) -> dict:
    prompt = f"""
    You are an expert body language analyst for job interviews.
    Here is frame-by-frame analysis data from a candidate's interview video.

    Each frame includes:
    - face_detected: whether face was visible
    - dominant_emotion: emotion detected from facial landmarks
    - posture: dict with shoulder_level_score, head_tilt_score, head_centered_score,
               distance_score, distance_status, overall_posture_score
    - hands_detected: whether hands were visible (fidgeting indicator)

    Emotions possible: happy, neutral, nervous, surprised, stressed, confused, looking_away

    Frame data:
    {json.dumps(frame_results, indent=2)}

    Based on this data, return ONLY a JSON object with absolutely no extra text,
    no explanation, no markdown, no code blocks, just raw JSON:
    {{
        "eye_contact_score": 0,
        "posture_score": 0,
        "head_tilt_score": 0,
        "distance_score": 0,
        "confidence_score": 0,
        "nervousness_score": 0,
        "overall_body_language_score": 0,
        "emotions_detected": ["list of unique emotions detected"],
        "dominant_emotion": "most common emotion throughout",
        "distance_feedback": "one sentence about their distance from camera",
        "feedback": "detailed body language feedback paragraph"
    }}

    Scoring guide:
    - eye_contact_score          : % of frames where face was detected and not looking_away
    - posture_score              : average of overall_posture_score across all frames
    - head_tilt_score            : average head_tilt_score across all frames
    - distance_score             : average distance_score across all frames
    - confidence_score           : based on emotions (happy/neutral = high, nervous/stressed/confused = low)
    - nervousness_score          : how often nervous/stressed/confused/looking_away appeared
    - overall_body_language_score: average of eye_contact, posture, confidence scores

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
            print(f"Frame {i+1}/{total_frames} | emotion: {result.get('dominant_emotion')} | posture: {result.get('posture', {}).get('overall_posture_score')} | distance: {result.get('posture', {}).get('distance_status')}")

        elapsed = time.time() - start_time
        time.sleep(max(0, interval - elapsed))

    cap.release()
    cv2.destroyAllWindows()

    print(f"\nAll {len(frame_results)} frames captured. Sending to LLM...")
    return interpret_with_llm(frame_results)