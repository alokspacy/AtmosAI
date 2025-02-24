from flask import Flask, request, jsonify
from flask_cors import CORS
import speech_recognition as sr
import os
import pyttsx3  # Cross-platform TTS
import google.generativeai as genai
import requests
import webbrowser
import platform

try:
    import pyautogui  # May not work on Render
    pyautogui_enabled = True
except ImportError:
    pyautogui_enabled = False

# Flask app setup
app = Flask(__name__)
CORS(app)  # Enable CORS for API requests

# Set Gemini API key
GENAI_API_KEY = "AIzaSyBTxpFrER0nGFSGiCwFm4tE9cbbBMfg_g8"  # 🔹 Replace with actual Gemini API Key
genai.configure(api_key=GENAI_API_KEY)

# Initialize TTS (Cross-Platform)
speaker = pyttsx3.init()

# Global variable to track listening state
listening_active = True  # Starts in listening mode

# Function to handle speaking
def speak(text):
    print(f"Atmos: {text}")  # Debugging log
    speaker.say(text)
    speaker.runAndWait()

# Function to query Gemini API
def ask_gemini(prompt):
    try:
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(prompt)
        return response.text if response else "I couldn't generate a response."
    except Exception as e:
        return f"Gemini API error: {e}"

# Function to recognize speech input
def recognize_speech():
    global listening_active
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        if not listening_active:
            return "Listening is disabled."
        speak("I'm listening...")
        print("Listening...")
        try:
            audio = recognizer.listen(source)
            print("Recognizing...")
            command = recognizer.recognize_google(audio, language="en-IN").lower()
            print(f"Recognized: {command}")
            return command
        except sr.UnknownValueError:
            return "Sorry, I couldn't understand that."
        except sr.RequestError as e:
            return f"Speech recognition error: {e}"

# Function to get weather
def get_weather(city="Kanpur"):
    API_KEY = "bd5e378503939ddaee76f12ad7a97608"  # 🔹 Replace with actual OpenWeather API Key
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
    try:
        response = requests.get(url)
        data = response.json()
        if data.get("cod") == 200:
            temp = data["main"]["temp"]
            description = data["weather"][0]["description"]
            return f"The temperature in {city} is {temp}°C with {description}."
        return "Could not fetch weather data."
    except Exception as e:
        return f"Weather API error: {e}"

# Function to execute tasks
def execute_task(command):
    global listening_active
    response = "I'm not sure how to handle that command."

    if not listening_active:
        return "Listening is turned off."

    if "stop listening" in command or "stop" in command:
        listening_active = False
        response = "Listening stopped. Click the mic button to resume."

    elif "weather" in command:
        speak("Which city's weather do you want to check?")
        city = recognize_speech()
        response = get_weather(city)

    elif "search location" in command or "find location" in command:
        speak("What location do you want to search for?")
        location = recognize_speech()
        webbrowser.open(f"https://www.google.com/maps/search/{location}")
        response = f"Searching Google Maps for {location}."

    elif "open google" in command:
        speak("What would you like to search for?")
        search_query = recognize_speech()
        if search_query and search_query != "Sorry, I couldn't understand that.":
            webbrowser.open(f"https://www.google.com/search?q={search_query.replace(' ', '+')}")
            response = f"Searching Google for {search_query}."
        else:
            response = "I couldn't recognize the search query."

    elif "open youtube" in command:
        speak("What would you like to search for?")
        search_query = recognize_speech()
        webbrowser.open(f"https://www.youtube.com/results?search_query={search_query.replace(' ', '+')}")
        response = f"Searching YouTube for {search_query}."

    elif "shutdown" in command:
        response = "Shutting down the system."
        os.system("shutdown /s /t 1")

    elif "restart" in command:
        response = "Restarting the system."
        os.system("shutdown /r /t 1")

    elif "sleep" in command:
        response = sleep_pc()  # Calls sleep function directly

    elif "increase volume" in command and pyautogui_enabled:
        pyautogui.press("volumeup", presses=5)
        response = "Increasing volume."

    elif "decrease volume" in command and pyautogui_enabled:
        pyautogui.press("volumedown", presses=5)
        response = "Decreasing volume."

    elif "who created you" in command:
        response = "I have been created by Team Atmos."

    else:
        response = ask_gemini(command)

    return response

# Sleep PC (Fixed for Linux)
@app.route("/api/sleep", methods=["GET"])
def sleep_pc():
    try:
        system = platform.system()
        if system == "Windows":
            os.system("rundll32.exe powrprof.dll,SetSuspendState Sleep")
        elif system == "Linux":
            os.system("systemctl suspend")
        else:
            return jsonify({"response": "Unsupported OS"}), 400

        return jsonify({"response": "PC is going to sleep."}), 200
    except Exception as e:
        return jsonify({"response": f"Error putting PC to sleep: {e}"}), 500

# API to continuously listen
@app.route("/api/listen", methods=["GET"])
def listen_command():
    global listening_active
    if not listening_active:
        return jsonify({"command": "", "response": "Listening is turned off. Click the mic button to resume."})

    command = recognize_speech()
    response = execute_task(command)
    return jsonify({"command": command, "response": response})

# API to toggle listening
@app.route("/api/toggle_listen", methods=["POST"])
def toggle_listening():
    global listening_active
    listening_active = not listening_active
    state = "on" if listening_active else "off"
    return jsonify({"message": f"Listening turned {state}."})

# API to handle Atmos responses
@app.route("/api/atmos", methods=["POST"])
def atmos_response():
    data = request.get_json()
    command = data.get("command", "")
    if not command:
        return jsonify({"error": "No command provided"}), 400
    response = execute_task(command)
    return jsonify({"response": response})

# Start Flask Server
if __name__ == "__main__":
    print("Atmos Assistant is running...")
    app.run(debug=False, host="0.0.0.0", port=5000)  # 🔥 Set debug=False in production
