# Chase Game (Singleplayer + Multiplayer)

A Python-based real-time chase game built with `turtle`, supporting both local singleplayer and online multiplayer using WebSockets (Flask-SocketIO + Socket.IO client).

**Note**: The public server option is currently available as a trial run on DigitalOcean but will be shut down soon due to hosting costs. Use Cloudflare Tunnel or host your own server for long-term multiplayer gaming.

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
- Automatic room creation - join any room name
- Room list broadcasting - see active rooms and player counts
- Heartbeat monitoring and automatic cleanup of inactive players
- Automatic reconnection on disconnection
- Cross-platform networking support
- Works with Public Server, Cloudflare Tunnel, or direct hosting

---

## Architecture Overview

### Server (`server.py`)
- Built with Flask + Flask-SocketIO
- Maintains **authoritative game state** for all rooms
- Handles:
  - Player connections and room joining (`connect`, `join_game`)
  - Player input (`input`)
  - Disconnections and room cleanup (`disconnect`)
  - Room list requests and broadcasting (`get_rooms`, `broadcast_rooms_update`)
  - Heartbeat monitoring and inactive player removal
- Runs a continuous game loop:
  - Updates physics for all players in all rooms
  - Broadcasts full state to room-specific clients every ~16ms
- Auto-creates rooms on first join, deletes empty rooms
- Supports connections from any IP (for public hosting)

### Client (`client.py`)
- Sends **input only** (WASD state)
- Receives **world state** for current room
- Renders all players in the room using `turtle`
- Does NOT simulate physics locally (server controls all movement)
- Thread-safe event handling for network events
- Automatic reconnection on disconnection with exponential backoff
- Heartbeat monitoring to detect connection issues

### Menu (`menu.py`)
- Main entry point for the game
- Options for singleplayer and multiplayer
- In multiplayer mode, choose from three connection options:
  - **Public Server**: Connects to a hosted server on DigitalOcean (trial run, will be shut down soon due to costs)
  - **Cloudflare**: Use a Cloudflare tunnel URL for secure remote access
  - **Localhost**: Connect to a local server for testing on the same network
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
pip install flask flask-socketio python-socketio python-engineio werkzeug==2.3.7 pyautogui
```

### Singleplayer Mode
```bash
python menu.py
```
Select "Play single player" from the menu.

### Multiplayer Mode

The game supports three connection methods:

#### Option 1: Public Server (Trial - Will be shut down soon)
- **Cost**: This uses a DigitalOcean droplet which costs money
- **Purpose**: Trial run to test remote multiplayer functionality
- **How to use**:
  1. Run `python menu.py`
  2. Select "Play multiplayer"
  3. Choose "Public Server"
  4. Enter a room name
- **Server Address**: `http://147.182.235.138:80`

#### Option 2: Cloudflare Tunnel (Recommended for remote play)
- **Cost**: Free
- **Purpose**: Secure remote access across the internet
- **How to use**:
  1. Start the server: `python server.py`
  2. In another terminal, create tunnel: `cloudflared tunnel --url http://localhost:5555`
  3. Copy the HTTPS URL provided by cloudflared
  4. Run `python menu.py`
  5. Select "Play multiplayer"
  6. Choose "Cloudflare"
  7. Enter the tunnel URL from step 3
  8. Enter a room name

#### Option 3: Localhost (For local testing)
- **Cost**: Free
- **Purpose**: Testing on the same computer or local network
- **How to use**:
  1. Start the server: `python server.py`
  2. Run `python menu.py`
  3. Select "Play multiplayer"
  4. Choose "Local Host"
  5. Enter a room name (creates room if doesn't exist)

### Hosting Your Own Server
To host the server yourself:
```bash
python server.py
```
The server runs on `http://localhost:5555` and accepts connections from any IP when hosted publicly.

### Network Testing (Multiple Computers)

#### Using Public Server (Trial)
- Run `python menu.py` on each computer
- Select "Play multiplayer" → "Public Server"
- Enter the same room name to play together
- **Note**: This server will be shut down soon due to hosting costs

#### Using Cloudflare Tunnel
1. On the host computer, start the server:
```bash
python server.py
```

2. Create a Cloudflare tunnel:
```bash
cloudflared tunnel --url http://localhost:5555
```
This gives you a URL like `https://example-example-example.trycloudflare.com`

3. On any computer, run the game:
```bash
python menu.py
```

4. In the menu:
- Select **Multiplayer**
- Choose **Cloudflare**
- Enter the Cloudflare tunnel URL from step 2
- Enter a room name

5. Other players can do the same:
- They enter the same Cloudflare tunnel URL
- They enter the same room name to play together
- Or enter a different room name to play separately

#### Using Local Network
- Ensure all computers are on the same network
- Start server on one computer: `python server.py`
- On other computers, use the server's local IP address instead of localhost
- Select "Local Host" option in the menu

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
- **Public Server**: Variable latency depending on location (hosted on DigitalOcean)
- **Cloudflare Tunnel**: Adds ~100-200ms latency
- **Localhost**: Minimal latency (<1ms)
- Smooth movement despite network latency through frequent updates

---

## Troubleshooting

### "Couldn't connect to server"
- **Public Server**: May be offline (trial period ending soon)
- **Cloudflare**: Verify server is running and tunnel URL is correct (copy-paste from cloudflared output)
- **Localhost**: Check that server is running on the same machine/network
- Ensure firewall allows connections on port 5555 (or 80 for public server)

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
