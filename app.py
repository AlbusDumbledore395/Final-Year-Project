from flask import Flask, render_template, Response, redirect, url_for, jsonify, request
import cv2
import dlib
import random 
import librosa
import numpy as np
from pydub import AudioSegment
import os
app = Flask(__name__)
stored_face_result = None
stored_voice_result = None
@app.route('/voice')
def voice():
    return render_template('voice.html')
@app.route('/')
def index():
    return render_template('home.html')

class StressDetector:
    def __init__(self, shape_predictor_path):
        self.detector = dlib.get_frontal_face_detector()
        self.predictor = dlib.shape_predictor(shape_predictor_path)
        self.stress_intensity = 0
        self.stress_percentage = 0

    def get_landmarks(self, frame, face):
        shape = self.predictor(frame, face)
        landmarks = np.array([[shape.part(i).x, shape.part(i).y] for i in range(shape.num_parts)], dtype=int)
        return landmarks

    def calculate_eye_aspect_ratio(self, eye_landmarks):
        d1 = np.linalg.norm(eye_landmarks[1] - eye_landmarks[5])
        d2 = np.linalg.norm(eye_landmarks[2] - eye_landmarks[4])
        d3 = np.linalg.norm(eye_landmarks[0] - eye_landmarks[3])
        ear = (d1 + d2) / (2.0 * d3)
        return ear

    def calculate_mouth_aspect_ratio(self, mouth_landmarks):
        d1 = np.linalg.norm(mouth_landmarks[0] - mouth_landmarks[6])
        d2 = np.linalg.norm(mouth_landmarks[3] - mouth_landmarks[9])
        d3 = np.linalg.norm(mouth_landmarks[2] - mouth_landmarks[10])
        mar = (d1 + d2) / (2.0 * d3)
        return mar

    def process_frame(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.detector(gray)

        for face in faces:
            landmarks = self.get_landmarks(gray, face)

            left_eye = landmarks[36:42]
            right_eye = landmarks[42:48]
            mouth = landmarks[48:68]

            left_ear = self.calculate_eye_aspect_ratio(left_eye)
            right_ear = self.calculate_eye_aspect_ratio(right_eye)
            avg_ear = (left_ear + right_ear) / 2.0

            mouth_mar = self.calculate_mouth_aspect_ratio(mouth)

            # Additional criteria for stress detection
            eye_closure_threshold = 0.2
            unhappy_threshold = 0.5

            eye_closure_detected = avg_ear < eye_closure_threshold
            unhappy_detected = mouth_mar < unhappy_threshold

            stress_detected = eye_closure_detected or unhappy_detected

            # Calculate stress intensity and percentage
            stress_threshold = 0.2
            self.stress_intensity = min(avg_ear, mouth_mar) / max(stress_threshold, unhappy_threshold) * 100
            self.stress_percentage = min(self.stress_intensity, 100)

            x, y, w, h = face.left(), face.top(), face.width(), face.height()
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.polylines(frame, [left_eye], isClosed=True, color=(0, 255, 0), thickness=2)
            cv2.polylines(frame, [right_eye], isClosed=True, color=(0, 255, 0), thickness=2)
            cv2.polylines(frame, [mouth], isClosed=True, color=(0, 255, 0), thickness=2)

            # Display stress detection result and intensity
            if self.stress_intensity > 50:
                stress_text = f"Stress Detected (Intensity: {self.stress_intensity:.2f}%, Percentage: {self.stress_percentage:.2f}%)"
            else:
                stress_text = "No Stress Detected"

            cv2.putText(frame, stress_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

        return frame

class VideoCamera:
    def __init__(self, shape_predictor_path):
        self.video = cv2.VideoCapture("D:\\final project\\project\\BEST & WORST Movies 2023 _ Shiromani Kant.mp4",)
        self.stress_detector = StressDetector(shape_predictor_path)
        self.total_stress_intensity = 0
        self.frame_count = 0
        self.detection_stopped = False

    def get_frame(self):
        success, frame = self.video.read()
        if success and not self.detection_stopped:
            processed_frame = self.stress_detector.process_frame(frame)

            # Update total stress intensity and frame count
            self.total_stress_intensity += self.stress_detector.stress_intensity
            self.frame_count += 1

            _, jpeg = cv2.imencode('.jpg', processed_frame)
            return jpeg.tobytes()
# Specify the path to the FFmpeg executable
ffmpeg_path = r"C:\\Users\\STUDENT\\Downloads\\ffmpeg-master-latest-win64-gpl-shared\\ffmpeg.exe"
AudioSegment.ffmpeg = ffmpeg_path

def mp3_to_wav(mp3_path, wav_path):
    audio = AudioSegment.from_mp3(mp3_path)
    audio.export(wav_path, format="wav")

def calculate_intensity(signal, sr, duration=10):
    try:
        # Analyze only the first 'duration' seconds
        signal = signal[:int(sr * duration)]

        # Extract features
        chroma = librosa.feature.chroma_stft(y=signal, sr=sr)
        energy = librosa.feature.rms(y=signal)
        zero_crossing_rate = librosa.feature.zero_crossing_rate(y=signal)

        # Analyze chroma variations (replace with the feature you choose)
        chroma_deriv = np.diff(chroma)
        chroma_std = np.std(chroma_deriv)

        # Analyze word stress (replace with an appropriate method)
        onset_frames = librosa.onset.onset_detect(y=signal, sr=sr)
        syllable_count = len(onset_frames)

        # Combine features into a stress score
        stress_score = (0.5 * np.mean(energy) + 0.3 * np.mean(chroma_std) + 0.2 * syllable_count) / 2

        print(f'Stress Score in calculate_intensity: {stress_score}')

        return stress_score

    except Exception as e:
        print(f'Error in calculate_intensity: {str(e)}')
        return 0  # Return a default value in case of an error



@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        audio_file = request.files['audio']
        audio_file_path = 'temp.wav'
        audio_file.save(audio_file_path)

        # If the file is in MP3 format, convert it to WAV
        if audio_file_path.lower().endswith('.mp3'):
            mp3_to_wav(audio_file_path, audio_file_path)

        signal, sr = librosa.load(audio_file_path)
        stress_score = calculate_intensity(signal, sr, duration=10)

        # Calculate average intensity over the entire duration
        average_intensity = stress_score * 10

        # Debugging statements
        print(f'Stress Score: {stress_score}')
        print(f'Average Intensity: {average_intensity}')

        # Store the voice stress result
        voice_result = {
            'average_intensity': average_intensity,
            'is_stressed': average_intensity > 50  # Set your threshold here
        }

        global stored_voice_result
        stored_voice_result = voice_result

        result = {
            'status': 'success',
            'message': 'Analysis completed successfully.',
            'average_intensity': average_intensity
        }
        return jsonify(result)

    except Exception as e:
        result = {
            'status': 'error',
            'message': f'Error: {str(e)}'
        }
        return jsonify(result)

    finally:
        # Clean up temporary WAV file if created
        if os.path.exists(audio_file_path):
            os.remove(audio_file_path)

video_camera = None

@app.route('/face')
def face():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    global video_camera
    return Response(gen(video_camera), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/start_stress_detection', methods=['POST'])
def start_stress_detection():
    global video_camera
    if not video_camera:
        video_camera = VideoCamera("D:\\final project\\project\\shape_predictor_68_face_landmarks.dat")
    return redirect(url_for('face'))

from flask import render_template, redirect, url_for

@app.route('/stop_video', methods=['POST'])
def stop_video():
    global video_camera
    if video_camera:
        average_stress_intensity = 0 if video_camera.frame_count == 0 else video_camera.total_stress_intensity / video_camera.frame_count
        stress_result = {
            'average_intensity': average_stress_intensity,
            'is_stressed': average_stress_intensity > 60
        }

        # Store the stress result in a global variable or a database for later retrieval
        global stored_face_result
        stored_face_result = stress_result

        video_camera.video.release()
        video_camera.detection_stopped = True
        video_camera = None

        # Redirect to the dot puzzle page
        return redirect(url_for('dot'))
    else:
        return render_template('index.html')


def gen(camera):
    while True:
        if video_camera and video_camera.video.isOpened():
            frame = camera.get_frame()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        else:
            break
@app.route('/dot')
def dot():
    return render_template('dot.html')
@app.route('/generate_dots/<int:num_dots>')
def generate_dots(num_dots):
    dots = [(random.randint(1, 10), random.randint(1, 10)) for _ in range(num_dots)]
    return jsonify(dots)
@app.route('/next')
def next():
    global stored_face_result
    global stored_voice_result

    face_stress_result = stored_face_result
    voice_stress_result = stored_voice_result

    return render_template('result.html', stress_result=face_stress_result, voice_result=voice_stress_result)
@app.route('/game')
def game():
    return render_template('game1.html')

if __name__ == '__main__':
    app.run(debug=True)