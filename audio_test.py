import sounddevice as sd
import soundfile as sf
import speech_recognition as sr
from pathlib import Path
import os

fs = 44100
seconds = 5

print("Recording...")
audio = sd.rec(int(seconds * fs), samplerate=fs, channels=1)
sd.wait()
print("Done")

sf.write("audio.wav", audio, fs)

audio_folder = "saved_audios"
audio_count = len([f for f in os.listdir(audio_folder) if os.path.isfile(os.path.join(audio_folder, f))])
sf.write(f"saved_audios/{audio_count+1}.wav", audio, fs)
sf.write("audio.wav", audio, fs)
print("Saved as audio.wav")

r = sr.Recognizer()

with sr.AudioFile("audio.wav") as source:
    audio = r.record(source)
try:
    text = r.recognize_google(audio)
    print(text)
except sr.UnknownValueError:
    print("i wasn't able to get that")
except sr.RequestError:
    print("i wasn't able to get that")