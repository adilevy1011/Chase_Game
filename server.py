# server.py
from flask import request
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask import Flask
import math
import logging
import warnings
import time

# Suppress Werkzeug logging
logging.getLogger('werkzeug').setLevel(logging.ERROR)
warnings.filterwarnings('ignore')

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False


socketio = SocketIO(
    app, 
    cors_allowed_origins="*",
    async_mode='threading',
    transports=['websocket','polling'],  
    ping_timeout=60,  # Increased from 120
    ping_interval=15,  # More frequent pings (was 25)
    logger=False, 
    engineio_logger=False,
    # Add connection stability options
    max_http_buffer_size=1024000,  # 1MB buffer
    cookie=False  # Disable cookies for better tunnel compatibility
)

class game_room:
    def __init__(self, name):
        self.players = {}
        self.name = name

# Store all game rooms
game_rooms = {}

# Track which room each player is in (socket_id -> room_name)
player_rooms = {}

#Web page for testing
controller_page = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>Game Controller</title>
  <style>
    body { font-family: Arial, sans-serif; color:#111827; margin:0; padding:20px; background:#eef2ff; }
    .container { max-width:980px; margin:0 auto; }
    h1, h2 { margin:0 0 12px 0; }
    .panel { background:#ffffff; border-radius:20px; box-shadow:0 18px 45px rgba(15, 23, 42, 0.12); padding:24px; margin-bottom:20px; }
    .controls { display:flex; flex-wrap:wrap; gap:12px; justify-content:center; margin-top:14px; }
    button { min-width:72px; min-height:72px; border:none; border-radius:18px; background:#2563eb; color:#ffffff; font-size:1rem; font-weight:700; cursor:pointer; transition:transform .12s ease, background .12s ease; }
    button:hover { background:#1d4ed8; transform:translateY(-1px); }
    button.active { background:#0f172a; }
    input { padding:12px 14px; border:1px solid #cbd5e1; border-radius:14px; width:260px; }
    .status { display:flex; flex-wrap:wrap; gap:10px; margin-top:16px; }
    .status span { background:#e0f2fe; padding:10px 14px; border-radius:14px; font-size:.95rem; }
    #canvas { width:100%; height:auto; border-radius:18px; background:#0f172a; display:block; }
    .preview-row { display:flex; flex-wrap:wrap; gap:18px; align-items:flex-start; }
    .players-panel { min-width:260px; max-width:320px; flex:1; }
    .players-panel h3 { margin-top:0; }
    .players-list { list-style:none; padding:0; margin:0; display:grid; gap:10px; }
    .players-list li { background:#f8fafc; border:1px solid #e2e8f0; border-radius:16px; padding:12px 14px; }
    .players-list span { display:block; color:#475569; font-size:.88rem; margin-top:6px; }
    .rooms-list { list-style:none; padding:0; margin:0; display:grid; gap:10px; }
    .rooms-list li { display:flex; justify-content:space-between; align-items:center; padding:14px 16px; border-radius:16px; background:#f8fafc; border:1px solid #e2e8f0; }
    .rooms-list strong { font-size:1rem; }
    .footer { color:#475569; font-size:.95rem; margin-top:10px; }
  </style>
</head>
<body>
  <div class="container">
    <div class="panel">
      <h1>Chase Game Controller</h1>
      <p>Join a room, send WASD commands, and watch player positions update live on the mini-map.</p>

      <div class="status">
        <span id="status">Disconnected</span>
        <span id="room-status">Room: None</span>
        <span id="player-status">Player: -</span>
      </div>

      <div style="margin-top:18px; display:flex; gap:10px; flex-wrap:wrap; align-items:center;">
        <input id="room-name" placeholder="Enter room name" />
        <button id="join-button">Join room</button>
      </div>
    </div>

    <div class="panel">
      <h2>Available rooms</h2>
      <ul id="rooms" class="rooms-list">
        <li>Loading rooms…</li>
      </ul>
    </div>

    <div class="panel">
      <h2>Live controller</h2>
      <div class="preview-row">
        <div class="controls" style="flex:1; min-width:220px;">
          <button id="up" data-key="w">W</button>
          <button id="left" data-key="a">A</button>
          <button id="down" data-key="s">S</button>
          <button id="right" data-key="d">D</button>
          <p style="margin-top:12px; color:#475569;">Use WASD or arrow keys to move. Click anywhere on the page to focus, and buttons also work on mobile via touch.</p>
        </div>
        <div class="players-panel">
          <h3>Room players</h3>
          <ul id="players" class="players-list">
            <li>No player data yet</li>
          </ul>
        </div>
      </div>
    </div>

    <div class="panel">
      <h2>Live game preview</h2>
      <canvas id="canvas" width="880" height="400"></canvas>
    </div>

    <div class="footer">Interactive demo page served by Flask + Socket.IO.</div>
  </div>

  <script src="https://cdn.socket.io/4.7.5/socket.io.min.js"></script>
  <script>
    const canvas = document.getElementById('canvas');
    const ctx = canvas.getContext('2d');
    const statusEl = document.getElementById('status');
    const roomStatusEl = document.getElementById('room-status');
    const playerStatusEl = document.getElementById('player-status');
    const roomsEl = document.getElementById('rooms');
    const roomInput = document.getElementById('room-name');
    const joinButton = document.getElementById('join-button');

    let currentRoom = null;
    let myId = null;
    let players = {};
    const inputState = { w:false, a:false, s:false, d:false };

    const playersEl = document.getElementById('players');
    const socket = io();

    socket.on('connect', () => {
      statusEl.textContent = 'Connected';
      statusEl.style.background = '#dcfce7';
      statusEl.style.color = '#166534';
      socket.emit('get_rooms');
    });

    socket.on('disconnect', () => {
      statusEl.textContent = 'Disconnected';
      statusEl.style.background = '';
      statusEl.style.color = '';
      roomStatusEl.textContent = 'Room: None';
      playerStatusEl.textContent = 'Player: -';
      currentRoom = null;
      players = {};
      updatePlayersPanel();
      drawMap();
    });

    socket.on('rooms_list', (rooms) => {
      renderRooms(rooms);
    });

    socket.on('joined_game', (data) => {
      currentRoom = data.room;
      roomStatusEl.textContent = 'Room: ' + currentRoom + ' (' + data.players + ' players)';
      setStatus('Joined ' + currentRoom);
      socket.emit('get_rooms');
    });

    socket.on('your_id', (id) => {
      myId = id;
      playerStatusEl.textContent = 'Player: ' + id.slice(0, 6);
    });

    socket.on('state', (roomPlayers) => {
      players = roomPlayers;
      updatePlayersPanel();
      drawMap();
    });

    function renderRooms(rooms) {
      if (!Array.isArray(rooms) || rooms.length === 0) {
        roomsEl.innerHTML = '<li>No active rooms yet</li>';
        return;
      }
      roomsEl.innerHTML = '';
      rooms.forEach(room => {
        const item = document.createElement('li');
        item.innerHTML = '<strong>' + escapeHtml(room.name) + '</strong> <span>' + room.players + ' player' + (room.players === 1 ? '' : 's') + '</span>';
        const joinBtn = document.createElement('button');
        joinBtn.textContent = 'Join';
        joinBtn.addEventListener('click', () => {
          roomInput.value = room.name;
          joinRoom();
        });
        item.appendChild(joinBtn);
        roomsEl.appendChild(item);
      });
    }

    function joinRoom() {
      const roomName = roomInput.value.trim();
      if (!roomName) {
        setStatus('Enter a room name first', true);
        return;
      }
      socket.emit('join_game', { room: roomName });
    }

    function setStatus(message, isError = false) {
      statusEl.textContent = message;
      statusEl.style.background = isError ? '#fee2e2' : '#e0f2fe';
      statusEl.style.color = isError ? '#b91c1c' : '#0c4a6e';
    }

    function sendInput() {
      socket.emit('input', { ...inputState });
      updateButtonStates();
    }

    function sendInputWhileActive() {
      if (Object.values(inputState).some(Boolean)) {
        sendInput();
      }
    }

    function updateButtonStates() {
      ['w','a','s','d'].forEach(key => {
        const button = document.querySelector('[data-key="' + key + '"]');
        if (button) button.classList.toggle('active', inputState[key]);
      });
    }

    function updatePlayersPanel() {
      const entries = Object.entries(players || {});
      if (!entries.length) {
        playersEl.innerHTML = '<li>No player data yet</li>';
        return;
      }
      playersEl.innerHTML = '';
      entries.forEach(([id, player]) => {
        const item = document.createElement('li');
        const name = id === myId ? 'You' : 'Player ' + id.slice(0,4);
        item.innerHTML = '<strong>' + escapeHtml(name) + '</strong>' +
          '<span>Position: ' + Math.round(player.x) + ', ' + Math.round(player.y) + '</span>' +
          '<span>Velocity: ' + Math.round(player.vx || 0) + ', ' + Math.round(player.vy || 0) + '</span>';
        playersEl.appendChild(item);
      });
    }

    function escapeHtml(text) {
      return text.replace(/[&<>"']/g, char => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":"&#39;" })[char]);
    }

    joinButton.addEventListener('click', joinRoom);

    document.body.tabIndex = 0;
    document.body.addEventListener('click', () => document.body.focus());

    ['up','left','down','right'].forEach(id => {
      const button = document.getElementById(id);
      const key = button.dataset.key;
      button.addEventListener('mousedown', () => { inputState[key] = true; sendInput(); });
      button.addEventListener('mouseup', () => { inputState[key] = false; sendInput(); });
      button.addEventListener('touchstart', (event) => { event.preventDefault(); inputState[key] = true; sendInput(); }, { passive:false });
      button.addEventListener('touchend', (event) => { event.preventDefault(); inputState[key] = false; sendInput(); });
    });

    window.addEventListener('keydown', (event) => {
      const key = normalizeKey(event.key);
      if (key && !inputState[key]) {
        inputState[key] = true;
        sendInput();
      }
    });

    window.addEventListener('keyup', (event) => {
      const key = normalizeKey(event.key);
      if (key && inputState[key]) {
        inputState[key] = false;
        sendInput();
      }
    });

    window.addEventListener('blur', () => {
      ['w','a','s','d'].forEach(key => inputState[key] = false);
      sendInput();
    });

    let lastSentInput = JSON.stringify(inputState);

    function normalizeKey(key) {
      key = key.toLowerCase();
      if (key === 'arrowup') return 'w';
      if (key === 'arrowdown') return 's';
      if (key === 'arrowleft') return 'a';
      if (key === 'arrowright') return 'd';
      if (['w','a','s','d'].includes(key)) return key;
      return null;
    }

    function drawMap() {
      const width = canvas.width;
      const height = canvas.height;
      ctx.clearRect(0, 0, width, height);
      ctx.fillStyle = '#0f172a';
      ctx.fillRect(0, 0, width, height);

      ctx.strokeStyle = '#334155';
      ctx.lineWidth = 1;
      for (let x = 0; x <= width; x += 80) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, height);
        ctx.stroke();
      }
      for (let y = 0; y <= height; y += 80) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
        ctx.stroke();
      }

      ctx.strokeStyle = '#60a5fa';
      ctx.lineWidth = 3;
      ctx.strokeRect(40, 40, width - 80, height - 80);
      ctx.fillStyle = 'rgba(59, 130, 246, 0.08)';
      ctx.fillRect(40, 40, width - 80, height - 80);

      ctx.fillStyle = '#cbd5e1';
      ctx.font = '13px Arial';
      ctx.fillText('Arena bounds: 390 x 295', 50, 60);
      ctx.fillText('Center = (0,0)', width - 150, 60);
      ctx.fillText('Use the controls or keyboard to move this player in real time.', 50, height - 20);

      Object.entries(players).forEach(([id, player]) => {
        if (!player || typeof player.x !== 'number' || typeof player.y !== 'number') return;
        const px = width / 2 + player.x;
        const py = height / 2 - player.y;
        const radius = 18;
        ctx.beginPath();
        ctx.fillStyle = id === myId ? '#22c55e' : '#3b82f6';
        ctx.strokeStyle = '#e2e8f0';
        ctx.lineWidth = 2;
        ctx.arc(px, py, radius, 0, Math.PI * 2);
        ctx.fill();
        ctx.stroke();

        ctx.fillStyle = '#ffffff';
        ctx.font = 'bold 12px Arial';
        ctx.fillText(id === myId ? 'You' : id.slice(0, 4), px - 18, py - 22);
        ctx.font = '11px Arial';
        ctx.fillText('x:' + Math.round(player.x) + ' y:' + Math.round(player.y), px - 18, py + 28);
      });

      if (!Object.keys(players).length) {
        ctx.fillStyle = '#94a3b8';
        ctx.font = '18px Arial';
        ctx.fillText('Waiting for players...', width / 2 - 110, height / 2);
      }
    }

    drawMap();
    setInterval(sendInputWhileActive, 70);
    setInterval(() => socket.emit('get_rooms'), 3000);
  </script>
</body>
</html>
"""

@app.route("/")
def index():
    return controller_page

def update_player(player, acc, friction, right, left, top, bottom):
    # --- normalize input direction ---
    length = math.hypot(player["dx"], player["dy"])
    if length != 0:
        player["dx"] /= length
        player["dy"] /= length

    # --- velocity update ---
    player["vx"] += player["dx"] * acc
    player["vy"] += player["dy"] * acc

    player["vx"] *= friction
    player["vy"] *= friction

    # --- position update ---
    x = player["x"]
    y = player["y"]

    new_x = x + player["vx"]
    new_y = y + player["vy"]

    # --- boundary check ---
    if new_x > right:
        new_x = right
        player["vx"] = 0
    elif new_x < left:
        new_x = left
        player["vx"] = 0

    if new_y > top:
        new_y = top
        player["vy"] = 0
    elif new_y < bottom:
        new_y = bottom
        player["vy"] = 0

    player["x"] = new_x
    player["y"] = new_y

    # --- reset input ---
    player["dx"] = 0
    player["dy"] = 0

@socketio.on("get_rooms")
def on_get_rooms():
    """Return list of all active rooms"""
    rooms_list = []
    for room_name, room in game_rooms.items():
        rooms_list.append({
            "name": room_name,
            "players": len(room.players)
        })
    emit("rooms_list", rooms_list)

def broadcast_rooms_update():
    """Broadcast updated room list to all connected clients"""
    rooms_list = []
    for room_name, room in game_rooms.items():
        rooms_list.append({
            "name": room_name,
            "players": len(room.players)
        })
    socketio.emit("rooms_list", rooms_list) 

@socketio.on("ping")
def on_ping():
    """Respond to client ping to test connection"""
    emit("pong")

@socketio.on("heartbeat")
def on_heartbeat():
    """Handle heartbeat from client"""
    emit("heartbeat_ack", {"timestamp": time.time()})

def game_loop():
    """Main game loop with heartbeat monitoring"""
    last_heartbeat_check = time.time()

    while True:
        current_time = time.time()

        # Update and broadcast for each room
        for room_name, room in list(game_rooms.items()):
            for player in list(room.players.values()):
                update_player(player, acc=1.5, friction=0.9, right=390, left=-395, top=295, bottom=-290)

            # Broadcast only to players in this room
            socketio.emit("state", room.players, room=room_name)

        # Check for inactive players every 30 seconds
        if current_time - last_heartbeat_check > 30:
            check_inactive_players()
            last_heartbeat_check = current_time

        socketio.sleep(0.016)

def check_inactive_players():
    """Remove players who haven't sent input recently"""
    current_time = time.time()
    timeout_threshold = 60  # 60 seconds timeout

    for room_name, room in list(game_rooms.items()):
        inactive_players = []
        for player_id, player_data in room.players.items():
            # Check if player has a last_activity timestamp
            last_activity = player_data.get('last_activity', current_time)
            if current_time - last_activity > timeout_threshold:
                inactive_players.append(player_id)

        # Remove inactive players
        for player_id in inactive_players:
            print(f"Removing inactive player {player_id} from room {room_name}")
            room.players.pop(player_id, None)

        # Clean up empty rooms
        if len(room.players) == 0:
            game_rooms.pop(room_name, None)
            print(f"Deleted empty room: {room_name}")

@socketio.on("connect")
def on_connect():
    print(f"Client connected: {request.sid}")
    # Don't create player yet - wait for room join

@socketio.on("join_game")
def on_join_game(data):
    """Client requests to join a specific game room"""
    room_name = data.get("room")
    
    if not room_name:
        emit("error", {"message": "Room name required"})
        return
    
    # Create room if it doesn't exist
    if room_name not in game_rooms:
        game_rooms[room_name] = game_room(room_name)
        print(f"Created new room: {room_name}")
        # Broadcast room update when new room is created
        broadcast_rooms_update()
    
    room = game_rooms[room_name]
    
    # Check if player already exists in this room (reconnection)
    if request.sid in room.players:
        print(f"Player {request.sid} reconnecting to room: {room_name}")
        # Don't reset position - keep existing player state
    else:
        # New player - create with default position
        print(f"New player {request.sid} joining room: {room_name}")
        room.players[request.sid] = {
            "x": 0,
            "y": 0,
            "vx": 0,
            "vy": 0,
            "dx": 0,
            "dy": 0,
            "last_activity": time.time()  # Initialize activity timestamp
        }
    
    # Track which room this player is in
    player_rooms[request.sid] = room_name
    
    # Join the SocketIO room (for broadcasting)
    join_room(room_name)
    
    print(f"Room {room_name} now has {len(room.players)} players")
    
    # Broadcast updated room list to all clients
    broadcast_rooms_update()
    
    # Send player their ID and room info
    emit("your_id", request.sid)
    emit("joined_game", {"room": room_name, "players": len(room.players)})

@socketio.on("input")
def handle_input(data):
    # Get which room this player is in
    room_name = player_rooms.get(request.sid)
    
    if not room_name or room_name not in game_rooms:
        return
    
    room = game_rooms[room_name]
    player = room.players.get(request.sid)
    
    if not player:
        return

    # Update last activity timestamp
    player['last_activity'] = time.time()

    if data.get("w"):
        player["dy"] += 1
    if data.get("s"):
        player["dy"] -= 1
    if data.get("a"):
        player["dx"] -= 1
    if data.get("d"):
        player["dx"] += 1

@socketio.on("disconnect")
def on_disconnect():
    print(f"Client disconnected: {request.sid}")
    
    # Get which room the player was in
    room_name = player_rooms.get(request.sid)
    
    if room_name and room_name in game_rooms:
        room = game_rooms[room_name]
        
        # Remove player from room
        room.players.pop(request.sid, None)
        print(f"Removed player from room: {room_name}")
        print(f"Room {room_name} now has {len(room.players)} players")
        
        # Broadcast updated room list
        broadcast_rooms_update()
        
        # Delete empty rooms (optional - keeps memory clean)
        if len(room.players) == 0:
            del game_rooms[room_name]
            print(f"Deleted empty room: {room_name}")
            # Broadcast again after room deletion
            broadcast_rooms_update()
    
    # Remove from player tracking
    player_rooms.pop(request.sid, None)

if __name__ == "__main__":
    print("Starting server on port 5555...")
    try:
        socketio.start_background_task(game_loop)
        socketio.run(app, host="0.0.0.0", port=5555, debug=False, use_reloader=False)
    except Exception as e:
        print(f"Server error: {e}")
    
    
#cloudflared tunnel --url http://localhost:5555