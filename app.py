from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import os
import sys
from sqlalchemy import func
import instaloader
import re

app = Flask(__name__)

# For production (Railway), use DATABASE_URL; fallback to local SQLite for dev
db_url = os.environ.get('DATABASE_URL', 'sqlite:///test.db')
if db_url.startswith("postgres://"):
    # Fix for old postgres URL format
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# === Database Model ===
class Country(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

    def __repr__(self):
        return f'<Country {self.name}>'

# === Route: Get all countries ===
@app.route('/countries', methods=['GET'])
def get_countries():
    countries = Country.query.all()
    return jsonify({
        "countries": [{"id": c.id, "name": c.name} for c in countries],
        "count": len(countries)
    })

# === Route: Add a new country ===
@app.route('/countries', methods=['POST'])
def add_country():
    data = request.get_json()
    country_name = data.get('name')
    if not country_name:
        return jsonify({"error": "Country name is required"}), 400

    existing = Country.query.filter(func.lower(Country.name) == country_name.lower()).first()
    if existing:
        return jsonify({"error": "Country already exists"}), 400

    new_country = Country(name=country_name)
    db.session.add(new_country)
    db.session.commit()
    return jsonify({"message": f"Country '{country_name}' added.", "id": new_country.id}), 201

# === Helper: Extract Instagram shortcode ===
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

# === Route: Instagram video download URL ===
@app.route('/download_instagram', methods=['POST'])
def download_instagram():
    data = request.get_json()
    url = data.get('url')

    if not url:
        return jsonify({"error": "Instagram URL is required"}), 400

    shortcode = extract_shortcode(url)
    if not shortcode:
        return jsonify({"error": "Invalid Instagram URL format"}), 400

    L = instaloader.Instaloader()
    try:
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

# === Run App ===
if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'initdb':
        with app.app_context():
            db.create_all()
            print("✅ Database tables created.")
    else:
        port = int(os.environ.get('PORT', 5051))
        app.run(host='0.0.0.0', port=port, debug=True)
