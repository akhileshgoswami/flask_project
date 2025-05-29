from flask import Flask, jsonify
from states import indian_states
import os

app = Flask(__name__)

@app.route('/states', methods=['GET'])
def get_states():
    return jsonify({
        "states": indian_states,
        "count": len(indian_states)
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5050))
    app.run(host='0.0.0.0', port=port)
