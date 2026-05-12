"""Blueprint de autenticação: register, login, refresh."""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from flask_bcrypt import generate_password_hash, check_password_hash
from models import SessionLocal, User
import re

auth_bp = Blueprint('auth', __name__)

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body is required"}), 400

    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    # Validações
    if not email or not EMAIL_REGEX.match(email):
        return jsonify({"error": "Invalid email format"}), 400

    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400

    session = SessionLocal()
    try:
        # Verifica duplicidade
        existing = session.query(User).filter_by(email=email).first()
        if existing:
            return jsonify({"error": "Email already registered"}), 409

        # Cria usuário
        password_hash = generate_password_hash(password, rounds=12).decode('utf-8')
        user = User(
            email=email,
            password_hash=password_hash,
            nome=data.get('nome', '').strip(),
            cep=data.get('cep', '').strip(),
            endereco=data.get('endereco', '').strip(),
            numero=data.get('numero', '').strip(),
            complemento=data.get('complemento', '').strip(),
            bairro=data.get('bairro', '').strip(),
            cidade=data.get('cidade', '').strip(),
            uf=data.get('uf', '').strip(),
        )
        session.add(user)
        session.commit()

        # Gera tokens
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))

        return jsonify({
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": {"id": user.id, "email": user.email}
        }), 201

    except Exception as e:
        session.rollback()
        return jsonify({"error": "Internal server error"}), 500
    finally:
        session.close()


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body is required"}), 400

    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    session = SessionLocal()
    try:
        user = session.query(User).filter_by(email=email).first()

        if not user or not check_password_hash(user.password_hash, password):
            return jsonify({"error": "Invalid credentials"}), 401

        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))

        return jsonify({
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": {"id": user.id, "email": user.email}
        }), 200

    except Exception as e:
        return jsonify({"error": "Internal server error"}), 500
    finally:
        session.close()


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    current_user_id = get_jwt_identity()
    access_token = create_access_token(identity=current_user_id)
    return jsonify({"access_token": access_token}), 200
