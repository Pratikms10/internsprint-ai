from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
import os
import threading
import time
import urllib.request

load_dotenv()

app = Flask(__name__)

# Fix: read CORS_ORIGINS (plural) correctly
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

# ── Keep-alive: prevents Render free tier from sleeping ──────────
def keep_alive():
    """Ping own /health endpoint every 10 minutes to prevent sleep."""
    SERVICE_URL = os.getenv(
        "SERVICE_URL",
        "https://internsprint-ai.onrender.com/health"
    )
    # Wait 60s for server to fully start before first ping
    time.sleep(60)
    while True:
        try:
            req = urllib.request.urlopen(SERVICE_URL, timeout=10)
            print(f"[keep-alive] ping OK — status {req.status}")
        except Exception as e:
            print(f"[keep-alive] ping failed: {e}")
        time.sleep(600)  # 10 minutes

# Start keep-alive thread as daemon (dies when main process dies)
keep_alive_thread = threading.Thread(target=keep_alive, daemon=True)
keep_alive_thread.start()
print("[keep-alive] background thread started")
# ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
