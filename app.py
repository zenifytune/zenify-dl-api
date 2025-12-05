from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import yt_dlp
import os
import tempfile
from pathlib import Path
app = Flask(__name__)
CORS(app)
@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"})
@app.route('/download/youtube', methods=['GET'])
def download_youtube():
    try:
        video_id = request.args.get('id')
        if not video_id:
            return jsonify({"error": "Missing 'id' parameter"}), 400
        
        temp_dir = tempfile.mkdtemp()
        output_template = os.path.join(temp_dir, '%(id)s.%(ext)s')
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_template,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f'https://www.youtube.com/watch?v={video_id}', download=True)
            filename = f"{video_id}.mp3"
            filepath = os.path.join(temp_dir, filename)
            
            return send_file(filepath, mimetype='audio/mpeg', as_attachment=True, download_name=f"{info.get('title', 'audio')}.mp3")
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))

    app.run(host='0.0.0.0', port=port)

@app.route('/download/spotify', methods=['GET'])
def download_spotify():
    """Download track from Spotify using spotdl"""
    try:
        track_url = request.args.get('url')
        if not track_url:
            return jsonify({"error": "Missing 'url' parameter"}), 400
        
        temp_dir = tempfile.mkdtemp()
        
        # Use spotdl (it downloads from YouTube using Spotify metadata)
        import subprocess
        result = subprocess.run(
            ['spotdl', track_url, '--output', temp_dir, '--format', 'mp3'],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode != 0:
            return jsonify({"error": f"spotdl failed: {result.stderr}"}), 500
        
        # Find the downloaded file
        files = list(Path(temp_dir).glob('*.mp3'))
        if not files:
            return jsonify({"error": "No file downloaded"}), 500
        
        filepath = str(files[0])
        filename = os.path.basename(filepath)
        
        return send_file(filepath, mimetype='audio/mpeg', as_attachment=True, download_name=filename)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
