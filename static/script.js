const socket = io();

let username = '';
let room = '';
let roomCode = '';
let typingTimeout;

// Room code mapping (in production, this would be server-side)
const roomCodes = {};

function switchTab(tab) {
    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
    
    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    document.getElementById(tab + '-tab').classList.add('active');
}

function generateRoomCode() {
    return Math.random().toString(36).substring(2, 8).toUpperCase();
}

function createRoom() {
    username = document.getElementById('username-input').value.trim();
    room = document.getElementById('room-input').value.trim() || 'general';
    
    if (!username) {
        alert('Please enter a username');
        return;
    }
    
    // Generate unique room code
    roomCode = generateRoomCode();
    
    // Store mapping
    roomCodes[roomCode] = room;
    
    joinChatRoom(room, roomCode);
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
    
    // In production, validate code with server
    // For now, we'll use the code as the room name
    room = code;
    roomCode = code;
    
    joinChatRoom(room, roomCode);
}

function joinChatRoom(roomName, code) {
    // Hide login, show chat
    document.getElementById('login-screen').style.display = 'none';
    document.getElementById('chat-screen').style.display = 'block';
    document.getElementById('room-name').textContent = roomName;
    document.getElementById('room-code').textContent = code;
    
    // Join the room
    socket.emit('join', { username, room: roomName, code });
    
    // Focus on message input
    document.getElementById('message-input').focus();
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

function sendMessage() {
    const input = document.getElementById('message-input');
    const message = input.value.trim();
    
    if (message) {
        socket.emit('send_message', { message });
        input.value = '';
    }
}

// Socket event listeners
socket.on('message_history', (data) => {
    const messagesDiv = document.getElementById('messages');
    messagesDiv.innerHTML = '';
    
    data.messages.forEach(msg => {
        addMessage(msg.username, msg.message, msg.timestamp, msg.file);
    });
    
    scrollToBottom();
});

socket.on('receive_message', (data) => {
    addMessage(data.username, data.message, data.timestamp, data.file);
    scrollToBottom();
});

socket.on('upload_error', (data) => {
    hideUploadProgress();
    alert('Upload failed: ' + data.message);
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

// Helper functions
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

function updateProgress(percent) {
    document.querySelector('.progress-fill').style.width = percent + '%';
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
    
    // Reset input
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
