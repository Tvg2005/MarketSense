"""Middleware de autenticação JWT."""

from functools import wraps
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from flask import jsonify


def token_required(f):
    """Decorator que protege endpoints exigindo JWT válido."""
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            verify_jwt_in_request()
            current_user_id = get_jwt_identity()
            return f(current_user_id, *args, **kwargs)
        except Exception as e:
            return jsonify({"error": "Missing or invalid token"}), 401
    return decorated
