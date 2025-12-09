from flask import Flask, request, jsonify
from ytmusicapi import YTMusic
import requests
import json

app = Flask(__name__)
ytmusic = YTMusic()

# 1. Cobalt (Best Quality, unstable)
COBALT_INSTANCES = [
    "https://cobalt.154.53.53.53.sslip.io",
    "https://api.cobalt.koyeb.app",
    "https://cobalt.ducks.party",
    "https://cobalt.synced.ly",
]

# 2. Piped (Reliable API, but aggressive caching/blocks)
PIPED_INSTANCES = [
    "https://pipedapi.kavin.rocks",
    "https://api-piped.mha.fi",
    "https://pipedapi.drgns.space",
    "https://pipedapi.tokhmi.xyz",
    "https://pipedapi.moomoo.me"
]

# 3. Invidious (Old faithful, strict rate limits but often works)
INVIDIOUS_INSTANCES = [
    "https://inv.tux.pizza",
    "https://vid.puffyan.us",
    "https://invidious.drgns.space",
    "https://invidious.lunar.icu",
    "https://iv.ggtyler.dev"
]

@app.route('/', methods=['GET'])
def home():
    return "Zenify Proxy Server Running (Active)", 200

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
    
    # Shared Headers to mimic browser
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Origin': 'https://www.youtube.com',
        'Referer': 'https://www.youtube.com/'
    }
    
    # --- STRATEGY 1: COBALT ---
    for instance in COBALT_INSTANCES:
        try:
            print(f"Trying Cobalt: {instance}")
            payload = {'url': youtube_url, 'downloadMode': 'audio', 'audioFormat': 'mp3'}
            
            # verify=False fixes 'sslip.io'
            resp = requests.post(instance, json=payload, headers=headers, timeout=8, verify=False)
            
            # 404/405 -> Try /api/json (V7/V10 compat)
            if resp.status_code in [404, 405]:
                 resp = requests.post(f"{instance}/api/json", json=payload, headers=headers, timeout=8, verify=False)

            if resp.status_code == 200:
                data = resp.json()
                if data.get('status') in ['stream', 'redirect'] and data.get('url'):
                    print(f"Cobalt Success: {instance}")
                    return jsonify({'url': data['url']})
            else:
                print(f"Cobalt {instance} status {resp.status_code}")

        except Exception as e:
            print(f"Cobalt {instance} error: {e}")
            continue

    # --- STRATEGY 2: PIPED ---
    for instance in PIPED_INSTANCES:
        try:
            print(f"Trying Piped: {instance}")
            resp = requests.get(f"{instance}/streams/{video_id}", headers=headers, timeout=8)
            
            if resp.status_code == 200:
                data = resp.json()
                for stream in data.get('audioStreams', []):
                    if stream.get('mimeType') == 'audio/mp4':
                        print(f"Piped Success: {instance}")
                        return jsonify({'url': stream['url']})
                        
                if data.get('audioStreams'):
                     print(f"Piped Fallback Success: {instance}")
                     return jsonify({'url': data['audioStreams'][0]['url']})
            else:
                 print(f"Piped {instance} status {resp.status_code}")

        except Exception as e:
            print(f"Piped {instance} error: {e}")
            continue

    # --- STRATEGY 3: INVIDIOUS (New!) ---
    for instance in INVIDIOUS_INSTANCES:
        try:
            print(f"Trying Invidious: {instance}")
            resp = requests.get(f"{instance}/api/v1/videos/{video_id}", headers=headers, timeout=8)
            
            if resp.status_code == 200:
                data = resp.json()
                # Sort by quality/bitrate if possible, but taking first valid logic
                for stream in data.get('formatStreams', []):
                    # Request audio/mp4 or any audio container
                    if 'audio' in stream.get('type', '') or stream.get('container') == 'm4a':
                         print(f"Invidious Success: {instance}")
                         return jsonify({'url': stream['url']})
                
                # Check adaptive streams (audio only)
                for stream in data.get('adaptiveFormats', []):
                    if 'audio' in stream.get('type', ''):
                         print(f"Invidious Adaptive Success: {instance}")
                         return jsonify({'url': stream['url']})
            else:
                 print(f"Invidious {instance} status {resp.status_code}")
                 
        except Exception as e:
            print(f"Invidious {instance} error: {e}")
            continue

    return jsonify({"error": "All instances (Cobalt, Piped, Invidious) failed"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
