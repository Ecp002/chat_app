from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'

# Use threading for faster local development
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Store active users and rooms
users = {}
rooms = {}
room_codes = {}

def generate_room_code():
    import random
    import string
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    print(f'Client connected: {request.sid}')

@socketio.on('test_connection')
def handle_test_connection():
    print(f'Connection test from: {request.sid}')
    emit('connection_confirmed')

@socketio.on('create_room')
def handle_create_room(data):
    try:
        username = data['username']
        room_name = data.get('room_name', 'general')
        
        print(f"Creating room for {username}, room: {room_name}")
        
        # Generate unique code
        code = generate_room_code()
        while code in room_codes:
            code = generate_room_code()
        
        print(f"Generated code: {code}")
        
        # Store mapping
        room_codes[code] = room_name
        
        # Create room if doesn't exist
        if room_name not in rooms:
            rooms[room_name] = {'users': [], 'messages': []}
        
        # Store user info
        users[request.sid] = {'username': username, 'room': room_name}
        
        # Join room
        join_room(room_name)
        rooms[room_name]['users'].append(username)
        
        print(f"User {username} joined room {room_name}")
        
        # Send response
        emit('room_created', {
            'room_name': room_name,
            'code': code,
            'messages': rooms[room_name]['messages']
        })
        
        # Notify others
        emit('user_joined', {
            'username': username,
            'timestamp': datetime.now().strftime('%H:%M')
        }, room=room_name)
        
        emit('update_users', {'users': rooms[room_name]['users']}, room=room_name)
        print(f'{username} created room {room_name} with code {code}')
        
    except Exception as e:
        print(f"Error creating room: {e}")
        emit('join_error', {'message': 'Failed to create room'})

@socketio.on('join_with_code')
def handle_join_with_code(data):
    try:
        username = data['username']
        code = data['code'].upper()
        
        print(f"User {username} trying to join with code {code}")
        
        if code not in room_codes:
            print(f"Invalid code: {code}")
            emit('join_error', {'message': 'Invalid room code'})
            return
        
        room_name = room_codes[code]
        print(f"Code {code} maps to room {room_name}")
        
        # Create room if doesn't exist
        if room_name not in rooms:
            rooms[room_name] = {'users': [], 'messages': []}
        
        # Store user info
        users[request.sid] = {'username': username, 'room': room_name}
        
        # Join room
        join_room(room_name)
        rooms[room_name]['users'].append(username)
        
        # Send response
        emit('room_joined', {
            'room_name': room_name,
            'code': code,
            'messages': rooms[room_name]['messages']
        })
        
        # Notify others
        emit('user_joined', {
            'username': username,
            'timestamp': datetime.now().strftime('%H:%M')
        }, room=room_name)
        
        emit('update_users', {'users': rooms[room_name]['users']}, room=room_name)
        print(f'{username} joined room {room_name} with code {code}')
        
    except Exception as e:
        print(f"Error joining room: {e}")
        emit('join_error', {'message': 'Failed to join room'})

@socketio.on('send_message')
def handle_message(data):
    if request.sid not in users:
        return
    
    username = users[request.sid]['username']
    room = users[request.sid]['room']
    message = data['message']
    timestamp = datetime.now().strftime('%H:%M')
    
    message_data = {
        'username': username,
        'message': message,
        'timestamp': timestamp
    }
    
    # Store message
    rooms[room]['messages'].append(message_data)
    
    # Keep only last 100 messages
    if len(rooms[room]['messages']) > 100:
        rooms[room]['messages'] = rooms[room]['messages'][-100:]
    
    # Broadcast to room
    emit('receive_message', message_data, room=room)
    print(f'{username} in {room}: {message}')

@socketio.on('disconnect')
def handle_disconnect():
    print(f'Client disconnected: {request.sid}')
    if request.sid in users:
        username = users[request.sid]['username']
        room = users[request.sid]['room']
        
        if room in rooms and username in rooms[room]['users']:
            rooms[room]['users'].remove(username)
        
        emit('user_left', {
            'username': username,
            'timestamp': datetime.now().strftime('%H:%M')
        }, room=room)
        
        emit('update_users', {'users': rooms[room]['users']}, room=room)
        del users[request.sid]

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting server on port {port}")
    socketio.run(app, debug=True, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)