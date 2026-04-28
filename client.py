# client.py
import socketio
import math
from player import player
import sys
import turtle
from tkinter import messagebox, simpledialog
import menu
import threading

sio = socketio.Client()

my_id = None
current_room = None
window = None
instruction_turtle = None
running = False
players = {}
latest_state = {}
local_player = None
already_joined = False
previous_player_count = 0
# Lock for thread-safe access to shared state
state_lock = threading.Lock()

def init_game():
    global window, instruction_turtle, players, latest_state, running, local_player
    
    window = turtle.Screen()
    window.title("Chase Game Multiplayer")
    window.tracer(0)
    
    # Setup keyboard input
    window.setup(width=800, height=600)
    window.listen()
    
    window.onkeypress(press_w, "w")
    window.onkeyrelease(release_w, "w")
    window.onkeypress(press_a, "a")
    window.onkeyrelease(release_a, "a")
    window.onkeypress(press_s, "s")
    window.onkeyrelease(release_s, "s")
    window.onkeypress(press_d, "d")
    window.onkeyrelease(release_d, "d")
    window.onkeypress(quit_game, "Escape")
    
    # Give focus to window
    window.update()
    window.getcanvas().focus()

    players = {}
    latest_state = {}
    running = True

    local_player = player()
    local_player.turt.color("blue")

    # Display instructions
    instructions = turtle.Turtle()
    instructions.hideturtle()
    instructions.speed(0)
    instructions.penup()
    instructions.goto(0, 280)
    instructions.write("Hold on, waiting for room...", align="center", font=("Arial", 12, "normal"))
    instruction_turtle = instructions


keys = {
    "w": False,
    "a": False,
    "s": False,
    "d": False
}

def press_w(): 
    keys["w"] = True

def release_w(): 
    keys["w"] = False

def press_a(): 
    keys["a"] = True

def release_a(): 
    keys["a"] = False

def press_s(): 
    keys["s"] = True

def release_s(): 
    keys["s"] = False

def press_d(): 
    keys["d"] = True

def release_d(): 
    keys["d"] = False

def quit_game():
    global running, window
    print("Disconnecting...")
    
    running = False
    try:
        sio.disconnect()
    except:
        pass
    if window:
        window.bye()
    menu.go_to_menu()


@sio.event
def connect():
    print("Connected to server")
    # Schedule the prompt on the main thread after a small delay
    if not already_joined:
        window.ontimer(prompt_for_room, 100)
    else:
        print("Already in a room, skipping prompt")
        # Re-join the room after reconnection
        window.ontimer(rejoin_room, 100)

def rejoin_room():
    """Rejoin the current room after reconnection"""
    global current_room
    if current_room:
        print(f"Rejoining room: {current_room}")
        sio.emit("join_game", {"room": current_room})

@sio.event
def disconnect():
    """Handle unexpected disconnection"""
    print("Disconnected from server")
    # Clear game state on disconnect
    global players, latest_state, my_id
    players = {}
    latest_state = {}
    my_id = None


def prompt_for_room():
    """Ask the user which room to join"""
    global already_joined
    try:
        root = window.getcanvas().winfo_toplevel()
        room_name = simpledialog.askstring(
            "Join Game Room", 
            "Enter room name:",
            parent=root
        )
        
        if room_name:
            join_game_room(room_name.strip())
            already_joined = True
        else:
            # User cancelled
            quit_game()
    except Exception as e:
        print(f"Error in prompt_for_room: {e}")
        # Fallback: ask through console
        room_name = input("Enter room name: ")
        if room_name:
            join_game_room(room_name.strip())
            already_joined = True
        else:
            quit_game()


def join_game_room(room_name):
    """Request to join a specific game room"""
    global current_room
    current_room = room_name
    print(f"Attempting to join room: {room_name}")
    sio.emit("join_game", {"room": room_name})
    send_input()
    render_loop()


@sio.event
def your_id(data):
    global my_id
    my_id = data
    print("My ID:", my_id)


