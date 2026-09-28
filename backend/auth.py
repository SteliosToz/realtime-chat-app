from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from extensions import db
from models import User

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({"error": "Λείπουν στοιχεία (username, email, password)"}), 400

    if User.query.filter((User.username == username) | (User.email == email)).first():
        return jsonify({"error": "Το username ή το email χρησιμοποιείται ήδη"}), 400

    new_user = User(username=username, email=email)
    new_user.set_password(password)

    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "Ο λογαριασμός δημιουργήθηκε επιτυχώς"}), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email).first()

    if not user or not user.check_password(password):
        return jsonify({"error": "Λάθος email ή password"}), 401

    access_token = create_access_token(identity=str(user.id))

    return jsonify({
        "access_token": access_token,
        "user": {"id": user.id, "username": user.username, "email": user.email}
    }), 200