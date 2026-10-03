from flask import request
from flask_jwt_extended import decode_token
from flask_socketio import join_room, emit
from extensions import socketio, db
from models import RoomMember, Message, User

print("🔵 Το sockets.py φορτώθηκε!")

connected_users = {}

def get_related_user_ids(user_id):
    room_ids = [m.room_id for m in RoomMember.query.filter_by(user_id=int(user_id)).all()]

    if not room_ids:
        return []

    memberships = RoomMember.query.filter(RoomMember.room_id.in_(room_ids)).all()
    related_ids = {m.user_id for m in memberships if m.user_id != int(user_id)}

    return list(related_ids)



@socketio.on('connect')
def handle_connect(auth):
    print("🟢 CONNECT EVENT ΠΥΡΟΔΟΤΗΘΗΚΕ! auth =", auth, flush=True)

    token = None
    if auth and 'token' in auth:
        token = auth['token']

    if not token:
        print("Απόρριψη σύνδεσης: δεν στάλθηκε token", flush=True)
        return False

    try:
        decoded = decode_token(token)
        user_id = decoded['sub']
    except Exception as e:
        print("Απόρριψη σύνδεσης: άκυρο token —", e, flush=True)
        return False

    connected_users[request.sid] = user_id
    join_room(f"user_{user_id}")
    print(f"Ο χρήστης {user_id} συνδέθηκε (sid={request.sid})", flush=True)

    related_ids = get_related_user_ids(user_id)
    for related_id in related_ids:
        socketio.emit('user_status_changed', {
            'user_id': int(user_id),
            'status': 'online'
        }, to=f"user_{related_id}")

    online_related_ids = [
        rid for rid in related_ids
        if str(rid) in [str(v) for v in connected_users.values()]
    ]
    emit('online_users_snapshot', {'online_user_ids': online_related_ids})


@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    user_id = connected_users.pop(sid, None)
    if user_id:
        print(f"Ο χρήστης {user_id} αποσυνδέθηκε (sid={sid})", flush=True)
        related_ids = get_related_user_ids(user_id)
        for related_id in related_ids:
            socketio.emit('user_status_changed', {
                'user_id': int(user_id),
                'status': 'offline'
            }, to=f"user_{related_id}")


@socketio.on('join_room')
def handle_join_room(data):
    sid = request.sid
    user_id = connected_users.get(sid)

    if not user_id:
        emit('error', {'message': 'Δεν είσαι συνδεδεμένος'})
        return

    room_id = data.get('room_id')

    membership = RoomMember.query.filter_by(room_id=room_id, user_id=int(user_id)).first()
    if not membership:
        emit('error', {'message': 'Δεν είσαι μέλος αυτού του δωματίου'})
        return

    join_room(str(room_id))
    print(f"Ο χρήστης {user_id} μπήκε στο room {room_id}", flush=True)

    emit('joined_room', {'room_id': room_id})


@socketio.on('send_message')
def handle_send_message(data):
    sid = request.sid
    user_id = connected_users.get(sid)

    if not user_id:
        emit('error', {'message': 'Δεν είσαι συνδεδεμένος'})
        return

    room_id = data.get('room_id')
    text = data.get('text')

    if not text:
        emit('error', {'message': 'Το μήνυμα είναι άδειο'})
        return

    membership = RoomMember.query.filter_by(room_id=room_id, user_id=int(user_id)).first()
    if not membership:
        emit('error', {'message': 'Δεν είσαι μέλος αυτού του δωματίου'})
        return

    new_message = Message(room_id=room_id, user_id=int(user_id), text=text)
    db.session.add(new_message)
    db.session.commit()

    sender = User.query.get(int(user_id))

    emit('new_message', {
        'id': new_message.id,
        'room_id': room_id,
        'user_id': int(user_id),
        'username': sender.username,
        'text': new_message.text,
        'created_at': new_message.created_at.isoformat()
    }, to=str(room_id))

    print(f"Νέο μήνυμα από {sender.username} στο room {room_id}: {text}", flush=True)