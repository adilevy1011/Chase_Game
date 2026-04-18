# Chase Game (Singleplayer + Multiplayer)

A Python-based real-time chase game built with `turtle`, supporting both local singleplayer and online multiplayer using WebSockets (Flask-SocketIO + Socket.IO client).

---

## Features

### Singleplayer Mode
- Built with Python `turtle`
- Player movement with WASD
- Bot AI chasing system

---

### Multiplayer Mode (Real-Time)
- Multiple players connected over the internet
- Real-time movement synchronization
- Server-authoritative player positions
- Smooth interpolation using frequent updates (~16ms loop)
- Works across networks using Cloudflare Tunnel (for testing) or direct hosting

---

## Architecture Overview

### Server (server.py)
- Built with Flask + Flask-SocketIO
- Maintains **authoritative game state**
- Handles:
  - Player connections (`connect`)
  - Player input (`input`)
  - Disconnections (`disconnect`)
- Runs a continuous game loop:
  - Updates physics
  - Broadcasts full state to all clients

### Client (client.py)
- Sends **input only** (WASD state)
- Receives **world state**
- Renders all players using `turtle`
- Does NOT simulate physics locally (server controls movement)

---

## How It Works

1. Client connects to server
2. Server assigns player ID and creates player state
3. Client sends input (WASD keys)
4. Server updates physics:
   - velocity
   - position
   - friction
5. Server broadcasts updated world state
6. Clients render the received state

This ensures all players stay synchronized.

---

## Running the Game
### Single Player
- Simply clone the repository and run the main program
### Multiplayer
#### 1. Install dependencies
```bash
pip install flask flask-socketio python-socketio keyboard
```
#### 2. Start the server 
```bash
python server.py
```
If you want external access to the server use a Cloudflare tunnel:
```bash
cloudflared tunnel --url http://localhost:5555
```
#### 3. Start the client
If you are running the server locally use:
```bash
python client.py http://localhost:5555
```
If you are running it using the tunnel use:
```bash
python client.py https://url_from_tunnel.trycloudflare.com #with actual url given to you
```
## Controls
- WASD -> movement
- esc -> quit

## Future Ideas
### Game rooms
- Create multiple rooms
- Join via room code
- Private matches
### Server-Side AI
- Move bot logic to server
- Sync bot behavior for all players
