from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('Virtual.html')

@app.route('/get_weather', methods=['POST'])
def get_weather():
    city = request.form['city']
    api_key = '06d3d50a82654699cb0e3c046e6c2954'  # Replace with your actual API key
    weather_url = f'http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}'
    
    try:
        response = requests.get(weather_url)
        data = response.json()
        temperature = data['main']['temp']
        return jsonify({'temperature': temperature})
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)
