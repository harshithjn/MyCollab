# MyCollab - Collaborative Code Editor

A real-time collaborative code editor built with Python FastAPI and WebSockets. Multiple users can edit the same document simultaneously.

## Features

- Real-time collaboration with multiple users
- Syntax highlighting for JavaScript, Python, Java, TypeScript, HTML, CSS, and JSON
- Live cursor tracking
- Built-in chat system
- Document sharing via URL
- Modern dark-themed UI

## Quick Start

### 1. Start the Application

```bash
./start.sh
```

### 2. Access the Application

Open your browser and go to: **http://localhost:8000**

### 3. Create a Document

1. Enter your username
2. Click "Connect" to create a new document
3. Start typing code

## Multi-User Collaboration

### For Users on Same WiFi Network

1. Find your IP address:

   ```bash
   ifconfig | grep "inet " | grep -v 127.0.0.1
   ```

2. Share this URL with others:

   ```
   http://YOUR_IP_ADDRESS:8000
   ```

3. Others can join by opening the shared URL and entering their username

### For Internet Users

1. Install ngrok:

   ```bash
   brew install ngrok
   ```

2. Create a tunnel:

   ```bash
   ngrok http 8000
   ```

3. Share the ngrok URL with others

## How to Collaborate

### Document Sharing

1. Host creates document and clicks "Share" button
2. Host copies the generated URL
3. Host shares URL with collaborators
4. Others open the shared URL and start editing

### Real-time Features

- Multiple users can edit simultaneously
- See real-time typing from all users
- View cursor positions of other users
- Chat with collaborators
- Syntax highlighting for multiple languages

## Test Collaboration

### Quick Test

1. Open http://localhost:8000 in one browser tab
2. Open the same URL in another browser tab
3. Use different usernames in each tab
4. Start typing in both tabs - you'll see real-time updates!

## Troubleshooting

### WebSocket Connection Issues

- Make sure you're using `./start.sh`
- Check that port 8000 is not blocked by firewall
- Try refreshing the browser page

### Network Issues

- Same Network: Use your computer's IP address instead of localhost
- Different Networks: Use ngrok tunnel
- Firewall: Ensure port 8000 is open

### Port Already in Use

```bash
lsof -ti:8000 | xargs kill -9
```

## Project Structure

```
MyCollab/
├── backend/           # FastAPI backend with WebSocket support
├── frontend/          # Monaco Editor frontend
├── docker-compose.yml # Docker setup
├── start.sh          # Start script
└── README.md         # This file
```

## Success!

When working correctly, you should see:

- Backend running on http://localhost:8000
- Frontend accessible in browser
- Multiple users in sidebar
- Real-time collaboration working
- No WebSocket errors in browser console

Happy collaborating!
