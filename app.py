from flask import Flask, render_template, request, send_from_directory
from flask_socketio import SocketIO, emit, join_room, leave_room
from datetime import datetime
import os
import uuid
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create uploads directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'webm', 'pdf', 'txt', 'doc', 'docx'}

socketio = SocketIO(app, cors_allowed_origins="*", max_http_buffer_size=16 * 1024 * 1024)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_type(filename):
    ext = filename.rsplit('.', 1)[1].lower()
    if ext in ['png', 'jpg', 'jpeg', 'gif']:
        return 'image'
    elif ext in ['mp4', 'webm']:
        return 'video'
    else:
        return 'file'

# Store active users and rooms
users = {}
rooms = {'general': {'users': [], 'messages': []}}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@socketio.on('upload_file')
def handle_file_upload(data):
    if request.sid not in users:
        return
    
    username = users[request.sid]['username']
    room = users[request.sid]['room']
    
    try:
        # Decode base64 file data
        import base64
        file_data = base64.b64decode(data['file_data'].split(',')[1])
        filename = secure_filename(data['filename'])
        
        if not allowed_file(filename):
            emit('upload_error', {'message': 'File type not allowed'})
            return
        
        # Generate unique filename
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        
        # Save file
        with open(file_path, 'wb') as f:
            f.write(file_data)
        
        # Create message data
        timestamp = datetime.now().strftime('%H:%M')
        message_data = {
            'username': username,
            'message': '',
            'timestamp': timestamp,
            'file': {
                'filename': filename,
                'url': f'/uploads/{unique_filename}',
                'type': get_file_type(filename),
                'size': len(file_data)
            }
        }
        
        # Store in room history
        rooms[room]['messages'].append(message_data)
        
        # Keep only last 100 messages
        if len(rooms[room]['messages']) > 100:
            rooms[room]['messages'] = rooms[room]['messages'][-100:]
        
        # Broadcast to room
        emit('receive_message', message_data, room=room)
        
    except Exception as e:
        emit('upload_error', {'message': 'Upload failed'})
        print(f"Upload error: {e}")

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
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, debug=False, host='0.0.0.0', port=port)
