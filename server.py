# server.py
from flask import request
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask import Flask
import math

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

class game_room:
    def __init__(self, name):
        self.players = {}
        self.name = name

# Store all game rooms
game_rooms = {}

# Track which room each player is in (socket_id -> room_name)
player_rooms = {}



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

def game_loop():
    while True:
        # Update and broadcast for each room
        for room_name, room in list(game_rooms.items()):
            for player in list(room.players.values()):
                update_player(player, acc=1.5, friction=0.9, right=390, left=-395, top=295, bottom=-290)
            
            # Broadcast only to players in this room
            socketio.emit("state", room.players, room=room_name)
        
        socketio.sleep(0.016)

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
    
    room = game_rooms[room_name]
    
    # Add player to room
    room.players[request.sid] = {
        "x": 0,
        "y": 0,
        "vx": 0,
        "vy": 0,
        "dx": 0,
        "dy": 0
    }
    
    # Track which room this player is in
    player_rooms[request.sid] = room_name
    
    # Join the SocketIO room (for broadcasting)
    join_room(room_name)
    
    print(f"Player {request.sid} joined room: {room_name}")
    print(f"Room {room_name} now has {len(room.players)} players")
    
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
        
        # Delete empty rooms (optional - keeps memory clean)
        if len(room.players) == 0:
            del game_rooms[room_name]
            print(f"Deleted empty room: {room_name}")
    
    # Remove from player tracking
    player_rooms.pop(request.sid, None)

if __name__ == "__main__":
    socketio.start_background_task(game_loop)
    socketio.run(app, host="0.0.0.0", port=5555)
    
    
#cloudflared tunnel --url http://localhost:5555