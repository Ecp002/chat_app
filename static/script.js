const socket = io({
    transports: ['websocket'],
    upgrade: false,
    timeout: 5000
});

let username = '';
let room = '';
let roomCode = '';
let typingTimeout;

function switchTab(tab) {
    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelector(`[onclick="switchTab('${tab}')"]`).classList.add('active');
    
    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    document.getElementById(tab + '-tab').classList.add('active');
}

function createRoom() {
    username = document.getElementById('username-input').value.trim();
    const roomName = document.getElementById('room-input').value.trim() || 'general';
    
    if (!username) {
        alert('Please enter a username');
        document.getElementById('username-input').focus();
        return;
    }
    
    if (username.length < 2) {
        alert('Username must be at least 2 characters');
        document.getElementById('username-input').focus();
        return;
    }
    
    // Disable button to prevent double-click
    const btn = document.querySelector('#create-tab .primary-btn');
    btn.disabled = true;
    btn.textContent = 'Creating...';
    
    // Set timeout to reset button if no response
    setTimeout(() => {
        if (btn.textContent === 'Creating...') {
            resetButtons();
            alert('Connection timeout. Please try again.');
        }
    }, 10000);
    
    socket.emit('create_room', { username, room_name: roomName });
}

function joinWithCode() {
    username = document.getElementById('username-input').value.trim();
    const code = document.getElementById('code-input').value.trim().toUpperCase();
    
    if (!username) {
        alert('Please enter a username');
        document.getElementById('username-input').focus();
        return;
    }
    
    if (username.length < 2) {
        alert('Username must be at least 2 characters');
        document.getElementById('username-input').focus();
        return;
    }
    
    if (!code) {
        alert('Please enter a room code');
        document.getElementById('code-input').focus();
        return;
    }
    
    if (code.length !== 6) {
        alert('Room code must be 6 characters');
        document.getElementById('code-input').focus();
        return;
    }
    
    // Disable button to prevent double-click
    const btn = document.querySelector('#join-tab .primary-btn');
    btn.disabled = true;
    btn.textContent = 'Joining...';
    
    // Set timeout to reset button if no response
    setTimeout(() => {
        if (btn.textContent === 'Joining...') {
            resetButtons();
            alert('Connection timeout. Please try again.');
        }
    }, 10000);
    
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
    
    if (navigator.clipboard) {
        navigator.clipboard.writeText(code).then(() => {
            const btn = document.querySelector('.copy-btn');
            btn.textContent = '✓';
            setTimeout(() => {
                btn.textContent = '📋';
            }, 2000);
        }).catch(() => {
            // Fallback for older browsers
            fallbackCopyTextToClipboard(code);
        });
    } else {
        fallbackCopyTextToClipboard(code);
    }
}

function fallbackCopyTextToClipboard(text) {
    const textArea = document.createElement("textarea");
    textArea.value = text;
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    try {
        document.execCommand('copy');
        const btn = document.querySelector('.copy-btn');
        btn.textContent = '✓';
        setTimeout(() => {
            btn.textContent = '📋';
        }, 2000);
    } catch (err) {
        alert('Copy failed. Code: ' + text);
    }
    
    document.body.removeChild(textArea);
}

// Socket event listeners
socket.on('connect', () => {
    console.log('Connected to server');
    // Test connection by emitting a simple event
    socket.emit('test_connection');
});

socket.on('connection_confirmed', () => {
    console.log('Server connection confirmed');
});

socket.on('disconnect', () => {
    console.log('Disconnected from server');
});

socket.on('connect_error', () => {
    console.log('Connection failed');
});

socket.on('room_created', (data) => {
    room = data.room_name;
    roomCode = data.code;
    showChatScreen(data.room_name, data.code);
    loadMessages(data.messages);
    resetButtons();
});

socket.on('room_joined', (data) => {
    room = data.room_name;
    roomCode = data.code;
    showChatScreen(data.room_name, data.code);
    loadMessages(data.messages);
    resetButtons();
});

socket.on('join_error', (data) => {
    alert('Error: ' + data.message);
    resetButtons();
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

socket.on('file_uploaded', (data) => {
    hideUploadProgress();
    console.log('File uploaded successfully');
});

// Helper functions
function resetButtons() {
    const createBtn = document.querySelector('#create-tab .primary-btn');
    const joinBtn = document.querySelector('#join-tab .primary-btn');
    
    if (createBtn) {
        createBtn.disabled = false;
        createBtn.textContent = 'Create & Join';
    }
    
    if (joinBtn) {
        joinBtn.disabled = false;
        joinBtn.textContent = 'Join Room';
    }
}

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
        
        // Check file type
        const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'video/mp4', 'video/webm', 'application/pdf', 'text/plain', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
        if (!allowedTypes.includes(file.type)) {
            alert('File type not supported. Please use images, videos, PDF, or text files.');
            return;
        }
        
        showUploadProgress();
        
        const reader = new FileReader();
        reader.onload = function(event) {
            socket.emit('upload_file', {
                filename: file.name,
                file_data: event.target.result
            });
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
