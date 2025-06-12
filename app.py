from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from sqlalchemy import func
from dotenv import load_dotenv
import os
import sys
import instaloader
import re

# Load environment variables from .env (for local dev)
load_dotenv()

app = Flask(__name__)
CORS(app)

# Database config
db_url = os.environ.get('DATABASE_URL', 'sqlite:///test.db')
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# === DB Model ===
class Country(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

    def __repr__(self):
        return f'<Country {self.name}>'

# === Routes ===
@app.route('/countries', methods=['GET'])
def get_countries():
    countries = Country.query.all()
    return jsonify({
        "countries": [{"id": c.id, "name": c.name} for c in countries],
        "count": len(countries)
    })

@app.route('/login_instagram', methods=['GET'])
def login_instagram():
    insta_user = os.environ.get("INSTA_USERNAME")
    insta_pass = os.environ.get("INSTA_PASSWORD")

    if not insta_user or not insta_pass:
        return jsonify({"error": "Username and password are required as query params"}), 400

    try:
        L = instaloader.Instaloader()
        L.login(insta_user, insta_pass)
        L.save_session_to_file()
        return jsonify({"message": f"✅ Logged in and session saved as .session-{insta_user}"}), 200
    except Exception as e:
        return jsonify({"error": f"Login failed: {str(e)}"}), 500

# === Helpers ===
def extract_shortcode(url):
    patterns = [
        r'/reel/([A-Za-z0-9_-]+)/',
        r'/p/([A-Za-z0-9_-]+)/',
        r'/tv/([A-Za-z0-9_-]+)/'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

# === Instagram downloader (anonymous) ===
@app.route('/download_instagram', methods=['POST'])
def download_instagram():
    data = request.get_json()
    url = data.get('url')
    if not url:
        return jsonify({"error": "Instagram URL is required"}), 400

    shortcode = extract_shortcode(url)
    if not shortcode:
        return jsonify({"error": "Invalid Instagram URL format"}), 400

    try:
        L = instaloader.Instaloader()
        L.context._session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/119.0.0.0 Safari/537.36'
        })

        post = instaloader.Post.from_shortcode(L.context, shortcode)

        if post.is_video:
            return jsonify({
                "video_url": post.video_url,
                "caption": post.caption,
                "author": post.owner_username
            }), 200
        else:
            return jsonify({"error": "This post does not contain a video"}), 400

    except Exception as e:
        return jsonify({"error": f"Failed to fetch video: {str(e)}"}), 500

@app.route('/download_instagram_login', methods=['POST'])
def download_instagram_with_login():
    data = request.get_json()
    url = data.get('url')
    if not url:
        return jsonify({"error": "Instagram URL is required"}), 400

    shortcode = extract_shortcode(url)
    if not shortcode:
        return jsonify({"error": "Invalid Instagram URL format"}), 400

    insta_user = os.environ.get("INSTA_USERNAME")
    insta_pass = os.environ.get("INSTA_PASSWORD")

    if not insta_user or not insta_pass:
        return jsonify({"error": "Instagram credentials not set"}), 500

    try:
        L = instaloader.Instaloader()

        # Try loading saved session
        try:
            L.load_session_from_file(insta_user)
        except FileNotFoundError:
            L.login(insta_user, insta_pass)
            L.save_session_to_file()

        post = instaloader.Post.from_shortcode(L.context, shortcode)

        if post.is_video:
            return jsonify({
                "video_url": post.video_url,
                "caption": post.caption,
                "author": post.owner_username
            }), 200
        else:
            return jsonify({"error": "This post does not contain a video"}), 400

    except Exception as e:
        return jsonify({"error": f"Login or fetch failed: {str(e)}"}), 500

# === App Runner ===
if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'initdb':
        with app.app_context():
            db.create_all()
            print("✅ Database tables created.")
    else:
        port = int(os.environ.get('PORT', 5051))
        app.run(host='0.0.0.0', port=port, debug=True)
