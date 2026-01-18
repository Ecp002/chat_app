from flask import Flask, render_template, request, send_from_directory
from flask_socketio import SocketIO, emit, join_room, leave_room
from datetime import datetime
import os
import uuid
import random
import string
from werkzeug.utils import secure_filename
import base64

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'webm', 'pdf', 'txt', 'doc', 'docx'}

socketio = SocketIO(app, cors_allowed_origins="*")

# Store active users and rooms
users = {}
rooms = {}
room_codes = {}  # Maps codes to room names

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

def generate_room_code():
    import random
    import string
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@socketio.on('connect')
def handle_connect():
    print(f'Client connected: {request.sid}')

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

@socketio.on('create_room')
def handle_create_room(data):
    username = data['username']
    room_name = data.get('room_name', 'general')
    
    # Generate unique code
    code = generate_room_code()
    while code in room_codes:
        code = generate_room_code()
    
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

@socketio.on('join_with_code')
def handle_join_with_code(data):
    username = data['username']
    code = data['code'].upper()
    
    if code not in room_codes:
        emit('join_error', {'message': 'Invalid room code'})
        return
    
    room_name = room_codes[code]
    
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

@socketio.on('upload_file')
def handle_file_upload(data):
    if request.sid not in users:
        return
    
    username = users[request.sid]['username']
    room = users[request.sid]['room']
    
    try:
        file_data = base64.b64decode(data['file_data'].split(',')[1])
        filename = secure_filename(data['filename'])
        
        if not allowed_file(filename):
            emit('upload_error', {'message': 'File type not allowed'})
            return
        
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        
        with open(file_path, 'wb') as f:
            f.write(file_data)
        
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
        
        rooms[room]['messages'].append(message_data)
        
        if len(rooms[room]['messages']) > 100:
            rooms[room]['messages'] = rooms[room]['messages'][-100:]
        
        emit('receive_message', message_data, room=room)
        emit('file_uploaded', {'success': True})
        
    except Exception as e:
        emit('upload_error', {'message': 'Upload failed'})
        print(f"Upload error: {e}")

@socketio.on('typing')
def handle_typing():
    if request.sid not in users:
        return
    
    username = users[request.sid]['username']
    room = users[request.sid]['room']
    
    emit('user_typing', {'username': username}, room=room, include_self=False)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, debug=False, host='0.0.0.0', port=port)
