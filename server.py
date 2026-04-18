# server.py
from flask import request
from flask_socketio import SocketIO, emit
from flask import Flask, request
import math

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

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

# store all player positions

players = {}
#bots = []

@app.route("/")
def index():
    return controller_page

@socketio.on("connect")
def on_connect():
    print("Client connected")
    players[request.sid] = {
    "x": 0,
    "y": 0,
    "vx": 0,
    "vy": 0,
    "dx": 0,
    "dy": 0
    }
    
    emit("your_id", request.sid)

    
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
        for player in list(players.values()):
            update_player(player, acc=1, friction=0.9, right=372,left=-380,top=320,bottom=-315)
        socketio.emit("state", players)
        socketio.sleep(0.016)
        
    
@socketio.on("input")
def handle_input(data):
    player = players.get(request.sid)
    if not player:
        return

    if data["w"]:
        player["dy"] += 1
    if data["s"]:
        player["dy"] -= 1
    if data["a"]:
        player["dx"] -= 1
    if data["d"]:
        player["dx"] += 1
    
   
    

    

@socketio.on("disconnect")
def on_disconnect():
    print("Client disconnected:", request.sid)
    players.pop(request.sid, None)

if __name__ == "__main__":
    socketio.start_background_task(game_loop)
    socketio.run(app, host="0.0.0.0", port=5555)
    
    
#use cloudflared tunnel --url http://localhost:5555 to run tunnel