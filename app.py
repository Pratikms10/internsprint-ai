from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

# Fix: read CORS_ORIGINS (plural) and support comma-separated list
cors_origins = os.getenv("CORS_ORIGINS", "*")
if cors_origins != "*":
    cors_origins = [o.strip() for o in cors_origins.split(",")]

CORS(app, origins=cors_origins, supports_credentials=False)

from routes.match import match_bp
from routes.skillgap import skillgap_bp
from routes.health import health_bp

app.register_blueprint(health_bp)
app.register_blueprint(match_bp)
app.register_blueprint(skillgap_bp)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)