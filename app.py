from flask import Flask, request, jsonify
from ytmusicapi import YTMusic
import requests
import json

app = Flask(__name__)
ytmusic = YTMusic()

# Server-Side Instance List (More reliable than Client-Side)
COBALT_INSTANCES = [
    "https://cobalt.154.53.53.53.sslip.io",
    "https://api.cobalt.koyeb.app",
    "https://cobalt.ducks.party",
    "https://cobalt.synced.ly",
]

PIPED_INSTANCES = [
    "https://pipedapi.kavin.rocks",
    "https://api-piped.mha.fi",
    "https://pipedapi.drgns.space",
]

@app.route('/', methods=['GET'])
def home():
    return "Zenify Proxy Server Running", 200

@app.route('/search', methods=['GET'])
def search_song():
    query = request.args.get('query') or request.args.get('q')
    if not query:
        return jsonify({"error": "No query provided"}), 400

    try:
        results = ytmusic.search(query, filter="songs")
        clean_results = []
        for song in results:
            if song['resultType'] == 'song':
                clean_results.append({
                    "name": song['title'],
                    "artist": song['artists'][0]['name'] if song['artists'] else "Unknown",
                    "image": song['thumbnails'][-1]['url'] if song['thumbnails'] else "",
                    "id": song['videoId']
                })
        return jsonify(clean_results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/stream', methods=['GET'])
def stream_song():
    video_id = request.args.get('id')
    if not video_id:
        return jsonify({"error": "No Video ID"}), 400

    youtube_url = f"https://www.youtube.com/watch?v={video_id}"
    
    # 1. Try Cobalt Instances
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    for instance in COBALT_INSTANCES:
        try:
            print(f"Trying Cobalt: {instance}")
            # Try V10 API (Root)
            payload = {
                'url': youtube_url,
                'downloadMode': 'audio',
                'audioFormat': 'mp3'
            }
            resp = requests.post(instance, json=payload, headers=headers, timeout=5)
            
            # Fallback to /api/json if root fails (V7 compatibility)
            if resp.status_code == 404:
                 resp = requests.post(f"{instance}/api/json", json=payload, headers=headers, timeout=5)

            if resp.status_code == 200:
                data = resp.json()
                if data.get('status') in ['stream', 'redirect'] and data.get('url'):
                    return jsonify({'url': data['url']})
        except Exception as e:
            print(f"Cobalt {instance} failed: {e}")
            continue

    # 2. Try Piped Instances (Backup)
    for instance in PIPED_INSTANCES:
        try:
            print(f"Trying Piped: {instance}")
            resp = requests.get(f"{instance}/streams/{video_id}", headers=headers, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                audio_streams = data.get('audioStreams', [])
                # Find mp4 audio
                for stream in audio_streams:
                    if stream.get('mimeType') == 'audio/mp4':
                        return jsonify({'url': stream['url']})
                # Fallback to any stream
                if audio_streams:
                     return jsonify({'url': audio_streams[0]['url']})
        except Exception as e:
            print(f"Piped {instance} failed: {e}")
            continue

    return jsonify({"error": "All instances failed"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
