from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db, socketio
from models import Room, RoomMember, User, Message, Invitation

rooms_bp = Blueprint('rooms', __name__)


@rooms_bp.route('/<int:room_id>/members', methods=['POST'])
@jwt_required()
def invite_to_room(room_id):
    current_user_id = get_jwt_identity()

    membership = RoomMember.query.filter_by(room_id=room_id, user_id=int(current_user_id)).first()
    if not membership:
        return jsonify({"error": "Δεν είσαι μέλος αυτού του δωματίου"}), 403

    data = request.get_json()
    username = data.get('username')

    user_to_invite = User.query.filter_by(username=username).first()
    if not user_to_invite:
        return jsonify({"error": "Ο χρήστης δεν βρέθηκε"}), 404

    already_member = RoomMember.query.filter_by(room_id=room_id, user_id=user_to_invite.id).first()
    if already_member:
        return jsonify({"error": "Ο χρήστης είναι ήδη μέλος"}), 400

    existing_invite = Invitation.query.filter_by(
        room_id=room_id, invited_user_id=user_to_invite.id, status='pending'
    ).first()
    if existing_invite:
        return jsonify({"error": "Υπάρχει ήδη εκκρεμές αίτημα για αυτόν τον χρήστη"}), 400

    invitation = Invitation(
        room_id=room_id,
        invited_user_id=user_to_invite.id,
        invited_by_id=int(current_user_id),
    )
    db.session.add(invitation)
    db.session.commit()

    inviter = User.query.get(int(current_user_id))
    room = Room.query.get(room_id)

    socketio.emit('new_invitation', {
        'id': invitation.id,
        'room_id': room_id,
        'room_name': room.name,
        'invited_by': inviter.username,
        'created_at': invitation.created_at.isoformat()
    }, to=f"user_{user_to_invite.id}")

    return jsonify({"message": f"Το αίτημα στάλθηκε στον {username}"}), 201


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