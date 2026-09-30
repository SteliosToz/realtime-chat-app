from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import Invitation, RoomMember

invitations_bp = Blueprint('invitations', __name__)


@invitations_bp.route('', methods=['GET'])
@jwt_required()
def get_my_invitations():
    current_user_id = get_jwt_identity()

    invitations = Invitation.query.filter_by(
        invited_user_id=int(current_user_id), status='pending'
    ).all()

    result = [{
        "id": inv.id,
        "room_id": inv.room_id,
        "room_name": inv.room.name,
        "invited_by": inv.invited_by.username,
        "created_at": inv.created_at.isoformat()
    } for inv in invitations]

    return jsonify(result), 200


@invitations_bp.route('/<int:invitation_id>/accept', methods=['POST'])
@jwt_required()
def accept_invitation(invitation_id):
    current_user_id = get_jwt_identity()

    invitation = Invitation.query.get(invitation_id)
    if not invitation or invitation.invited_user_id != int(current_user_id):
        return jsonify({"error": "Το αίτημα δεν βρέθηκε"}), 404

    if invitation.status != 'pending':
        return jsonify({"error": "Το αίτημα δεν είναι πλέον εκκρεμές"}), 400

    invitation.status = 'accepted'
    new_membership = RoomMember(room_id=invitation.room_id, user_id=int(current_user_id))
    db.session.add(new_membership)
    db.session.commit()

    return jsonify({"message": "Έγινες μέλος του δωματίου"}), 200


@invitations_bp.route('/<int:invitation_id>/reject', methods=['POST'])
@jwt_required()
def reject_invitation(invitation_id):
    current_user_id = get_jwt_identity()

    invitation = Invitation.query.get(invitation_id)
    if not invitation or invitation.invited_user_id != int(current_user_id):
        return jsonify({"error": "Το αίτημα δεν βρέθηκε"}), 404

    if invitation.status != 'pending':
        return jsonify({"error": "Το αίτημα δεν είναι πλέον εκκρεμές"}), 400

    invitation.status = 'rejected'
    db.session.commit()

    return jsonify({"message": "Το αίτημα απορρίφθηκε"}), 200