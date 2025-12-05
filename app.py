from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import os
import tempfile
from pathlib import Path
import subprocess
app = Flask(__name__)
CORS(app)
@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "service": "spotdl"})
@app.route('/download', methods=['GET'])
def download():
    """Download using spotdl - works for both search queries and URLs"""
    try:
        query = request.args.get('q')
        if not query:
            return jsonify({"error": "Missing 'q' parameter"}), 400
        
        temp_dir = tempfile.mkdtemp()
        
        # spotdl works with both search queries and URLs!
        result = subprocess.run(
            ['spotdl', query, '--output', temp_dir, '--format', 'mp3'],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode != 0:
            return jsonify({"error": f"Download failed: {result.stderr}"}), 500
        
        # Find the downloaded file
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
