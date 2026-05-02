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
    transports=['websocket', 'polling'],  # Try websocket first, fallback to polling
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
<html>
<head>
    <title>Game Controller</title>
</head>
<body>
    <h1>Controller</h1>

    <button onmousedown="send('w', true)" onmouseup="send('w', false)">W</button><br><br>
    <button onmousedown="send('a', true)" onmouseup="send('a', false)">A</button>
    <button onmousedown="send('s', true)" onmouseup="send('s', false)">S</button>
    <button onmousedown="send('d', true)" onmouseup="send('d', false)">D</button>

    <script src="https://cdn.socket.io/4.7.5/socket.io.min.js"></script>
    <script>
        const socket = io();

        function send(key, state) {
            let data = {w:false,a:false,s:false,d:false};
            data[key] = state;
            socket.emit("input", data);
        }
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
    socketio.emit("rooms_list", rooms_list, broadcast=True)

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