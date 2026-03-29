from flask import Blueprint, jsonify
from datetime import datetime

health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "UP",
        "service": "InternSprint AI Module",
        "timestamp": datetime.now().isoformat()
    })
