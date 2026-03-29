from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000", os.getenv("CORS_ORIGIN", "*")])

from routes.match import match_bp
from routes.skillgap import skillgap_bp
from routes.health import health_bp

app.register_blueprint(health_bp)
app.register_blueprint(match_bp)
app.register_blueprint(skillgap_bp)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)