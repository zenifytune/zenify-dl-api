from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import yt_dlp
import os
import tempfile
from pathlib import Path
import subprocess
app = Flask(__name__)
CORS(app)
@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "services": ["youtube", "spotify"]})
@app.route('/download/youtube', methods=['GET'])
def download_youtube():
    """Download audio from YouTube with bot bypass"""
    try:
        video_id = request.args.get('id')
        if not video_id:
            return jsonify({"error": "Missing 'id' parameter"}), 400
        
        temp_dir = tempfile.mkdtemp()
        output_template = os.path.join(temp_dir, '%(id)s.%(ext)s')
        
        # Enhanced yt-dlp options to bypass bot detection
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_template,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
            'no_warnings': True,
            # Anti-bot measures
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web'],
                    'player_skip': ['webpage', 'configs'],
                }
            },
            # Mimic real browser
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-us,en;q=0.5',
                'Sec-Fetch-Mode': 'navigate',
            }
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f'https://www.youtube.com/watch?v={video_id}', download=True)
            filename = f"{video_id}.mp3"
            filepath = os.path.join(temp_dir, filename)
            
            return send_file(
                filepath,
                mimetype='audio/mpeg',
                as_attachment=True,
                download_name=f"{info.get('title', 'audio')}.mp3"
            )
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@app.route('/download/spotify', methods=['GET'])
def download_spotify():
    """Download track from Spotify using spotdl"""
    try:
        track_url = request.args.get('url')
        if not track_url:
            return jsonify({"error": "Missing 'url' parameter"}), 400
        
        temp_dir = tempfile.mkdtemp()
        
        result = subprocess.run(
            ['spotdl', track_url, '--output', temp_dir, '--format', 'mp3'],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode != 0:
            return jsonify({"error": f"spotdl failed: {result.stderr}"}), 500
        
        files = list(Path(temp_dir).glob('*.mp3'))
        if not files:
            return jsonify({"error": "No file downloaded"}), 500
        
        filepath = str(files[0])
        filename = os.path.basename(filepath)
        
        return send_file(
            filepath,
            mimetype='audio/mpeg',
            as_attachment=True,
            download_name=filename
        )
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
