from flask import Flask, request, jsonify
from ytmusicapi import YTMusic

app = Flask(__name__)
ytmusic = YTMusic()

@app.route('/', methods=['GET'])
def home():
    return "Zenify Search Engine is Running (Cobalt Mode)", 200

@app.route('/search', methods=['GET'])
def search_song():
    query = request.args.get('query')
    if not query:
        # Fallback for 'q' parameter if used
        query = request.args.get('q')
        
    if not query:
        return jsonify({"error": "No query provided"}), 400

    try:
        # 'filter=songs' ensures we only get music
        results = ytmusic.search(query, filter="songs")
        
        clean_results = []
        for song in results:
            if song['resultType'] == 'song':
                # Standardizing the data for Flutter app
                clean_results.append({
                    "title": song['title'],
                    "artist": song['artists'][0]['name'] if song['artists'] else "Unknown",
                    "image": song['thumbnails'][-1]['url'] if song['thumbnails'] else "",
                    "id": song['videoId']
                })
        
        return jsonify(clean_results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
