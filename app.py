from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# For production (Railway), use DATABASE_URL environment variable.
# For local testing, fallback to SQLite.
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///test.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Model for Country
class Country(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

    def __repr__(self):
        return f'<Country {self.name}>'

# Route to get all countries
@app.route('/countries', methods=['GET'])
def get_countries():
    countries = Country.query.all()
    return jsonify({
        "countries": [{"id": c.id, "name": c.name} for c in countries],
        "count": len(countries)
    })

# Route to add a new country
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
    with app.app_context():
        db.create_all()  # Create tables inside app context
    port = int(os.environ.get('PORT', 5051))
    app.run(host='0.0.0.0', port=port, debug=True)
