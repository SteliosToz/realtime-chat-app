from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import Room, RoomMember, User, Message

rooms_bp = Blueprint('rooms', __name__)


@rooms_bp.route('', methods=['POST'])
@jwt_required()
def create_room():
    current_user_id = get_jwt_identity()
    data = request.get_json()

    name = data.get('name')
    is_group = data.get('is_group', False)
    member_ids = data.get('member_ids', [])  # άλλοι χρήστες που θα μπουν στο room

    new_room = Room(name=name, is_group=is_group)
    db.session.add(new_room)
    db.session.commit()

    # Πρόσθεσε τον δημιουργό σαν μέλος
    all_member_ids = set(member_ids + [int(current_user_id)])
    for uid in all_member_ids:
        membership = RoomMember(room_id=new_room.id, user_id=uid)
        db.session.add(membership)

    db.session.commit()

    return jsonify({
        "id": new_room.id,
        "name": new_room.name,
        "is_group": new_room.is_group
    }), 201


@rooms_bp.route('', methods=['GET'])
@jwt_required()
def get_my_rooms():
    current_user_id = get_jwt_identity()

    memberships = RoomMember.query.filter_by(user_id=current_user_id).all()
    rooms = [m.room for m in memberships]

    result = [{"id": r.id, "name": r.name, "is_group": r.is_group} for r in rooms]

    return jsonify(result), 200

@rooms_bp.route('/<int:room_id>/messages', methods=['GET'])
@jwt_required()
def get_room_messages(room_id):
    current_user_id = get_jwt_identity()

    membership = RoomMember.query.filter_by(room_id=room_id, user_id=int(current_user_id)).first()
    if not membership:
        return jsonify({"error": "Δεν είσαι μέλος αυτού του δωματίου"}), 403

    messages = Message.query.filter_by(room_id=room_id).order_by(Message.created_at.asc()).all()

    result = [{
        "id": m.id,
        "user_id": m.user_id,
        "username": m.sender.username,
        "text": m.text,
        "created_at": m.created_at.isoformat()
    } for m in messages]

    return jsonify(result), 200

@rooms_bp.route('/<int:room_id>/members', methods=['POST'])
@jwt_required()
def add_room_member(room_id):
    current_user_id = get_jwt_identity()

    membership = RoomMember.query.filter_by(room_id=room_id, user_id=int(current_user_id)).first()
    if not membership:
        return jsonify({"error": "Δεν είσαι μέλος αυτού του δωματίου"}), 403

    data = request.get_json()
    username = data.get('username')

    user_to_add = User.query.filter_by(username=username).first()
    if not user_to_add:
        return jsonify({"error": "Ο χρήστης δεν βρέθηκε"}), 404

    existing = RoomMember.query.filter_by(room_id=room_id, user_id=user_to_add.id).first()
    if existing:
        return jsonify({"error": "Ο χρήστης είναι ήδη μέλος"}), 400

    new_membership = RoomMember(room_id=room_id, user_id=user_to_add.id)
    db.session.add(new_membership)
    db.session.commit()

    return jsonify({"message": f"Ο {username} προστέθηκε στο δωμάτιο"}), 201