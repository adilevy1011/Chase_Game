# client.py
import socketio
import math
from player import player
import sys
import turtle
from tkinter import messagebox
import menu

sio = socketio.Client()

my_id = None

def init_game():
    global window
    window = turtle.Screen()
    window.title("Chase Game Multiplayer")
    window.tracer(0)
    window.onkeypress(press_w, "w")
    window.onkeyrelease(release_w, "w")

    window.onkeypress(press_a, "a")
    window.onkeyrelease(release_a, "a")

    window.onkeypress(press_s, "s")
    window.onkeyrelease(release_s, "s")

    window.onkeypress(press_d, "d")
    window.onkeyrelease(release_d, "d")

    window.onkeypress(quit_game, "Escape")

    window.listen()
    global players
    players = {}
    global latest_state
    latest_state = {}

    global running
    running = True

    global local_player
    local_player = player()
    local_player.turt.color("blue")



keys = {
    "w": False,
    "a": False,
    "s": False,
    "d": False
}
def press_w(): keys["w"] = True

def release_w(): keys["w"] = False

def press_a(): keys["a"] = True

def release_a(): keys["a"] = False

def press_s(): keys["s"] = True

def release_s(): keys["s"] = False

def press_d(): keys["d"] = True

def release_d(): keys["d"] = False

def quit_game():
    global running
    global window
    print("Disconnecting...")
    
    running = False
    try:
        sio.disconnect()
    except:
        pass
    #window.bye()
    menu.go_to_menu()



@sio.event
def connect():
    print("Connected to server")
    send_input()
    render_loop()



@sio.event
def your_id(data):
    global my_id
    my_id = data
    print("My ID:", my_id)

@sio.event
def state(data):
    global latest_state
    latest_state = data

    # only maintain existence (NO rendering here anymore)
    for pid in list(players.keys()):
        if pid not in data:
            players[pid].turt.hideturtle()
            del players[pid]


def render_loop():
    if not running:
        return
    if my_id is not None and latest_state:

        for player_id, p in latest_state.items():

            # own player
            if player_id == my_id:
                t = local_player
            else:
                if player_id not in players:
                    players[player_id] = player()
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
    if sio.connected:
        sio.emit("input", keys.copy())

    window.ontimer(send_input, 50)
    
def connect_to_server():
    # connect to server
    try:
        if len(sys.argv) <= 1:
            sio.connect("http://localhost:5555")
        else: 
            sio.connect(sys.argv[1])
    except socketio.exceptions.ConnectionError:
        window.bye()
        messagebox.showerror("Connection Error", "Couldn't connect to server")
        menu.go_to_menu()
def run_game():
    connect_to_server()
    turtle.mainloop()
    
if __name__=="__main__":
    run_game()