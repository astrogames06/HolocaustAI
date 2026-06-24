from openai import *
import pyttsx3, os, asyncio, threading
import sounddevice as sd
import soundfile as sf
import speech_recognition as sr
from pathlib import Path
from nicegui import ui
import numpy as np

API_KEY = os.getenv("HOLOCAUST_AI_API_KEY")
client = OpenAI(api_key=API_KEY)
AI_INSTRUCTIONS = """
You are an educational AI assistant that helps people learn about the Holocaust.

Your purpose is to provide accurate, factual, and balanced information based on well-established historical evidence. You must prioritise historical accuracy above everything else.

You must never invent facts, quotes, statistics, events, dates, testimonies, or historical details.

If you are not certain about an answer or the information cannot be verified from widely accepted historical sources, you must clearly say:
"I am not sure."

Do not guess. Do not make assumptions. Do not fill in missing information.

If there are multiple historical interpretations accepted by historians, explain this briefly and objectively without presenting speculation as fact.

When discussing the Holocaust:
- Be respectful and sensitive.
- Avoid sensational or dramatic language.
- Explain events factually and clearly.
- Never minimise, justify, glorify, or deny the Holocaust.
- Correct misinformation politely using established historical evidence.

STYLE:
- Keep responses short unless the user asks for more detail.
- Use simple, easy-to-understand language.
- Answer directly before giving any additional explanation.
- Respond naturally, as if speaking to someone in a conversation.
- Avoid bullet points, headings, markdown, or overly formal language unless the user specifically requests them.

If a question is outside your knowledge or cannot be answered confidently from reliable historical evidence, simply say:
"I am not sure."

Your goal is to help people understand the Holocaust accurately while remaining truthful, careful, and respectful.
"""

voice_engine = pyttsx3.init()

recording = False
audio_data = []
stream = None

audio_folder = "saved_audios"
os.makedirs(audio_folder, exist_ok=True)

with ui.row().classes('items-center'):
    ui.icon('smart_toy', size="50px")
    ui.label('Holocaust AI').classes('text-h3')
ai_text = ui.label('Ask the AI!').classes('text-h6') # Display of ai output

audio_text = ""
fs = 44100

def audio_callback(indata, frames, time, status):
    global audio_data, recording
    if recording:
        audio_data.append(indata.copy())

async def start_recording():
    global recording, audio_data, stream

    print("Recording...")
    ai_text.text = "Recording..."
    ai_text.update()
    await asyncio.sleep(0.05)

    audio_data = []
    recording = True

    stream = sd.InputStream(
        samplerate=fs,
        channels=1,
        callback=audio_callback
    )
    stream.start()

    await asyncio.sleep(0.1)

async def stop_recording():
    global recording, stream, audio_data, audio_text

    print("Stopping...")
    recording = False

    stream.stop()
    stream.close()

    if len(audio_data) == 0:
        print("No audio captured")
        ai_text.text = "No audio detected"
        ai_text.update()
        return

    import numpy as np
    audio = np.concatenate(audio_data, axis=0)

    sf.write("audio.wav", audio, fs)
    files = os.listdir(audio_folder)
    audio_count = len(files)

    file_path = f"{audio_folder}/{audio_count + 1}.wav"
    sf.write(file_path, audio, fs)

    r = sr.Recognizer()
    audio_text = "I wasn't able to get that"

    with sr.AudioFile("audio.wav") as source:
        audio_file = r.record(source)

    try:
        audio_text = r.recognize_google(audio_file)
    except:
        pass

    print("Text:", audio_text)

    ai_text.text = "AI Thinking..."
    ai_text.update()

    asyncio.create_task(run_ai(audio_text))

async def run_ai(audio_text):
    ai_text.text = "AI Thinking..."
    ai_text.update()
    await asyncio.sleep(0.05)

    ai_response = "I wasn't able to get that"
    if audio_text != "I wasn't able to get that":
        response = client.responses.create(
            model="gpt-5.5",
            instructions=AI_INSTRUCTIONS,
            input=audio_text,
        )

        ai_response = response.output_text

    threading.Thread(target=lambda: voice_engine.say(ai_response) or voice_engine.runAndWait()).start()

    ai_text.text = ai_response
    ai_text.update()

ui.button("Hold to Record", icon="mic") \
    .on("mousedown", start_recording) \
    .on("mouseup", stop_recording)

ui.run()