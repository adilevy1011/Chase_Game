# Chase Game (Singleplayer + Multiplayer)

A Python-based real-time chase game built with `turtle`, supporting both local singleplayer and online multiplayer using WebSockets (Flask-SocketIO + Socket.IO client).

---

## Features

### Singleplayer Mode
- Built with Python `turtle`
- Player movement with WASD
- Bot AI chasing system

### Multiplayer Mode (Real-Time)
- Multiple game rooms with separate matches
- Real-time movement synchronization across players
- Server-authoritative player positions
- Smooth interpolation using frequent updates (~16ms loop)
- Works across networks using Cloudflare Tunnel or direct hosting
- Automatic room creation - join any room name
- Cross-platform networking support

---

## Architecture Overview

### Server (`server.py`)
- Built with Flask + Flask-SocketIO
- Maintains **authoritative game state** for all rooms
- Handles:
  - Player connections and room joining (`connect`, `join_game`)
  - Player input (`input`)
  - Disconnections and room cleanup (`disconnect`)
- Runs a continuous game loop:
  - Updates physics for all players in all rooms
  - Broadcasts full state to room-specific clients every ~16ms
- Auto-creates rooms on first join, deletes empty rooms

### Client (`client.py`)
- Sends **input only** (WASD state)
- Receives **world state** for current room
- Renders all players in the room using `turtle`
- Does NOT simulate physics locally (server controls all movement)
- Thread-safe event handling for network events

### Menu (`menu.py`)
- Main entry point for the game
- Options for singleplayer and multiplayer
- Prompts for Cloudflare tunnel URL in multiplayer mode
- Room name entry before joining

---

## How It Works

### Multiplayer Flow
1. User runs `menu.py` and selects multiplayer
2. User enters Cloudflare tunnel URL (or localhost for local testing)
3. Client connects to server
4. Server assigns player ID and creates player state
5. User enters room name (creates room if doesn't exist)
6. Client sends input (WASD keys) every ~30ms
7. Server updates all players in the room:
   - Applies input to velocity
   - Updates physics (acceleration, friction, boundaries)
   - Updates position
8. Server broadcasts updated room state to all players in that room every ~16ms
9. Clients render received player positions and rotations

This ensures all players stay synchronized with server authority.

---

## Running the Game

### Prerequisites
```bash
pip install flask flask-socketio python-socketio python-engineio werkzeug==2.3.7
```

### Local Testing (Single Computer)

#### 1. Start the server
```bash
python server.py
```
Server will start on `http://localhost:5555`

#### 2. Run the game
```bash
python menu.py
```

#### 3. In the menu:
- Select **Multiplayer**
- Enter server address: `http://localhost:5555`
- Enter a room name (e.g., "room1")

Open `menu.py` multiple times to test multiple players in the same room.

### Network Testing (Multiple Computers or Cloudflare Tunnel)

#### 1. Start the server
```bash
python server.py
```

#### 2. Create a Cloudflare tunnel (in another terminal)
```bash
cloudflared tunnel --url http://localhost:5555
```
This gives you a URL like `https://example-example-example.trycloudflare.com`

#### 3. On any computer, run the game
```bash
python menu.py
```

#### 4. In the menu:
- Select **Multiplayer**
- Enter the Cloudflare tunnel URL from step 2
- Enter a room name

#### 5. Other players can do the same
- They enter the same Cloudflare tunnel URL
- They enter the same room name to play together
- Or enter a different room name to play separately

---

## Controls

- **WASD** - Movement
- **Esc** - Quit to menu

---

## Game Rooms

- Each room is a separate game instance
- Rooms are created automatically when first player joins
- Empty rooms are automatically deleted
- Players only see other players in their room
- Room names can be anything (case-sensitive)
- No password protection - anyone with the server URL can join
---

## Network Details

### Client → Server
- **Input events** (every ~30ms)
- **Join room requests**
- **Disconnect signals**

### Server → Client
- **World state** (every ~16ms)
- **Player ID confirmation**
- **Room join confirmation**

### Data Flow
Client Input (WASD)
↓
Server Physics Update
↓
Server Broadcasts State
↓
Client Renders New Positions

---

## Performance Notes

- Server loop runs at ~62.5 FPS (16ms per frame)
- Client input sent every ~33ms
- Uses WebSocket with HTTP polling fallback
- Tested with Cloudflare Tunnel (adds ~100-200ms latency)
- Smooth movement despite network latency through frequent updates

---

## Troubleshooting

### "Couldn't connect to server"
- Verify server is running: `python server.py`
- Check the URL is correct (copy-paste from cloudflared tunnel output)
- Ensure firewall allows connections

### Players not seeing each other
- Verify both joined the **same room name** (case-sensitive)
- Check server console shows both players in the same room
- Restart client and rejoin

### Movement stuttering
- This is normal on Cloudflare Tunnel (higher latency)
- Works smoothly on local networks
- Movement syncs correctly despite visual stuttering

### Server keeps showing "write() before start_response" errors
- These are harmless Werkzeug warnings during reconnection
- Game continues to work normally
- Safe to ignore

---

## Future Ideas

### Gameplay Features
- Game objectives (tag/chase mechanics)
- Score tracking per room
- Leaderboards
- Power-ups

### Server Features
- Persistent rooms (don't delete after empty)
- Admin commands
- Server-side AI/bots in rooms
- Chat system between players

### Client Features
- Custom player colors
- Player names/usernames
- Spectator mode
- Replay recording
