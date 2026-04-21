import edge_tts
import asyncio
import pygame
import os

# The voice we chose for our AI interviewer
INTERVIEWER_VOICE = "en-US-JennyNeural"

async def speak(text: str):
    """
    Takes any text and speaks it out loud.
    This is the only function you need to call from anywhere in the project.
    """
    try:
        # Convert text to audio and save temporarily
        communicate = edge_tts.Communicate(text, voice=INTERVIEWER_VOICE)
        temp_file = "temp_speech.mp3"
        await communicate.save(temp_file)

        # Play the audio
        pygame.mixer.init()
        pygame.mixer.music.load(temp_file)
        pygame.mixer.music.play()

        # Wait until finished
        while pygame.mixer.music.get_busy():
            await asyncio.sleep(0.1)

        # Clean up
        pygame.mixer.quit()
        os.remove(temp_file)

    except Exception as e:
        print(f"[TTS Error] Could not speak: {e}")