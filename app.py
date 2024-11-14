# server.py
from flask import Flask, request, jsonify
import requests
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
AUDD_API_KEY = 'a123b456-c789-012d-e345-f678g901h234'
OPENAI_API_KEY = 'f79a3d8e7b7d42c6aee107040bf27c9f'

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/identify', methods=['POST'])
def identify_song():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']
    filename = secure_filename(file.filename)
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)


    with open(file_path, 'rb') as f:
        response = requests.post(
            'https://api.audd.io/',
            data={'api_token': AUDD_API_KEY, 'return': 'apple_music,spotify'},
            files={'file': f}
        )

    os.remove(file_path) 

    if response.status_code != 200 or 'result' not in response.json():
        return jsonify({"error": "Failed to identify song"}), 500

    song_info = response.json()['result']
    song_title = song_info.get('title')
    artist = song_info.get('artist')

    if not song_title or not artist:
        return jsonify({"error": "Song title or artist not found"}), 404

    prompt = f"Can you provide the lyrics of the song '{song_title}' by {artist}?"
    gpt_response = requests.post(
        'https://tng-openai-eastus2.openai.azure.com/openai/deployments/gpt-4/chat/completions?api-version=2024-06-01',
        headers={
            'Authorization': f'Bearer {OPENAI_API_KEY}',
            'Content-Type': 'application/json'
        },
        json={
            'model': 'text-davinci-003',
            'prompt': prompt,
            'max_tokens': 1000
        }
    )

    if gpt_response.status_code != 200:
        return jsonify({"error": "Failed to retrieve lyrics"}), 500

    lyrics = gpt_response.json().get('choices', [])[0].get('text', '').strip()

    return jsonify({
        "title": song_title,
        "artist": artist,
        "lyrics": lyrics
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
