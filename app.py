from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import os
import sys

app = Flask(__name__)

# For production (Railway), use DATABASE_URL; fallback to local SQLite for dev
db_url = os.environ.get('DATABASE_URL', 'sqlite:///test.db')
if db_url.startswith("postgres://"):
    # Fix for old postgres URL format
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Country model
class Country(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

    def __repr__(self):
        return f'<Country {self.name}>'

# Route: Get all countries
@app.route('/countries', methods=['GET'])
def get_countries():
    countries = Country.query.all()
    return jsonify({
        "countries": [{"id": c.id, "name": c.name} for c in countries],
        "count": len(countries)
    })

# Route: Add a new country
@app.route('/countries', methods=['POST'])
def add_country():
    data = request.get_json()
    country_name = data.get('name')
    if not country_name:
        return jsonify({"error": "Country name is required"}), 400

    # Check if country already exists
    existing = Country.query.filter_by(name=country_name).first()
    if existing:
        return jsonify({"error": "Country already exists"}), 400

    new_country = Country(name=country_name)
    db.session.add(new_country)
    db.session.commit()
    return jsonify({"message": f"Country '{country_name}' added.", "id": new_country.id}), 201

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'initdb':
        # Initialize the database tables if run with 'initdb' argument
        with app.app_context():
            db.create_all()
            print("✅ Database tables created.")
    else:
        port = int(os.environ.get('PORT', 5051))
        app.run(host='0.0.0.0', port=port, debug=True)
