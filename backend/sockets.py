from flask import request
from flask_jwt_extended import decode_token
from extensions import socketio

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
    print(f"Ο χρήστης {user_id} συνδέθηκε (sid={request.sid})", flush=True)