@sio.event
def joined_game(data):
    """Confirmation that we joined a room"""
    global current_room, instruction_turtle, local_player, players, previous_player_count
    current_room = data["room"]
    player_count = data["players"]
    previous_player_count = player_count  # Initialize with first count
    
    print(f"Successfully joined room: {data['room']}")
    print(f"Players in room: {player_count}")
    
    # Clear the entire screen
    window.clearscreen()
    window.tracer(0)
    
    # Reset players dictionary (clear old players)
    players = {}
    
    # Redraw the local player
    local_player = player()
    local_player.turt.color("blue")
    
    # Create new instruction turtle
    instructions = turtle.Turtle()
    instructions.hideturtle()
    instructions.speed(0)
    instructions.penup()
    instructions.goto(0, 280)
    instructions.write(
        f"Room: {data['room']} | Players: {player_count}", 
        align="center", 
        font=("Arial", 12, "normal")
    )
    instruction_turtle = instructions
    
    # RE-ESTABLISH KEYBOARD BINDINGS after clearscreen
    window.listen()
    window.onkeypress(press_w, "w")
    window.onkeyrelease(release_w, "w")
    window.onkeypress(press_a, "a")
    window.onkeyrelease(release_a, "a")
    window.onkeypress(press_s, "s")
    window.onkeyrelease(release_s, "s")
    window.onkeypress(press_d, "d")
    window.onkeyrelease(release_d, "d")
    window.onkeypress(quit_game, "Escape")
    
    # Re-focus window after dialog closes
    window.getcanvas().focus_set()
    window.listen()


@sio.event
def state(data):
    global latest_state, instruction_turtle, current_room, previous_player_count
    
    # Use lock to safely update state
    with state_lock:
        latest_state = data.copy()
        
        # Remove players that are no longer in the state
        for pid in list(players.keys()):
            if pid not in data:
                try:
                    players[pid].turt.hideturtle()
                    del players[pid]
                except:
                    pass
    
    # Update player count if it changed
    current_player_count = len(data)
    if current_player_count != previous_player_count and instruction_turtle and current_room:
        previous_player_count = current_player_count
        
        instruction_turtle.clear()
        instruction_turtle.penup()
        instruction_turtle.goto(0, 280)
        instruction_turtle.write(
            f"Room: {current_room} | Players: {current_player_count}", 
            align="center", 
            font=("Arial", 12, "normal")
        )


def render_loop():
    if not running:
        return
    
    try:
        # Use lock to safely read state
        with state_lock:
            current_state = latest_state.copy()
        
        if my_id is not None and current_state and current_room is not None:

            for player_id, p in current_state.items():
                try:
                    # own player
                    if player_id == my_id:
                        t = local_player
                    else:
                        if player_id not in players:
                            players[player_id] = player()
                            players[player_id].turt.color("red")
                        t = players[player_id]

                    t.turt.goto(p["x"], p["y"])

                    if p["vx"] != 0 or p["vy"] != 0:
                        angle = math.degrees(math.atan2(p["vy"], p["vx"]))
                        t.turt.setheading(angle)
                except:
                    # Skip if turtle was deleted
                    pass

        window.update()
    except:
        # Skip this frame if there's an error
        pass
    
    window.ontimer(render_loop, 16)

 
def send_input():
    if not running:
        return
    
    if sio.connected and current_room is not None:
        sio.emit("input", keys.copy())

    window.ontimer(send_input, 50)

    
def connect_to_server(tunnel_address):
    """Connect to the server"""
    try:
        url = tunnel_address if tunnel_address else "http://localhost:5555"
        print(f"Attempting to connect to: {url}")
        
        if tunnel_address == None:
            sio.connect(
                "http://localhost:5555",
                transports=['websocket', 'polling']
            )
        else:
            sio.connect(
                tunnel_address,
                transports=['websocket', 'polling']
            )
        
        print("Connected successfully!")
        
    except socketio.exceptions.ConnectionError as e:
        print(f"Connection error: {e}")
        if window:
            window.bye()
        messagebox.showerror("Connection Error", f"Couldn't connect to server:\n{str(e)}")
        menu.go_to_menu()
    except Exception as e:
        print(f"Unexpected error: {e}")
        if window:
            window.bye()
        messagebox.showerror("Error", f"Unexpected error:\n{str(e)}")
        menu.go_to_menu()

def run_game(tunnel_address):
    init_game()
    connect_to_server(tunnel_address)
    turtle.mainloop()
    
if __name__=="__main__":
    run_game()