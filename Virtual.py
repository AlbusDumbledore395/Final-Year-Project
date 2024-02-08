from flask import Flask, render_template, Response, redirect, url_for, jsonify, request
import os
import requests
import pytube
import pyjokes
app = Flask(__name__)
greetings = ["hello", "hi", "hey", "greetings", "howdy", "hai"]
farewells = ["goodbye", "bye", "see you later", "farewell"]
questions = ["how are you?", "what's up?", "how's it going?"]
responses = {
    "hello": "Hello! How can I assist you today?",
    "hi": "Hi there! How can I help you?",
    "hey": "Hey! What can I do for you?",
    "greetings": "Greetings! How can I assist you today?",
    "hai": "Hai! How can I assist you today?",  # Added "hai" response
    "how are you?": "I'm just a bot, so I'm always doing fine. How about you?",
    "what's up?": "Not much, just here to help. How can I assist you?",
    "how's it going?": "I'm doing well. How about yourself?",
    "stress": "I'm here to guide you out of it. Take a deep breath and let's talk about it.\n\nTasks that I can perform:\n1) I can give weather report\n2) If you give me a prompt to search in YouTube, I can do it\n3) I can tell you a joke\n4) I can provide you with nature soundscape music.",
    "default": "I'm sorry, I didn't understand that. Can you please rephrase?"
}

# Remedies for stress
stress_remedies = [
    ("Take a few deep breaths. Inhale deeply through your nose, hold for a moment, and then exhale slowly through your mouth.", "Deep breathing can help calm your mind and body."),
    ("Go for a short walk or spend some time outdoors. Fresh air and nature can help reduce stress levels.", "Being in nature has a calming effect on the mind."),
    ("Listen to calming music or sounds. Instrumental music or nature sounds can help relax your mind.", "Music has the power to soothe the soul."),
    ("Practice mindfulness or meditation. Take a few moments to focus on your breath and be present in the moment.", "Mindfulness can help bring awareness to your thoughts and emotions."),
    ("Engage in a hobby or activity you enjoy. Doing something you love can distract your mind from stressors.", "Hobbies provide a positive outlet for stress."),
    ("Reach out to a friend or loved one for support. Sharing your feelings with others can help lighten the load.", "Talking to someone you trust can provide emotional support."),
]

# Function to get weather report
def get_weather_report(district):
    api_key = "4f73fd4ea90e2d50e1755c2767855962"
    url = f"http://api.openweathermap.org/data/2.5/weather?q={district}&appid={api_key}&units=metric"
    response = requests.get(url)
    data = response.json()
    if data["cod"] == 200:
        weather_description = data["weather"][0]["description"]
        temperature = data["main"]["temp"]
        return weather_description, temperature
    else:
        return None, None

# Function to search YouTube
def search_youtube(query):
    search_results = []
    youtube_url = "https://www.youtube.com/results?search_query="
    search_query = "+".join(query.split())
    url = youtube_url + search_query
    response = requests.get(url)
    if response.status_code == 200:
        # Extract video IDs from search results
        video_ids = []
        start_index = response.text.find('videoId":"') + len('videoId":"')
        while start_index != -1 + len('videoId":"'):
            end_index = response.text.find('"', start_index)
            video_id = response.text[start_index:end_index]
            video_ids.append(video_id)
            start_index = response.text.find('videoId":"', end_index)
        # Construct video URLs
        for video_id in video_ids:
            search_results.append("https://www.youtube.com/watch?v=" + video_id)
    return search_results

# Function to generate a joke
def get_joke():
    return pyjokes.get_joke()

# Function to provide nature soundscape music
def get_nature_soundscape_music():
    return "https://www.youtube.com/playlist?list=PLD1nCoeovTZ5lK3xcCpqVUor6c2lkxSgG"

# Function to generate responses
def generate_response(message, username):
    message = message.lower()
    if "stress" in message:
        return responses["stress"].replace("you", username)
    elif "weather" in message:
        return "Please provide your district name."
    elif "youtube" in message:
        return "Please provide your search query."
    elif "joke" in message:
        return get_joke()
    elif "nature soundscape music" in message:
        return get_nature_soundscape_music()
    elif message in responses:
        return responses[message].replace("you", username)
    elif message in greetings:
        return random.choice(greetings).replace("you", username)
    elif message in farewells:
        return random.choice(farewells).replace("you", username)
    elif "?" in message:
        return "I'm sorry, I'm not equipped to answer questions.".replace("you", username)
    else:
        return responses["default"].replace("you", username)

@app.route('/get-response', methods=['POST'])
def get_response():
    data = request.get_json()
    user_message = data['message']
    username = data['username']
    bot_response = generate_response(user_message, username)
    return jsonify({'response': bot_response})

@app.route('/virtual')
def virtual():
    return render_template('Virtual.html')
if __name__ == '__main__':
    app.run(debug=True)
