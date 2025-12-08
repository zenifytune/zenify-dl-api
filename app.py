import os
from flask import Flask, request, jsonify
from ytmusicapi import YTMusic
import yt_dlp

app = Flask(__name__)
ytmusic = YTMusic()

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    if not query:
        return jsonify({'error': 'No query provided'}), 400
    
    try:
        # Search explicitly for songs
        results = ytmusic.search(query, filter='songs')
        # Map to a simpler format compatible with Zenify
        mapped_results = []
        for item in results:
            if item['resultType'] == 'song':
                mapped_results.append({
                    'id': item['videoId'],
                    'name': item['title'],
                    'artists': {'primary': [{'name': a['name']} for a in item['artists']]},
                    'album': {'name': item['album']['name'] if 'album' in item and item['album'] else 'Unknown'},
                    'duration': item.get('duration_seconds', 0),
                    'image': item['thumbnails']
                })
        return jsonify(mapped_results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/stream', methods=['GET'])
def stream():
    video_id = request.args.get('id')
    if not video_id:
        return jsonify({'error': 'No id provided'}), 400
        
    try:
        url = f"https://music.youtube.com/watch?v={video_id}"
        
        # Check for cookies file
        cookie_file = 'cookies.txt'
        if not os.path.exists(cookie_file):
             # Try absolute path just in case
             cookie_file = os.path.join(os.getcwd(), 'cookies.txt')

        has_cookies = os.path.exists(cookie_file)
        cookie_status = "Missing"
        if has_cookies:
            size = os.path.getsize(cookie_file)
            cookie_status = f"Found ({size} bytes) at {cookie_file}"
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'extract_flat': 'in_playlist',
            'verbose': True,
            'extractor_args': {
                'youtube': {
                    'player_client': ['tv_embedded', 'tv', 'android_creator']
                }
            }
        }
        
        if has_cookies:
            ydl_opts['cookiefile'] = cookie_file
            print(f"Using cookies: {cookie_status}")

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return jsonify({'url': info['url']})
            
    except Exception as e:
        # Return extended debug info in the error
        debug_info = {
            'error': str(e),
            'cookie_status': locals().get('cookie_status', 'Unknown'),
            'cwd': os.getcwd(),
            'files_in_dir': os.listdir(os.getcwd())
        }
        print(f"Stream Error: {debug_info}")
        return jsonify(debug_info), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
