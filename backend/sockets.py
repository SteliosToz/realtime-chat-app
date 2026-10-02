from flask import request
from flask_jwt_extended import decode_token
from flask_socketio import join_room, emit
from extensions import socketio, db
from models import RoomMember, Message, User

print("🔵 Το sockets.py φορτώθηκε!")

connected_users = {}


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


@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    user_id = connected_users.pop(sid, None)
    if user_id:
        print(f"Ο χρήστης {user_id} αποσυνδέθηκε (sid={sid})", flush=True)


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