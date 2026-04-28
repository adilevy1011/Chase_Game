# client.py
import socketio
import math
from player import player
import sys
import turtle
from tkinter import messagebox, simpledialog
import menu
import threading
import queue

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
state_lock = threading.Lock()

# Thread-safe queue for events from SocketIO thread
event_queue = queue.Queue()

# Flags to track if loops are running
render_loop_running = False
send_input_running = False

def init_game():
    global window, instruction_turtle, players, latest_state, running, local_player
    
    window = turtle.Screen()
    window.title("Chase Game Multiplayer")
    window.tracer(0)
    
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
    
    window.update()
    window.getcanvas().focus()

    players = {}
    latest_state = {}
    running = True

    local_player = player()
    local_player.turt.color("blue")

    instructions = turtle.Turtle()
    instructions.hideturtle()
    instructions.speed(0)
    instructions.penup()
    instructions.goto(0, 280)
    instructions.write("Hold on, waiting for room...", align="center", font=("Arial", 12, "normal"))
    instruction_turtle = instructions
    
    # Start checking event queue
    check_event_queue()


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


def check_event_queue():
    """Check if there are any events from SocketIO thread to process"""
    try:
        while True:
            event_name, event_data = event_queue.get_nowait()
            
            if event_name == "prompt_for_room":
                prompt_for_room()
            elif event_name == "rejoin_room":
                rejoin_room()
    except queue.Empty:
        pass
    
    # Check again in 10ms
    window.ontimer(check_event_queue, 10)


@sio.event
def connect():
    print("Connected to server")
    # Queue the prompt instead of calling it directly
    if not already_joined:
        event_queue.put(("prompt_for_room", None))
    else:
        print("Already in a room, skipping prompt")
        event_queue.put(("rejoin_room", None))


@sio.event
def disconnect():
    """Handle unexpected disconnection"""
    print("Disconnected from server")
    global players, latest_state, my_id, render_loop_running, send_input_running
    players = {}
    latest_state = {}
    my_id = None
    render_loop_running = False
    send_input_running = False


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
            quit_game()
    except Exception as e:
        print(f"Error in prompt_for_room: {e}")
        room_name = input("Enter room name: ")
        if room_name:
            join_game_room(room_name.strip())
            already_joined = True
        else:
            quit_game()


def rejoin_room():
    """Rejoin the current room after reconnection"""
    global current_room
    if current_room:
        print(f"Rejoining room: {current_room}")
        sio.emit("join_game", {"room": current_room})


def join_game_room(room_name):
    """Request to join a specific game room"""
    global current_room
    current_room = room_name
    print(f"Attempting to join room: {room_name}")
    sio.emit("join_game", {"room": room_name})
    # Don't start loops yet - wait for joined_game confirmation

@sio.event
def your_id(data):
    global my_id
    my_id = data
    print("My ID:", my_id)

@sio.event
def joined_game(data):
    """Confirmation that we joined a room"""
    global current_room, instruction_turtle, local_player, players, previous_player_count
    global render_loop_running, send_input_running
    
    current_room = data["room"]
    player_count = data["players"]
    previous_player_count = player_count
    
    print(f"Successfully joined room: {data['room']}")
    print(f"Players in room: {player_count}")
    
    # Only clear screen on first join, not on reconnection
    first_join = not render_loop_running
    
    if first_join:
        window.clearscreen()
        window.tracer(0)
        
        # Reset players dictionary only on first join
        players = {}
        
        # Create new local player only on first join
        local_player = player()
        local_player.turt.color("blue")
    
    # Always update the instruction display
    if instruction_turtle:
        try:
            instruction_turtle.clear()
        except:
            pass
    
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
    
    # Re-establish keyboard bindings
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
    
    window.getcanvas().focus_set()
    window.listen()
    
    # NOW start the game loops (only if not already running)
    if not render_loop_running:
        render_loop_running = True
        render_loop()
    
    if not send_input_running:
        send_input_running = True
        send_input()

@sio.event
def state(data):
    global latest_state, instruction_turtle, current_room, previous_player_count
    
    with state_lock:
        latest_state = data.copy()
        
        for pid in list(players.keys()):
            if pid not in data:
                try:
                    players[pid].turt.hideturtle()
                    del players[pid]
                except:
                    pass
    
    current_player_count = len(data)
    if current_player_count != previous_player_count and instruction_turtle and current_room:
        previous_player_count = current_player_count
        
        try:
            instruction_turtle.clear()
            instruction_turtle.penup()
            instruction_turtle.goto(0, 280)
            instruction_turtle.write(
                f"Room: {current_room} | Players: {current_player_count}", 
                align="center", 
                font=("Arial", 12, "normal")
            )
        except:
            pass


def render_loop():
    if not running or not render_loop_running:
        return
    
    try:
        with state_lock:
            current_state = latest_state.copy()
        
        if my_id is not None and current_state and current_room is not None:

            for player_id, p in current_state.items():
                try:
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
                except Exception as e:
                    pass

        window.update()
    except Exception as e:
        pass
    
    window.ontimer(render_loop, 16)

 
def send_input():
    if not running or not send_input_running:
        return
    
    if sio.connected and current_room is not None:
        sio.emit("input", keys.copy())

    window.ontimer(send_input, 30)

    
def connect_to_server(tunnel_address):
    """Connect to the server"""
    try:
        url = tunnel_address if tunnel_address else "http://localhost:5555"
        print(f"Attempting to connect to: {url}")
        
        sio.connect(
            url,
            transports=['websocket', 'polling'],  # Try websocket first, fallback to polling
            wait_timeout=10
        )
        
        print("Connected successfully!")
        
    except socketio.exceptions.ConnectionError as e:
        print(f"Connection error: {e}")
        if window:
            window.bye()
        messagebox.showerror("Connection Error", f"Couldn't connect to server")
        menu.go_to_menu()


def run_game(tunnel_address):
    init_game()
    connect_to_server(tunnel_address)
    turtle.mainloop()
    
if __name__=="__main__":
    run_game()