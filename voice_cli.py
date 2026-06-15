#!/usr/bin/env python3
"""Customer360 Voice CLI — MCP client with speech input/output."""

import sys
import itertools
import requests
import speech_recognition as sr
import pyttsx3
import sounddevice as sd
import numpy as np
import wave

MCP_URL = "http://localhost:8000/mcp"
_ids = itertools.count(1)

tts = pyttsx3.init()
tts.setProperty("rate", 175)


def speak(text):
    print(f"\nbot> {text}")
    tts.say(text)
    tts.runAndWait()


def rpc(method, params=None):
    payload = {"jsonrpc": "2.0", "id": next(_ids), "method": method}
    if params is not None:
        payload["params"] = params
    r = requests.post(MCP_URL, json=payload, timeout=120)
    r.raise_for_status()
    return r.json()


def listen():
    fs = 16000
    duration = 6
    print("\n🎤 Listening... (speak now)")
    audio = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype="int16")
    sd.wait()

    with wave.open("temp.wav", "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(fs)
        wf.writeframes(audio.tobytes())

    r = sr.Recognizer()
    with sr.AudioFile("temp.wav") as source:
        recorded = r.record(source)
    try:
        text = r.recognize_google(recorded)
        print(f"you (voice)> {text}")
        return text
    except sr.UnknownValueError:
        print("Could not understand audio.")
        return None
    except sr.RequestError as e:
        print(f"Speech service error: {e}")
        return None

def ask_customer360(question):
    resp = rpc("tools/call", {
        "name": "ask_customer360",
        "arguments": {"question": question},
    })
    if "error" in resp:
        return f"Error: {resp['error']}"
    for item in resp["result"]["content"]:
        if item.get("type") == "text":
            return item["text"]
    return "No answer."


def main():
    print("Customer360 Voice CLI — MCP client")
    init = rpc("initialize")
    info = init["result"]["serverInfo"]
    print(f"Connected: {info['name']} v{info['version']}\n")

    mode = input("Mode — (v)oice or (t)ext? ").strip().lower()

    print("\nSay/type 'quit' to exit.\n")
    while True:
        if mode == "v":
            question = listen()
            if question is None:
                continue
        else:
            question = input("you> ").strip()

        if not question:
            continue
        if question.lower() in ("quit", "exit"):
            speak("Goodbye.")
            break

        full_answer = ask_customer360(question)
        print(f"\n--- Full result ---\n{full_answer}\n-------------------")

        # Speak just the first line (Cortex's plain-English interpretation)
        first_line = full_answer.strip().split("\n")[0]
        if "interpretation" in full_answer.lower():
            lines = [l for l in full_answer.split("\n") if l.strip()]
            spoken = lines[1] if len(lines) > 1 else first_line
        else:
            spoken = first_line

        speak(spoken + ". Full results are shown on screen.")


if __name__ == "__main__":
    main()