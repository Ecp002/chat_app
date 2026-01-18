from flask import Flask, render_template_string, request
from flask_socketio import SocketIO, emit, join_room

app = Flask(__name__)
app.config['SECRET_KEY'] = 'test-key'
socketio = SocketIO(app, cors_allowed_origins="*")

users = {}
rooms = {'general': {'users': [], 'messages': []}}

@app.route('/')
def index():
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>Simple Chat Test</title>
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
</head>
<body>
    <div id="messages" style="height: 300px; overflow-y: scroll; border: 1px solid #ccc; padding: 10px;"></div>
    <input type="text" id="username" placeholder="Username">
    <button onclick="join()">Join</button>
    <br><br>
    <input type="text" id="messageInput" placeholder="Message">
    <button onclick="send()">Send</button>
    
    <script>
        const socket = io();
        let username = '';
        
        socket.on('connect', () => {
            console.log('Connected to server');
        });
        
        function join() {
            username = document.getElementById('username').value;
            if (username) {
                socket.emit('join', {username: username, room: 'general'});
                console.log('Joining with username:', username);
            }
        }
        
        function send() {
            const msg = document.getElementById('messageInput').value;
            if (msg && username) {
                socket.emit('send_message', {message: msg});
                document.getElementById('messageInput').value = '';
                console.log('Sending message:', msg);
            }
        }
        
        socket.on('receive_message', (data) => {
            console.log('Received message:', data);
            const div = document.createElement('div');
            div.textContent = data.username + ': ' + data.message;
            document.getElementById('messages').appendChild(div);
            document.getElementById('messages').scrollTop = document.getElementById('messages').scrollHeight;
        });
        
        socket.on('user_joined', (data) => {
            console.log('User joined:', data);
            const div = document.createElement('div');
            div.style.color = 'green';
            div.textContent = data.username + ' joined the chat';
            document.getElementById('messages').appendChild(div);
        });
        
        // Enter key support
        document.getElementById('messageInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') send();
        });
        
        document.getElementById('username').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') join();
        });
    </script>
</body>
</html>
    ''')

@socketio.on('join')
def handle_join(data):
    username = data['username']
    room = data.get('room', 'general')
    
    users[request.sid] = {'username': username, 'room': room}
    join_room(room)
    
    emit('user_joined', {'username': username}, room=room)
    print(f'{username} joined {room}')

@socketio.on('send_message')
def handle_message(data):
    if request.sid not in users:
        print('User not found in users dict')
        return
    
    username = users[request.sid]['username']
    room = users[request.sid]['room']
    message = data['message']
    
    message_data = {
        'username': username,
        'message': message
    }
    
    emit('receive_message', message_data, room=room)
    print(f'{username}: {message}')

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5001)