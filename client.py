# client.py
import socketio
import math
from player import player
import sys
import turtle
from tkinter import messagebox, simpledialog
import menu
import time

sio = socketio.Client()

my_id = None
current_room = None
window = None
instruction_turtle = None
running = False
players = {}
latest_state = {}
local_player = None

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
    instructions.write("Waiting for room...", align="center", font=("Arial", 12, "normal"))
    instruction_turtle = instructions


keys = {
    "w": False,
    "a": False,
    "s": False,
    "d": False
}

def press_w(): 
    keys["w"] = True
    #print("W pressed")

def release_w(): 
    keys["w"] = False
    #print("W released")

def press_a(): 
    keys["a"] = True
    #print("A pressed")

def release_a(): 
    keys["a"] = False
    #print("A released")

def press_s(): 
    keys["s"] = True
    #print("S pressed")

def release_s(): 
    keys["s"] = False
    #print("S released")

def press_d(): 
    keys["d"] = True
    #print("D pressed")

def release_d(): 
    keys["d"] = False
    #print("D released")

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
    window.ontimer(prompt_for_room, 100)


def prompt_for_room():
    """Ask the user which room to join"""
    try:
        root = window.getcanvas().winfo_toplevel()
        room_name = simpledialog.askstring(
            "Join Game Room", 
            "Enter room name:",
            parent=root
        )
        
        if room_name:
            join_game_room(room_name.strip())
        else:
            # User cancelled
            quit_game()
    except Exception as e:
        print(f"Error in prompt_for_room: {e}")
        # Fallback: ask through console
        room_name = input("Enter room name: ")
        if room_name:
            join_game_room(room_name.strip())
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
    global current_room, instruction_turtle, local_player, players
    current_room = data["room"]
    player_count = data["players"]
    
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
    global latest_state
    latest_state = data

    # Remove players that are no longer in the state
    for pid in list(players.keys()):
        if pid not in data:
            players[pid].turt.hideturtle()
            del players[pid]


def render_loop():
    if not running:
        return
    
    if my_id is not None and latest_state and current_room is not None:

        for player_id, p in latest_state.items():

            # own player
            if player_id == my_id:
                t = local_player
            else:
                if player_id not in players:
                    players[player_id] = player()
                    players[player_id].turt.color("red")  # Other players are red
                t = players[player_id]

            t.turt.goto(p["x"], p["y"])

            if p["vx"] != 0 or p["vy"] != 0:
                angle = math.degrees(math.atan2(p["vy"], p["vx"]))
                t.turt.setheading(angle)

    window.update()
    window.ontimer(render_loop, 16)

 
def send_input():
    if not running:
        return
    
    if sio.connected and current_room is not None:
        sio.emit("input", keys.copy())

    window.ontimer(send_input, 50)

    
def connect_to_server():
    """Connect to the server"""
    try:
        if len(sys.argv) <= 1:
            sio.connect("http://localhost:5555")
        else: 
            sio.connect(sys.argv[1])
    except socketio.exceptions.ConnectionError:
        if window:
            window.bye()
        messagebox.showerror("Connection Error", "Couldn't connect to server")
        menu.go_to_menu()


def run_game():
    init_game()
    connect_to_server()
    turtle.mainloop()
    
if __name__=="__main__":
    run_game()