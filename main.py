from openai import *
import os, asyncio, threading, subprocess
import sounddevice as sd
import soundfile as sf
import speech_recognition as sr
from nicegui import ui
import numpy as np

API_KEY = os.getenv("HOLOCAUST_AI_API_KEY")
client = OpenAI(api_key=API_KEY)

AI_INSTRUCTIONS = """You are an educational AI assistant that helps people learn about the Holocaust.

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
- Keep responses short and simple by default.
- Only give longer or more detailed explanations if the user asks for more detail or explicitly requests it.
- Use simple, easy-to-understand language.
- Answer directly before giving any additional explanation.
- Respond naturally, as if speaking to someone in a conversation.
- Avoid bullet points, headings, markdown, or overly formal language unless the user specifically requests them.

If a question is outside your knowledge or cannot be answered confidently from reliable historical evidence, simply say:
"I am not sure."

Your goal is to help people understand the Holocaust accurately while remaining truthful, careful, and respectful."""

recording = False
audio_data = []
stream = None
audio_text = ""

fs = 44100

audio_folder = "saved_audios"
os.makedirs(audio_folder, exist_ok=True)

recording_lock = threading.Lock()

with ui.row().classes('items-center'):
    ui.icon('smart_toy', size="50px")
    ui.label('Holocaust AI').classes('text-h3')

ai_text = ui.label('Ask the AI!').classes('text-h6')

def audio_speak(text):
    subprocess.run(["say", text])

def audio_callback(indata, frames, time, status):
    global audio_data, recording

    with recording_lock:
        if recording:
            audio_data.append(indata.copy())


async def start_recording():
    global recording, audio_data, stream

    ai_text.text = "Recording..."
    ai_text.update()
    await asyncio.sleep(0.05)

    audio_data = []

    with recording_lock:
        recording = True

    stream = sd.InputStream(
        samplerate=fs,
        channels=1,
        callback=audio_callback
    )
    stream.start()


async def stop_recording():
    global recording, stream, audio_data, audio_text

    ai_text.text = "Processing..."
    ai_text.update()

    with recording_lock:
        recording = False

    if stream is not None:
        stream.stop()
        stream.close()
        stream = None

    if len(audio_data) == 0:
        ai_text.text = "No audio detected"
        ai_text.update()
        return

    audio = np.concatenate(audio_data, axis=0)

    sf.write("audio.wav", audio, fs)

    files = os.listdir(audio_folder)
    sf.write(f"{audio_folder}/{len(files) + 1}.wav", audio, fs)

    r = sr.Recognizer()
    audio_text = "I wasn't able to get that"

    with sr.AudioFile("audio.wav") as source:
        audio_file = r.record(source)

    try:
        audio_text = r.recognize_google(audio_file)
    except sr.UnknownValueError:
        audio_text = "I wasn't able to get that"
    except sr.RequestError:
        audio_text = "Speech API error"

    asyncio.create_task(run_ai(audio_text))


async def run_ai(audio_text):
    ai_text.text = "AI Thinking..."
    ai_text.update()
    await asyncio.sleep(0.05)

    ai_response = audio_text

    if audio_text not in ["I wasn't able to get that", "Speech API error"]:
        response = client.responses.create(
            model="gpt-5.5",
            instructions=AI_INSTRUCTIONS,
            input=audio_text,
        )
        ai_response = response.output_text

    threading.Thread(target=audio_speak, args=(ai_response,), daemon=True).start()

    ai_text.text = f"AI: {ai_response}"
    ai_text.update()

record_btn = ui.button("Record", icon="mic")

def toggle_recording():
    global recording
    if not recording:
        record_btn.text = "Stop"
        asyncio.create_task(start_recording())
    else:
        record_btn.text = "Record"
        asyncio.create_task(stop_recording())
        
record_btn.on("click", toggle_recording)

ui.run()