const socket = io();

let username = '';
let room = '';
let roomCode = '';
let typingTimeout;

function switchTab(tab) {
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
    
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    document.getElementById(tab + '-tab').classList.add('active');
}

function createRoom() {
    username = document.getElementById('username-input').value.trim();
    const roomName = document.getElementById('room-input').value.trim() || 'general';
    
    if (!username) {
        alert('Please enter a username');
        return;
    }
    
    socket.emit('create_room', { username, room_name: roomName });
}

function joinWithCode() {
    username = document.getElementById('username-input').value.trim();
    const code = document.getElementById('code-input').value.trim().toUpperCase();
    
    if (!username) {
        alert('Please enter a username');
        return;
    }
    
    if (!code) {
        alert('Please enter a room code');
        return;
    }
    
    socket.emit('join_with_code', { username, code });
}

function sendMessage() {
    const input = document.getElementById('message-input');
    const message = input.value.trim();
    
    if (message) {
        socket.emit('send_message', { message });
        input.value = '';
    }
}

function copyCode() {
    const code = document.getElementById('room-code').textContent;
    navigator.clipboard.writeText(code).then(() => {
        const btn = document.querySelector('.copy-btn');
        btn.textContent = '✓';
        setTimeout(() => {
            btn.textContent = '📋';
        }, 2000);
    });
}

// Socket event listeners
socket.on('connect', () => {
    console.log('Connected to server');
});

socket.on('room_created', (data) => {
    room = data.room_name;
    roomCode = data.code;
    showChatScreen(data.room_name, data.code);
    loadMessages(data.messages);
});

socket.on('room_joined', (data) => {
    room = data.room_name;
    roomCode = data.code;
    showChatScreen(data.room_name, data.code);
    loadMessages(data.messages);
});

socket.on('join_error', (data) => {
    alert('Error: ' + data.message);
});

socket.on('receive_message', (data) => {
    addMessage(data.username, data.message, data.timestamp, data.file);
    scrollToBottom();
});

socket.on('user_joined', (data) => {
    addSystemMessage(`${data.username} joined the chat`);
    scrollToBottom();
});

socket.on('user_left', (data) => {
    addSystemMessage(`${data.username} left the chat`);
    scrollToBottom();
});

socket.on('update_users', (data) => {
    const usersList = document.getElementById('users-list');
    usersList.innerHTML = '';
    
    data.users.forEach(user => {
        const li = document.createElement('li');
        li.textContent = user;
        usersList.appendChild(li);
    });
});

socket.on('user_typing', (data) => {
    const indicator = document.getElementById('typing-indicator');
    indicator.textContent = `${data.username} is typing...`;
    
    clearTimeout(typingTimeout);
    typingTimeout = setTimeout(() => {
        indicator.textContent = '';
    }, 2000);
});

socket.on('upload_error', (data) => {
    hideUploadProgress();
    alert('Upload failed: ' + data.message);
});

// Helper functions
function showChatScreen(roomName, code) {
    document.getElementById('login-screen').style.display = 'none';
    document.getElementById('chat-screen').style.display = 'block';
    document.getElementById('room-name').textContent = roomName;
    document.getElementById('room-code').textContent = code;
    document.getElementById('message-input').focus();
}

function loadMessages(messages) {
    const messagesDiv = document.getElementById('messages');
    messagesDiv.innerHTML = '';
    
    messages.forEach(msg => {
        addMessage(msg.username, msg.message, msg.timestamp, msg.file);
    });
    
    scrollToBottom();
}

function addMessage(username, message, timestamp, file = null) {
    const messagesDiv = document.getElementById('messages');
    
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message';
    
    const headerDiv = document.createElement('div');
    headerDiv.className = 'message-header';
    
    const usernameSpan = document.createElement('span');
    usernameSpan.className = 'message-username';
    usernameSpan.textContent = username;
    
    const timestampSpan = document.createElement('span');
    timestampSpan.className = 'message-timestamp';
    timestampSpan.textContent = timestamp;
    
    headerDiv.appendChild(usernameSpan);
    headerDiv.appendChild(timestampSpan);
    messageDiv.appendChild(headerDiv);
    
    if (message) {
        const textDiv = document.createElement('div');
        textDiv.className = 'message-text';
        textDiv.textContent = message;
        messageDiv.appendChild(textDiv);
    }
    
    if (file) {
        const fileDiv = document.createElement('div');
        fileDiv.className = 'message-file';
        
        if (file.type === 'image') {
            fileDiv.innerHTML = `
                <div class="media-preview">
                    <img src="${file.url}" alt="${file.filename}" onclick="openMedia('${file.url}')">
                </div>
            `;
        } else if (file.type === 'video') {
            fileDiv.innerHTML = `
                <div class="media-preview">
                    <video controls>
                        <source src="${file.url}" type="video/mp4">
                        Your browser does not support the video tag.
                    </video>
                </div>
            `;
        } else {
            const icon = getFileIcon(file.filename);
            fileDiv.innerHTML = `
                <div class="file-preview" onclick="window.open('${file.url}', '_blank')">
                    <div class="file-icon">${icon}</div>
                    <div class="file-info">
                        <div class="file-name">${file.filename}</div>
                        <div class="file-size">${formatFileSize(file.size)}</div>
                    </div>
                </div>
            `;
        }
        
        messageDiv.appendChild(fileDiv);
    }
    
    messagesDiv.appendChild(messageDiv);
}

function addSystemMessage(message) {
    const messagesDiv = document.getElementById('messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'system-message';
    messageDiv.textContent = message;
    messagesDiv.appendChild(messageDiv);
}

function scrollToBottom() {
    const messagesDiv = document.getElementById('messages');
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function getFileIcon(filename) {
    const ext = filename.split('.').pop().toLowerCase();
    const icons = {
        'pdf': '📄',
        'doc': '📝',
        'docx': '📝',
        'txt': '📄',
        'zip': '📦',
        'rar': '📦'
    };
    return icons[ext] || '📎';
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function openMedia(url) {
    window.open(url, '_blank');
}

function showUploadProgress() {
    document.getElementById('upload-progress').style.display = 'block';
}

function hideUploadProgress() {
    document.getElementById('upload-progress').style.display = 'none';
}

// Event listeners
document.getElementById('message-input').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        sendMessage();
    } else {
        socket.emit('typing');
    }
});

document.getElementById('file-input').addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        if (file.size > 16 * 1024 * 1024) {
            alert('File size must be less than 16MB');
            return;
        }
        
        showUploadProgress();
        
        const reader = new FileReader();
        reader.onload = function(event) {
            socket.emit('upload_file', {
                filename: file.name,
                file_data: event.target.result
            });
            hideUploadProgress();
        };
        
        reader.onerror = function() {
            hideUploadProgress();
            alert('Error reading file');
        };
        
        reader.readAsDataURL(file);
    }
    
    e.target.value = '';
});

document.getElementById('username-input').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        const activeTab = document.querySelector('.tab-content.active');
        if (activeTab.id === 'create-tab') {
            createRoom();
        } else {
            joinWithCode();
        }
    }
});

document.getElementById('room-input').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        createRoom();
    }
});

document.getElementById('code-input').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        joinWithCode();
    }
});
