import speech_recognition as sr

def transcribe_from_mic() -> str:
    """
    Records audio from microphone and returns transcribed text.
    """
    recognizer = sr.Recognizer()
    recognizer.pause_threshold = 3.0
    recognizer.non_speaking_duration = 3.0

    with sr.Microphone() as source:
        print("Adjusting for ambient noise...")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        print("Listening... Speak now!")
        audio = recognizer.listen(source, timeout=10, phrase_time_limit=30)

    text = recognizer.recognize_google(audio)
    return text