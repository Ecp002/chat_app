from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
socketio = SocketIO(app, cors_allowed_origins="*")

# Store active users and rooms
users = {}
rooms = {'general': {'users': [], 'messages': []}}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    print(f'Client connected: {request.sid}')

@socketio.on('disconnect')
def handle_disconnect():
    if request.sid in users:
        username = users[request.sid]['username']
        room = users[request.sid]['room']
        
        # Remove user from room
        if room in rooms and username in rooms[room]['users']:
            rooms[room]['users'].remove(username)
        
        # Notify others
        emit('user_left', {
            'username': username,
            'timestamp': datetime.now().strftime('%H:%M')
        }, room=room)
        
        # Update online users
        emit('update_users', {'users': rooms[room]['users']}, room=room)
        
        del users[request.sid]
        print(f'{username} disconnected')

@socketio.on('join')
def handle_join(data):
    username = data['username']
    room = data.get('room', 'general')
    
    # Create room if it doesn't exist
    if room not in rooms:
        rooms[room] = {'users': [], 'messages': []}
    
    # Store user info
    users[request.sid] = {'username': username, 'room': room}
    
    # Join the room
    join_room(room)
    rooms[room]['users'].append(username)
    
    # Send message history
    emit('message_history', {'messages': rooms[room]['messages']})
    
    # Notify others
    emit('user_joined', {
        'username': username,
        'timestamp': datetime.now().strftime('%H:%M')
    }, room=room)
    
    # Update online users
    emit('update_users', {'users': rooms[room]['users']}, room=room)
    
    print(f'{username} joined room: {room}')

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
    
    # Store message in room history
    rooms[room]['messages'].append(message_data)
    
    # Keep only last 100 messages
    if len(rooms[room]['messages']) > 100:
        rooms[room]['messages'] = rooms[room]['messages'][-100:]
    
    # Broadcast to room
    emit('receive_message', message_data, room=room)

@socketio.on('typing')
def handle_typing(data):
    if request.sid not in users:
        return
    
    username = users[request.sid]['username']
    room = users[request.sid]['room']
    
    emit('user_typing', {'username': username}, room=room, include_self=False)

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
