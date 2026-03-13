import speech_recognition as sr

recognizer = sr.Recognizer()
recognizer.pause_threshold = 3.0
recognizer.non_speaking_duration = 3.0

with sr.Microphone() as source:
    print("Adjusting for ambient noise... Please wait.")
    recognizer.adjust_for_ambient_noise(source, duration=1)
    
    print("Listening... Speak now!")
    audio = recognizer.listen(source)

    try:
        text = recognizer.recognize_google(audio)
        print(f"You said: {text}")

    except sr.UnknownValueError:
        print("Could not understand the audio.")
    except sr.RequestError as e:
        print(f"Could not request results from Google Speech Recognition service; {e}")

    while True:
        try:
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=30)
            text = recognizer.recognize_google(audio)
            print(f"You said: {text}")

        except sr.WaitTimeoutError:
            break

        except sr.UnknownValueError:
            print("Couldn't understand")

        except sr.RequestError as e:
            break