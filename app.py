from flask import Flask, request, jsonify
from flask_cors import CORS
import speech_recognition as sr
import os
import pyttsx3  # Backup TTS
import google.generativeai as genai
import requests
import webbrowser
from ecapture import ecapture as ec
import platform
import pyautogui

# Flask app setup
app = Flask(__name__)
CORS(app)  # Enable CORS for API requests

# Set Gemini API key
genai.configure(api_key="AIzaSyBTxpFrER0nGFSGiCwFm4tE9cbbBMfg_g8")

# Initialize TTS (Text-to-Speech)
# Initialize TTS (Cross-Platform)
speaker = pyttsx3.init()

# Global variable to track listening state
listening_active = True  # Starts in listening mode

# Function to handle speaking
def speak(text):
    print(f"Atmos: {text}")  # Debugging log
    if win32_tts:
        speaker.Speak(text)
    else:
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
        

# Function to open Notepad
def open_notepad():
        os.system("notepad.exe")

# Restart My PC
def restart_pc():
    os.system("shutdown /r /t 1")
    return "Restarting the system."

# Shut Down PC
def shutdown_pc():
    os.system("shutdown /s /t 1")
    return "Shutting down the system."

# Increase Volume
def increase_volume():
    pyautogui.press("volumeup", presses=5)

# Decrease Volume
def decrease_volume():
    pyautogui.press("volumedown", presses=5)

# Show System Information
def system_info():
    return platform.uname()

# Open File Explorer
def open_file_explorer():
    os.system("explorer")

# Open Google
def open_google():
    webbrowser.open("https://www.google.com")

# Open Network Settings
def open_network_settings():
    os.system("start ms-settings:network")

# Search Location
def search_location(query):
    url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}"
    webbrowser.open(url)

# Open Camera
def open_camera():
    ec.capture(0, "Atmos Camera", "camera_capture.jpg")

# Function to execute tasks
def execute_task(command):
    global listening_active, speaking_active
    response = "I'm not sure how to handle that command."

    if not listening_active:
        return "Listening is turned off."

    if "stop listening" in command or "stop" in command:
        listening_active = False
        response = "Listening stopped. Click the mic button to resume."

    elif "weather" in command:
        response = get_weather("Kanpur")  # Example default location

    elif "open camera" in command:
         open_camera()
         response = "Opening camera."

    elif "search location" in command or "find location" in command:
         speak("What location do you want to search for?")
         location = recognize_speech()
         search_location(location)
         response = f"Searching Google Maps for {location}."


    elif "open google" in command:
         speak("What would you like to search for?")
         search_query = recognize_speech()
         if search_query and search_query != "Sorry, I couldn't understand that.":
           url = f"https://www.google.com/search?q={search_query.replace(' ', '+')}"
           webbrowser.open(url)
           response = f"Searching Google for {search_query}."
         else:
           response = "I couldn't recognize the search query."

    elif "open network settings" in command:
         open_network_settings()
         response = "Opening Network settings."

    elif "open file explorer" in command:
         open_file_explorer()
         response = "Opening File Explorer."

    elif "system info" in command:
         info = system_info()
         response = f"System: {info.system}, Version: {info.version}, Machine: {info.machine}"


    elif "open notepad" in command:
         open_notepad()
         response = "Opening Notepad."

    elif "increase volume" in command:
         increase_volume()
         response = "Increasing volume."

    elif "decrease volume" in command:
         decrease_volume()
         response = "Decreasing volume."


    elif "open youtube" in command:
        speak("What would you like to search for?")
        search_query = recognize_speech()
        url = f"https://www.youtube.com/results?search_query={search_query.replace(' ', '+')}"
        webbrowser.open(url)
        response = f"Searching YouTube for {search_query}."

    elif "shutdown" in command or "shut down my pc" in command:
        response = shutdown_pc()

    elif "restart" in command or "reboot pc" in command:
        response = restart_pc()

    elif "sleep" in command or "sleep mode" in command:
        requests.get("http://127.0.0.1:5000/api/sleep")
        response = "Putting the PC to sleep."

    elif "who created you" in command:
        response = "I have been created by Team Atmos."

    else:
        response = ask_gemini(command)

    return response  # 🔥 Only return text, do NOT call speak() 
# 🔥 Sleep PC
@app.route("/api/sleep", methods=["GET"])
def sleep_pc():
    try:
        system = platform.system()
        if system == "Windows":
            os.system("rundll32.exe powrprof.dll,SetSuspendState Sleep")
        elif system == "Linux":
            os.system("systemctl suspend")  # Correct Linux command
        else:
            return jsonify({"response": "Unsupported OS"}), 400

        return jsonify({"response": "PC is going to sleep."}), 200
    except Exception as e:
        return jsonify({"response": f"Error putting PC to sleep: {e}"}), 500

# API to continuously listen until stopped by mic button
@app.route("/api/listen", methods=["GET"])
def listen_command():
    global listening_active
    if not listening_active:
        return jsonify({"command": "", "response": "Listening is turned off. Click the mic button to resume."})

    command = recognize_speech()
    response = execute_task(command)  # 🔥 Only returns text now
    return jsonify({"command": command, "response": response})
    
# API to toggle listening state when mic button is clicked
@app.route("/api/toggle_listen", methods=["POST"])
def toggle_listening():
    global listening_active
    listening_active = not listening_active
    state = "on" if listening_active else "off"
    return jsonify({"message": f"Listening turned {state}."})

# Function to get weather
def get_weather(city="Kanpur"):
    api_key = "bd5e378503939ddaee76f12ad7a97608"
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    try:
        response = requests.get(url)
        data = response.json()
        if data.get("cod") == 200:
            temp = data["main"]["temp"]
            description = data["weather"][0]["description"]
            return f"The temperature in {city} is {temp}°C with {description}."
        return f"Could not fetch weather data."
    except Exception as e:
        return f"Weather API error: {e}"

# API to handle text-based Atmos requests
@app.route("/api/atmos", methods=["POST"])
def atmos_response():
    data = request.get_json()
    command = data.get("command", "")
    if not command:
        return jsonify({"error": "No command provided"}), 400
    response = execute_task(command)
    return jsonify({"response": response})

# API to stop execution
@app.route("/api/stop", methods=["POST"])
def stop_execution():
    global listening_active
    listening_active = False
    return jsonify({"message": "Listening stopped."})

if __name__ == "__main__":
    print("Atmos Assistant is running...")
    app.run(debug=True, host="0.0.0.0", port=5000)
