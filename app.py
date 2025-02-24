from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import google.generativeai as genai
import requests
import webbrowser
import platform

# Check if running on Render
running_on_render = os.getenv("RENDER") is not None

# Try importing speech recognition (Only works on Windows/Linux)
try:
    import speech_recognition as sr
    sr_available = True
except ImportError:
    sr_available = False

# Flask app setup
app = Flask(__name__)
CORS(app)

# Set Gemini API key
GENAI_API_KEY = "AIzaSyBTxpFrER0nGFSGiCwFm4tE9cbbBMfg_g8"  # 🔹 Replace with actual Gemini API Key
genai.configure(api_key=GENAI_API_KEY)

# Function to query Gemini API
def ask_gemini(prompt):
    try:
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(prompt)
        return response.text if response else "I couldn't generate a response."
    except Exception as e:
        return f"Gemini API error: {e}"


# Function to handle speech recognition (Only works on local systems)
def recognize_speech():
    if running_on_render or not sr_available:
        return "Speech recognition is disabled on Render."

    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        try:
            audio = recognizer.listen(source)
            command = recognizer.recognize_google(audio, language="en-IN").lower()
            print(f"Recognized: {command}")
            return command
        except sr.UnknownValueError:
            return "Sorry, I couldn't understand that."
        except sr.RequestError:
            return "Speech recognition service is unavailable."

# Function to execute tasks
def execute_task(command):
    response = "I'm not sure how to handle that command."

    if "weather" in command:
        response = get_weather("Kanpur")  # Example default location

    elif "search location" in command or "find location" in command:
        webbrowser.open(f"https://www.google.com/maps/search/{command.replace('search location ', '').strip()}")
        response = f"Searching Google Maps for {command}."

    elif "open google" in command:
        webbrowser.open("https://www.google.com")
        response = "Opening Google."

    elif "open youtube" in command:
        search_query = command.replace("open youtube ", "").strip()
        webbrowser.open(f"https://www.youtube.com/results?search_query={search_query}")
        response = f"Searching YouTube for {search_query}."

    elif "shutdown" in command:
        response = "Shutting down the system."
        os.system("shutdown /s /t 1")

    elif "restart" in command:
        response = "Restarting the system."
        os.system("shutdown /r /t 1")

    elif "sleep" in command:
        response = sleep_pc()

    elif "who created you" in command:
        response = "I have been created by Team Atmos."

    else:
        response = ask_gemini(command)

    return response

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

# API to receive text-based commands from the frontend
@app.route("/api/listen", methods=["POST"])
def listen_command():
    data = request.get_json()
    command = data.get("command", "").strip()

    if not command:
        return jsonify({"error": "No command provided"}), 400

    response = execute_task(command)
    return jsonify({"command": command, "response": response})

# API to handle Atmos responses
@app.route("/api/atmos", methods=["POST"])
def atmos_response():
    data = request.get_json()
    command = data.get("command", "").strip()

    if not command:
        return jsonify({"error": "No command provided"}), 400

    response = execute_task(command)
    return jsonify({"response": response})

# Sleep PC
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

# Start Flask Server
if __name__ == "__main__":
    print("Atmos Assistant is running...")
    app.run(debug=False, host="0.0.0.0", port=5000)
