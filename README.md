# Modern Chat Application

A real-time chat application built with Flask, Socket.IO, and WebSockets.

## Features ✨

- 🌐 Web-based interface (no terminal needed!)
- 💬 Real-time messaging with WebSockets
- 👥 Multiple chat rooms
- 📊 Online user status
- 📜 Message history (last 100 messages per room)
- ⌨️ Typing indicators
- 🎨 Modern, responsive UI

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the server:
```bash
python app.py
```

3. Open your browser and go to:
```
http://localhost:5000
```

## Usage

1. Enter your username
2. Choose a room (or use default "general")
3. Start chatting!

## Deployment (Step 2️⃣)

### Deploy to Render

1. Create a `render.yaml`:
```yaml
services:
  - type: web
    name: chat-app
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python app.py
```

2. Push to GitHub and connect to Render

### Deploy to Railway

1. Install Railway CLI:
```bash
npm i -g @railway/cli
```

2. Deploy:
```bash
railway login
railway init
railway up
```

### Deploy to AWS (EC2)

1. Launch an EC2 instance
2. SSH into it
3. Install Python and dependencies
4. Run the app with a process manager like `gunicorn`:
```bash
pip install gunicorn
gunicorn --worker-class eventlet -w 1 app:app --bind 0.0.0.0:5000
```

## Next Steps 🚀

- [ ] Add user authentication
- [ ] Persistent message storage (database)
- [ ] Private messaging
- [ ] File sharing
- [ ] Emoji support
- [ ] User profiles with avatars
