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
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chat App</title>
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #ffc0cb 0%, #ffb6c1 100%);
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }

        #login {
            width: 100%;
            height: 100%;
            display: flex;
            justify-content: center;
            align-items: center;
        }

        .container {
            background: white;
            padding: 40px;
            border-radius: 15px;
            box-shadow: 0 15px 50px rgba(255, 105, 180, 0.3);
            text-align: center;
            min-width: 400px;
            max-width: 450px;
        }

        h1 {
            margin-bottom: 30px;
            color: #ff69b4;
        }

        input {
            width: 100%;
            padding: 12px;
            margin: 10px 0;
            border: 2px solid #ffb6c1;
            border-radius: 8px;
            font-size: 16px;
        }

        input:focus {
            outline: none;
            border-color: #ff69b4;
        }

        .tab-container {
            display: flex;
            gap: 10px;
            margin: 20px 0 15px 0;
        }

        .tab-btn {
            flex: 1;
            padding: 10px;
            background: #ffe4e9;
            color: #ff69b4;
            border: 2px solid #ffb6c1;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
        }

        .tab-btn:hover {
            background: #ffc0cb;
            color: white;
        }

        .tab-btn.active {
            background: #ffb6c1;
            color: white;
            border-color: #ff69b4;
        }

        .tab-content {
            display: none;
            animation: fadeIn 0.3s;
        }

        .tab-content.active {
            display: block;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .primary-btn {
            width: 100%;
            padding: 14px;
            margin-top: 15px;
            background: linear-gradient(135deg, #ffb6c1 0%, #ff69b4 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            box-shadow: 0 4px 15px rgba(255, 105, 180, 0.3);
        }

        .primary-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(255, 105, 180, 0.4);
        }

        .primary-btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }

        #chat {
            display: none;
            width: 100%;
            height: 100vh;
        }

        .chat-container {
            display: flex;
            height: 100vh;
            background: white;
        }

        .sidebar {
            width: 250px;
            background: #ffe4e9;
            color: #333;
            display: flex;
            flex-direction: column;
        }

        .room-info {
            padding: 20px;
            background: #ffc0cb;
            border-bottom: 1px solid #ffb6c1;
        }

        .room-info h2 {
            font-size: 20px;
            margin-bottom: 15px;
        }

        .room-code-display {
            margin-top: 15px;
            padding: 15px;
            background: rgba(255, 255, 255, 0.3);
            border-radius: 10px;
        }

        .code-label {
            font-size: 11px;
            text-transform: uppercase;
            color: #ff69b4;
            font-weight: 600;
            margin-bottom: 8px;
            letter-spacing: 1px;
        }

        .code-box {
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: white;
            padding: 12px 15px;
            border-radius: 8px;
            margin-bottom: 8px;
        }

        .code {
            font-size: 20px;
            font-weight: bold;
            color: #ff69b4;
            letter-spacing: 3px;
            font-family: 'Courier New', monospace;
        }

        .copy-btn {
            background: #ffe4e9;
            border: none;
            padding: 6px 10px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            transition: all 0.2s;
        }

        .copy-btn:hover {
            background: #ffb6c1;
            transform: scale(1.1);
        }

        .code-hint {
            font-size: 11px;
            color: #333;
            font-style: italic;
        }

        .online-users {
            padding: 20px;
            flex: 1;
            overflow-y: auto;
        }

        .online-users h3 {
            font-size: 14px;
            margin-bottom: 15px;
            color: #ff69b4;
            text-transform: uppercase;
        }

        #users {
            list-style: none;
        }

        #users div {
            padding: 8px 0;
            color: #333;
            display: flex;
            align-items: center;
        }

        #users div:before {
            content: '●';
            color: #ff69b4;
            margin-right: 8px;
        }

        .chat-main {
            flex: 1;
            display: flex;
            flex-direction: column;
        }

        .messages {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            background: #fff5f7;
        }

        .message {
            margin-bottom: 15px;
            animation: fadeIn 0.3s;
        }

        .message-header {
            display: flex;
            align-items: center;
            margin-bottom: 5px;
        }

        .username {
            font-weight: bold;
            color: #ff69b4;
            margin-right: 10px;
        }

        .message-timestamp {
            font-size: 12px;
            color: #95a5a6;
        }

        .message-text {
            background: white;
            padding: 10px 15px;
            border-radius: 10px;
            display: inline-block;
            max-width: 70%;
            word-wrap: break-word;
        }

        .system-message {
            text-align: center;
            color: #95a5a6;
            font-size: 14px;
            font-style: italic;
            margin: 10px 0;
        }

        #typing-indicator {
            padding: 0 20px;
            height: 20px;
            font-size: 12px;
            color: #95a5a6;
            font-style: italic;
        }

        .input-area {
            padding: 20px;
            background: white;
            border-top: 1px solid #e0e0e0;
        }

        .input-container {
            display: flex;
            align-items: center;
            background: #f8f9fa;
            border-radius: 25px;
            padding: 8px;
            border: 2px solid #e0e0e0;
            transition: border-color 0.3s;
        }

        .input-container:focus-within {
            border-color: #ffb6c1;
        }

        #message {
            flex: 1;
            padding: 12px 16px;
            border: none;
            background: transparent;
            font-size: 14px;
            outline: none;
        }

        .input-actions {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .send-btn {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, #ffb6c1 0%, #ff69b4 100%);
            color: white;
            border: none;
            border-radius: 50%;
            cursor: pointer;
            transition: all 0.3s;
        }

        .send-btn:hover {
            transform: scale(1.1);
            box-shadow: 0 4px 15px rgba(255, 105, 180, 0.4);
        }

        @media (max-width: 768px) {
            .chat-container {
                flex-direction: column;
            }
            
            .sidebar {
                width: 100%;
                height: auto;
                max-height: 200px;
                order: 2;
            }
            
            .chat-main {
                order: 1;
                height: calc(100vh - 200px);
            }
            
            .container {
                min-width: 300px;
                margin: 20px;
                padding: 30px;
            }
        }
    </style>
</head>
<body>
    <div id="login">
        <div class="container">
            <h1>💬 Chat App</h1>
            <input type="text" id="username" placeholder="Enter your username" maxlength="20">
            
            <div class="tab-container">
                <div class="tab-btn active" onclick="switchTab('create')">Create Room</div>
                <div class="tab-btn" onclick="switchTab('join')">Join with Code</div>
            </div>

            <div id="create-tab" class="tab-content active">
                <input type="text" id="roomname" placeholder="Room name (optional)" maxlength="20">
                <button onclick="createRoom()" class="primary-btn">Create & Join</button>
            </div>

            <div id="join-tab" class="tab-content">
                <input type="text" id="code" placeholder="Enter 6-digit code" maxlength="6">
                <button onclick="joinRoom()" class="primary-btn">Join Room</button>
            </div>
        </div>
    </div>
    
    <div id="chat">
        <div class="chat-container">
            <div class="sidebar">
                <div class="room-info">
                    <h2 id="room-title">Room</h2>
                    <div class="room-code-display">
                        <p class="code-label">Room Code</p>
                        <div class="code-box">
                            <span class="code" id="room-code">------</span>
                            <button onclick="copyCode()" class="copy-btn" title="Copy code">📋</button>
                        </div>
                        <p class="code-hint">Share this code with friends!</p>
                    </div>
                </div>
                <div class="online-users">
                    <h3>Online Users</h3>
                    <div id="users"></div>
                </div>
            </div>

            <div class="chat-main">
                <div class="messages" id="messages"></div>
                <div id="typing-indicator"></div>
                <div class="input-area">
                    <div class="input-container">
                        <input type="text" id="message" placeholder="Type a message..." autocomplete="off" onkeypress="if(event.key==='Enter') sendMessage()">
                        <div class="input-actions">
                            <button onclick="sendMessage()" class="send-btn">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                                    <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
                                </svg>
                            </button>
                        </div>
                    </div>
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
            addMessage(data.username, data.message, data.timestamp);
        });
        
        socket.on('user_joined', (data) => {
            addSystemMessage(`${data.username} joined the chat`);
        });
        
        socket.on('user_left', (data) => {
            addSystemMessage(`${data.username} left the chat`);
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
        
        function addMessage(user, msg, timestamp) {
            const messagesDiv = document.getElementById('messages');
            
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message';
            
            const headerDiv = document.createElement('div');
            headerDiv.className = 'message-header';
            
            const usernameSpan = document.createElement('span');
            usernameSpan.className = 'username';
            usernameSpan.textContent = user;
            
            const timestampSpan = document.createElement('span');
            timestampSpan.className = 'message-timestamp';
            timestampSpan.textContent = timestamp || new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
            
            headerDiv.appendChild(usernameSpan);
            headerDiv.appendChild(timestampSpan);
            
            const textDiv = document.createElement('div');
            textDiv.className = 'message-text';
            textDiv.textContent = msg;
            
            messageDiv.appendChild(headerDiv);
            messageDiv.appendChild(textDiv);
            messagesDiv.appendChild(messageDiv);
            
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
        
        function addSystemMessage(msg) {
            const messagesDiv = document.getElementById('messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = 'system-message';
            messageDiv.textContent = msg;
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
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