from flask import Flask, render_template_string, request
from flask_socketio import SocketIO, emit, join_room
import random
import string
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback-secret-key')

# Production-ready SocketIO configuration
socketio = SocketIO(
    app, 
    cors_allowed_origins="*",
    async_mode='threading',
    logger=True,
    engineio_logger=True,
    ping_timeout=60,
    ping_interval=25
)

users = {}
rooms = {}
codes = {}

def generate_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

@app.route('/')
def index():
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>Chat App</title>
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    <style>
        body { font-family: Arial; background: linear-gradient(135deg, #ffc0cb, #ffb6c1); margin: 0; padding: 20px; }
        .container { max-width: 400px; margin: 50px auto; background: white; padding: 30px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
        h1 { text-align: center; color: #ff69b4; margin-bottom: 30px; }
        input { width: 100%; padding: 12px; margin: 10px 0; border: 2px solid #ffb6c1; border-radius: 8px; font-size: 16px; }
        button { width: 100%; padding: 15px; background: linear-gradient(135deg, #ffb6c1, #ff69b4); color: white; border: none; border-radius: 8px; font-size: 16px; cursor: pointer; margin: 10px 0; }
        button:hover { transform: translateY(-2px); }
        .tabs { display: flex; gap: 10px; margin: 20px 0; }
        .tab { flex: 1; padding: 10px; background: #ffe4e9; color: #ff69b4; border: 2px solid #ffb6c1; border-radius: 8px; cursor: pointer; text-align: center; }
        .tab.active { background: #ffb6c1; color: white; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        #chat { display: none; }
        .chat-container { display: flex; height: 80vh; }
        .sidebar { width: 200px; background: #ffe4e9; padding: 20px; }
        .messages { flex: 1; padding: 20px; background: #fff5f7; overflow-y: auto; }
        .input-area { padding: 20px; background: white; }
        .message { margin: 10px 0; padding: 10px; background: white; border-radius: 10px; }
        .username { font-weight: bold; color: #ff69b4; }
        .code-display { background: white; padding: 15px; border-radius: 10px; margin: 15px 0; text-align: center; }
        .code { font-size: 24px; font-weight: bold; color: #ff69b4; letter-spacing: 3px; }
    </style>
</head>
<body>
    <div id="login" class="container">
        <h1>💬 Chat App</h1>
        <input type="text" id="username" placeholder="Enter your username" maxlength="20">
        
        <div class="tabs">
            <div class="tab active" onclick="switchTab('create')">Create Room</div>
            <div class="tab" onclick="switchTab('join')">Join Room</div>
        </div>
        
        <div id="create-tab" class="tab-content active">
            <input type="text" id="roomname" placeholder="Room name (optional)">
            <button onclick="createRoom()">Create & Join</button>
        </div>
        
        <div id="join-tab" class="tab-content">
            <input type="text" id="code" placeholder="Enter 6-digit code" maxlength="6">
            <button onclick="joinRoom()">Join Room</button>
        </div>
    </div>
    
    <div id="chat">
        <div class="chat-container">
            <div class="sidebar">
                <h3 id="room-title">Room</h3>
                <div class="code-display">
                    <div>Room Code:</div>
                    <div class="code" id="room-code">------</div>
                    <button onclick="copyCode()">📋 Copy</button>
                </div>
                <h4>Online Users:</h4>
                <div id="users"></div>
            </div>
            <div style="flex: 1;">
                <div class="messages" id="messages"></div>
                <div class="input-area">
                    <input type="text" id="message" placeholder="Type a message..." onkeypress="if(event.key==='Enter') sendMessage()">
                    <button onclick="sendMessage()">Send</button>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // Production-ready Socket.IO connection
        const socket = io({
            transports: ['polling', 'websocket'],
            upgrade: true,
            timeout: 20000,
            forceNew: false,
            reconnection: true,
            reconnectionDelay: 1000,
            reconnectionAttempts: 5,
            maxReconnectionAttempts: 5
        });
        
        let username = '';
        let currentRoom = '';
        let currentCode = '';
        
        // Connection status handling
        socket.on('connect', () => {
            console.log('Connected to server');
        });
        
        socket.on('disconnect', () => {
            console.log('Disconnected from server');
        });
        
        socket.on('connect_error', (error) => {
            console.log('Connection error:', error);
            setTimeout(() => {
                if (!socket.connected) {
                    alert('Connection failed. Please refresh and try again.');
                }
            }, 3000);
        });
        
        function switchTab(tab) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
            event.target.classList.add('active');
            document.getElementById(tab + '-tab').classList.add('active');
        }
        
        function createRoom() {
            username = document.getElementById('username').value.trim();
            const roomname = document.getElementById('roomname').value.trim() || 'general';
            if (!username) { alert('Enter username'); return; }
            
            // Disable button during request
            const btn = event.target;
            btn.disabled = true;
            btn.textContent = 'Creating...';
            
            socket.emit('create_room', {username, roomname});
            
            // Reset button after timeout
            setTimeout(() => {
                btn.disabled = false;
                btn.textContent = 'Create & Join';
            }, 10000);
        }
        
        function joinRoom() {
            username = document.getElementById('username').value.trim();
            const code = document.getElementById('code').value.trim().toUpperCase();
            if (!username || !code) { alert('Enter username and code'); return; }
            
            // Disable button during request
            const btn = event.target;
            btn.disabled = true;
            btn.textContent = 'Joining...';
            
            socket.emit('join_room', {username, code});
            
            // Reset button after timeout
            setTimeout(() => {
                btn.disabled = false;
                btn.textContent = 'Join Room';
            }, 10000);
        }
        
        function sendMessage() {
            const msg = document.getElementById('message').value.trim();
            if (msg) {
                socket.emit('send_message', {message: msg});
                document.getElementById('message').value = '';
            }
        }
        
        function copyCode() {
            if (navigator.clipboard) {
                navigator.clipboard.writeText(currentCode).then(() => {
                    alert('Code copied!');
                });
            } else {
                // Fallback for older browsers
                const textArea = document.createElement("textarea");
                textArea.value = currentCode;
                document.body.appendChild(textArea);
                textArea.select();
                document.execCommand('copy');
                document.body.removeChild(textArea);
                alert('Code copied!');
            }
        }
        
        socket.on('room_created', (data) => {
            currentRoom = data.room;
            currentCode = data.code;
            showChat(data.room, data.code);
            // Reset button
            document.querySelectorAll('button').forEach(btn => {
                btn.disabled = false;
                if (btn.textContent === 'Creating...') btn.textContent = 'Create & Join';
            });
        });
        
        socket.on('room_joined', (data) => {
            currentRoom = data.room;
            currentCode = data.code;
            showChat(data.room, data.code);
            // Reset button
            document.querySelectorAll('button').forEach(btn => {
                btn.disabled = false;
                if (btn.textContent === 'Joining...') btn.textContent = 'Join Room';
            });
        });
        
        socket.on('error', (data) => {
            alert(data.message);
            // Reset buttons
            document.querySelectorAll('button').forEach(btn => {
                btn.disabled = false;
                if (btn.textContent === 'Creating...') btn.textContent = 'Create & Join';
                if (btn.textContent === 'Joining...') btn.textContent = 'Join Room';
            });
        });
        
        socket.on('message', (data) => {
            addMessage(data.username, data.message);
        });
        
        socket.on('users_update', (data) => {
            document.getElementById('users').innerHTML = data.users.map(u => '<div>' + u + '</div>').join('');
        });
        
        function showChat(room, code) {
            document.getElementById('login').style.display = 'none';
            document.getElementById('chat').style.display = 'block';
            document.getElementById('room-title').textContent = room;
            document.getElementById('room-code').textContent = code;
        }
        
        function addMessage(user, msg) {
            const div = document.createElement('div');
            div.className = 'message';
            div.innerHTML = '<span class="username">' + user + ':</span> ' + msg;
            document.getElementById('messages').appendChild(div);
            document.getElementById('messages').scrollTop = document.getElementById('messages').scrollHeight;
        }
    </script>
</body>
</html>
    ''')

@socketio.on('create_room')
def create_room(data):
    try:
        username = data['username']
        roomname = data['roomname']
        code = generate_code()
        
        users[request.sid] = {'username': username, 'room': roomname}
        
        if roomname not in rooms:
            rooms[roomname] = {'users': [], 'messages': []}
        
        rooms[roomname]['users'].append(username)
        codes[code] = roomname
        
        join_room(roomname)
        emit('room_created', {'room': roomname, 'code': code})
        emit('users_update', {'users': rooms[roomname]['users']}, room=roomname)
        
        print(f"Room created: {roomname} with code {code} by {username}")
        
    except Exception as e:
        print(f"Error creating room: {e}")
        emit('error', {'message': 'Failed to create room'})

@socketio.on('join_room')
def join_room_with_code(data):
    try:
        username = data['username']
        code = data['code']
        
        if code not in codes:
            emit('error', {'message': 'Invalid room code'})
            return
        
        roomname = codes[code]
        users[request.sid] = {'username': username, 'room': roomname}
        
        if roomname not in rooms:
            rooms[roomname] = {'users': [], 'messages': []}
        
        rooms[roomname]['users'].append(username)
        
        join_room(roomname)
        emit('room_joined', {'room': roomname, 'code': code})
        emit('users_update', {'users': rooms[roomname]['users']}, room=roomname)
        
        print(f"User {username} joined room {roomname} with code {code}")
        
    except Exception as e:
        print(f"Error joining room: {e}")
        emit('error', {'message': 'Failed to join room'})

@socketio.on('send_message')
def send_message(data):
    try:
        if request.sid in users:
            username = users[request.sid]['username']
            room = users[request.sid]['room']
            message = data['message']
            
            emit('message', {'username': username, 'message': message}, room=room)
            print(f"Message from {username} in {room}: {message}")
            
    except Exception as e:
        print(f"Error sending message: {e}")

@socketio.on('disconnect')
def handle_disconnect():
    try:
        if request.sid in users:
            username = users[request.sid]['username']
            room = users[request.sid]['room']
            
            if room in rooms and username in rooms[room]['users']:
                rooms[room]['users'].remove(username)
                emit('users_update', {'users': rooms[room]['users']}, room=room)
            
            del users[request.sid]
            print(f"User {username} disconnected from {room}")
            
    except Exception as e:
        print(f"Error handling disconnect: {e}")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, debug=False, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)