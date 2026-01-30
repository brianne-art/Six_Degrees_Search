from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS
from search import find_path, ArticleNotFoundError, NoPathFoundError

app = Flask(__name__, static_folder='static')
CORS(app)


@app.route('/')
def index():
    return send_from_directory('static', 'index.html')


@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)


@app.route('/find-path', methods=['POST'])
def find_path_endpoint():
    # Parse JSON body
    try:
        data = request.get_json()
        if data is None:
            return jsonify({"success": False, "error": "Invalid request format"}), 400
    except Exception:
        return jsonify({"success": False, "error": "Invalid request format"}), 400

    # Validate input
    start = data.get('start', '').strip() if data.get('start') else ''
    end = data.get('end', '').strip() if data.get('end') else ''

    if not start or not end:
        return jsonify({"success": False, "error": "Both start and end articles required"}), 400

    # Execute search
    try:
        path = find_path(start, end)
        return jsonify({
            "success": True,
            "path": path,
            "length": len(path)
        }), 200

    except ArticleNotFoundError as e:
        return jsonify({"success": False, "error": str(e)}), 404

    except NoPathFoundError as e:
        return jsonify({"success": False, "error": str(e)}), 404

    except Exception as e:
        return jsonify({"success": False, "error": "Error accessing Wikipedia API"}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)
