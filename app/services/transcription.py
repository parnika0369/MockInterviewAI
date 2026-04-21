import speech_recognition as sr
import threading

def transcribe_from_mic(stop_event=None) -> str:
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 300
    recognizer.dynamic_energy_threshold = True

    audio_chunks = []
    listening = True

    def listen_loop():
        with sr.Microphone() as source:
            print("🎙️ Adjusting for background noise...")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            print("✅ Ready! Speak now...\n")
            while listening:
                try:
                    audio = recognizer.listen(
                        source,
                        timeout=2,
                        phrase_time_limit=30
                    )
                    audio_chunks.append(audio)
                except sr.WaitTimeoutError:
                    pass
                except Exception as e:
                    print(f"Mic error: {e}")
                    break

    listen_thread = threading.Thread(target=listen_loop)
    listen_thread.daemon = True
    listen_thread.start()

    if stop_event:
        stop_event.wait()
    else:
        input()

    listening = False
    listen_thread.join(timeout=3)

    if not audio_chunks:
        print("⚠️ No audio captured.")
        return ""

    print(f"🔄 Transcribing {len(audio_chunks)} audio chunk(s)...")

    full_transcript = []
    for i, chunk in enumerate(audio_chunks):
        try:
            text = recognizer.recognize_google(chunk)
            full_transcript.append(text)
            print(f"  Chunk {i+1}: {text}")
        except sr.UnknownValueError:
            pass
        except Exception as e:
            print(f"  Chunk {i+1} error: {e}")

    result = " ".join(full_transcript).strip()
    return result