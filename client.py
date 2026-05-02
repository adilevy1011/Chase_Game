# client.py
import socketio
import math
from player import player
import sys
import turtle
from tkinter import messagebox, simpledialog
import tkinter as tk
import menu
import threading
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
already_joined = False
previous_player_count = 0
state_lock = threading.Lock()
room_name = None

# Global variable for room selection
available_rooms = []
room_already_selected = False  # Track if room was selected in GUI callbacks

# Flags to track if loops are running
render_loop_running = False
send_input_running = False

def init_game():
    """Initialize the game state (window already created in run_game)"""
    global window, instruction_turtle, players, latest_state, running, local_player
    
    # Window was already created in run_game, just initialize game state
    window.clearscreen()
    window.tracer(0)
    window.update()
    window.getcanvas().focus()

    players = {}
    latest_state = {}
    running = True

    
    instructions = turtle.Turtle()
    instructions.hideturtle()
    instructions.speed(0)
    instructions.penup()
    instructions.goto(0, 280)
    instructions.write("Hold on, waiting for room...", align="center", font=("Arial", 12, "normal"))
    instructions._is_instruction = True
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


def initialize_game(data):
    """Initialize the game graphics and controls (called from main thread)"""
    global current_room, instruction_turtle, local_player, players, previous_player_count
    global render_loop_running, send_input_running, window, running
    
    player_count = data["players"]
    
    # Create the turtle window on first join (fallback)
    if window is None:
        init_game()
    
    # Only clear screen on first join, not on reconnection
    first_join = not render_loop_running
    
    if first_join:
        running = True
        
        # 2. NOW REVEAL the game window since we are in a room!
        root = window.getcanvas().winfo_toplevel()
        root.deiconify() 
        
        # Update the window title and size
        window.title(f"Chase Game Multiplayer - Room: {data['room']}")
        window.setup(width=800, height=600)
        
        window.clearscreen()
        window.tracer(0)
        
        # Reset players dictionary only on first join
        players = {}
        
        # Create new local player only on first join
        local_player = player()
        local_player.turt.color("blue")
      
    # Create instruction turtle if it doesn't exist
    if instruction_turtle is None:
        instructions = turtle.Turtle()
        instructions.hideturtle()
        instructions.speed(0)
        instructions.penup()
        instructions._is_instruction = True
        instruction_turtle = instructions
    
    # Update room info
    if instruction_turtle:
        instruction_turtle.clear()
        instruction_turtle.goto(0, 280)
        instruction_turtle.write(
            f"Room: {data['room']} | Players: {player_count}", 
            align="center", 
            font=("Arial", 12, "normal")
        )
    
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
    
    # Start the game loops if this is the first join
    if first_join:
        render_loop_running = True
        send_input_running = True
        render_loop()  # Start the render loop
        send_input()   # Start the input loop


# Connection management
connection_state = {
    "connected": False,
    "reconnecting": False,
    "last_room": None,
    "reconnect_attempts": 0,
    "max_reconnect_attempts": 5,
    "reconnect_delay": 1000,  # Start with 1 second
    "max_reconnect_delay": 30000  # Max 30 seconds
}

@sio.event
def connect():
    print("Connected to server")
    connection_state["connected"] = True
    connection_state["reconnecting"] = False
    connection_state["reconnect_attempts"] = 0
    connection_state["reconnect_delay"] = 1000

    # If already joined, rejoin the room
    if already_joined:
        print("Already in a room, rejoining...")
        rejoin_room()

@sio.event
def disconnect():
    """Handle disconnection with automatic reconnection"""
    print("Disconnected from server")
    connection_state["connected"] = False

    # Clear game state
    global players, latest_state, my_id, render_loop_running, send_input_running, already_joined
    players = {}
    latest_state = {}
    my_id = None
    render_loop_running = False
    send_input_running = False
    already_joined = False  # Reset join status on disconnect

    # Store current room for reconnection
    if current_room:
        connection_state["last_room"] = current_room

    # Start reconnection if we haven't exceeded max attempts
    if connection_state["reconnect_attempts"] < connection_state["max_reconnect_attempts"]:
        connection_state["reconnecting"] = True
        connection_state["reconnect_attempts"] += 1

        print(f"Attempting to reconnect... (attempt {connection_state['reconnect_attempts']}/{connection_state['max_reconnect_attempts']})")

        # Schedule reconnection with exponential backoff
        if window:
            try:
                window.ontimer(attempt_reconnect, connection_state["reconnect_delay"])
            except:
                pass

        # Increase delay for next attempt (exponential backoff)
        connection_state["reconnect_delay"] = min(
            connection_state["reconnect_delay"] * 2,
            connection_state["max_reconnect_delay"]
        )

def attempt_reconnect():
    """Attempt to reconnect to the server"""
    if connection_state["reconnecting"]:
        try:
            url = "http://147.182.235.138.nip.io:80"  # Default localhost
            print(f"Reconnecting to server...")
            sio.connect(
                url,
                transports=['polling'],
                wait_timeout=30
            )
            print("Reconnected successfully!")
        except Exception as e:
            print(f"Reconnection failed: {e}")

@sio.event
def rooms_list(data):
    """Update the list of available rooms"""
    global available_rooms
    available_rooms = data
    print(f"Received rooms list: {available_rooms}")


def create_room_selection_screen():
    """Display a window to select or create a room"""
    global room_name, available_rooms, window
    
    # Fix 3: Attach to existing root to prevent Tkinter window corruption
    try:
        root = tk.Toplevel(window.getcanvas().winfo_toplevel())
    except:
        root = tk.Tk() # Fallback only if window isn't accessible
        
    root.title("Room Selection")
    root.geometry("400x500")
    # ... (Keep the rest of your UI building code exactly the same below this)
    root.resizable(True, True)
    
    # Store after callback ID so we can cancel it
    after_id = [None]  # Use list to allow modification in nested function
    
    def cleanup_window():
        """Cancel any pending callbacks and destroy window"""
        if after_id[0]:
            root.after_cancel(after_id[0])
            after_id[0] = None
        root.destroy()
    
    # Handle window close button
    root.protocol("WM_DELETE_WINDOW", cleanup_window)
    
    # Title label
    title_label = tk.Label(root, text="Select a Room or Create a New One", font=("Arial", 14, "bold"))
    title_label.pack(pady=10)
    
    # Create a Canvas and Scrollbar for scrollable content
    canvas = tk.Canvas(root, bg="white")
    scrollbar = tk.Scrollbar(root, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas, bg="white")
    
    # Configure the Canvas to scroll the Frame
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    # Pack the Canvas and Scrollbar
    canvas.pack(side="left", fill="both", expand=True, padx=5, pady=5)
    scrollbar.pack(side="right", fill="y")
    
    # Create room button
    create_btn_frame = tk.Frame(scrollable_frame)
    create_btn_frame.pack(pady=5, padx=5, fill="x")
    
    tk.Button(
        create_btn_frame, 
        text="+ Create New Room", 
        command=lambda: on_create_room(root, after_id),
        width=25,
        bg="#4CAF50",
        fg="white",
        font=("Arial", 10, "bold")
    ).pack(fill="x")
    
    # Separator
    tk.Frame(scrollable_frame, height=2, bg="gray").pack(fill="x", padx=5, pady=5)
    
    # Label for available rooms
    rooms_label = tk.Label(scrollable_frame, text="Active Rooms:", font=("Arial", 11, "bold"), bg="white")
    rooms_label.pack(padx=5, pady=5)
    
    # Create a container frame for dynamic room content
    rooms_container = tk.Frame(scrollable_frame, bg="white")
    rooms_container.pack(fill="both", expand=True, padx=5)
    
    # Request rooms list from server
    sio.emit("get_rooms")
    
    # Function to refresh room buttons
    def refresh_rooms():
        global available_rooms
        
        # Check if window still exists
        if not root.winfo_exists():
            after_id[0] = None
            return
        
        try:
            # Clear all children in the rooms container
            for widget in rooms_container.winfo_children():
                widget.destroy()
            
            if not available_rooms:
                no_rooms_label = tk.Label(rooms_container, text="No active rooms", font=("Arial", 10), bg="white", fg="gray")
                no_rooms_label.pack(padx=5, pady=10)
            else:
                for room_info in available_rooms:
                    room_name_str = room_info["name"]
                    player_count = room_info["players"]
                    
                    # Create a button for each room
                    room_btn = tk.Button(
                        rooms_container,
                        text=f"{room_name_str} ({player_count} player{'s' if player_count != 1 else ''})",
                        command=lambda n=room_name_str: on_room_selected(n, root, after_id),
                        width=25,
                        bg="#2196F3",
                        fg="white",
                        font=("Arial", 10)
                    )
                    room_btn.pack(pady=3, padx=5, fill="x")
            
            # Schedule refresh after 1 second (only if window still exists)
            if root.winfo_exists():
                after_id[0] = root.after(1000, refresh_rooms)
            else:
                after_id[0] = None
        except tk.TclError:
            # Window was destroyed while updating, cancel refresh
            after_id[0] = None
    
    # Start the refresh cycle
    refresh_rooms()
    
    # Use wait_window instead of mainloop to avoid blocking
    root.wait_window()

def on_room_selected(selected_room_name, window, after_id):
    """Handle room selection"""
    global room_name, room_already_selected
    room_name = selected_room_name
    room_already_selected = True  # Mark that room was selected in GUI
    print(f"Selected room: {room_name}")
    # Cancel any pending callbacks and close window
    if after_id[0]:
        window.after_cancel(after_id[0])
        after_id[0] = None
    window.destroy()
    # Join the room automatically
    join_game_room(room_name)

def on_create_room(window, after_id):
    """Handle creating a new room"""
    global room_name, room_already_selected
    new_room_name = simpledialog.askstring(
        "Create Room",
        "Enter a name for the new room:",
        parent=window
    )
    if new_room_name and new_room_name.strip():
        room_name = new_room_name.strip()
        room_already_selected = True  # Mark that room was selected in GUI
        print(f"Created new room: {room_name}")
        # Cancel any pending callbacks and close window
        if after_id[0]:
            window.after_cancel(after_id[0])
            after_id[0] = None
        window.destroy()
        # Join the room automatically
        join_game_room(room_name)

def prompt_for_room():
    """Ask the user which room to join"""
    global already_joined
    global room_name
    global room_already_selected  # Track if room was selected in GUI
    
    # Reset the flag
    room_already_selected = False
    
    try:
        create_room_selection_screen()
        
        # Only join if room wasn't already selected in the GUI callbacks
        if room_name and not room_already_selected:
            join_game_room(room_name.strip())
            already_joined = True
        elif not room_name:
            # User cancelled room selection, return to menu
            menu.go_to_menu()
    except Exception as e:
        print(f"Error in prompt_for_room: {e}")
        # Fallback to simple input
        room_name = input("Enter room name: ")
        if room_name:
            join_game_room(room_name.strip())
            already_joined = True
        else:
            menu.go_to_menu()


def rejoin_room():
    """Rejoin the current room after reconnection"""
    room_to_join = current_room or connection_state.get("last_room")
    if room_to_join:
        print(f"Rejoining room: {room_to_join}")
        sio.emit("join_game", {"room": room_to_join})
    else:
        print("No room to rejoin")
        # Fall back to room selection
        prompt_for_room()


def join_game_room(room_name):
    """Request to join a specific game room"""
    global current_room
    current_room = room_name
    print(f"Attempting to join room: {room_name}")
    
    sio.emit("join_game", {"room": room_name})
    # Game window will be created in initialize_game() when server confirms

@sio.event
def your_id(data):
    global my_id
    my_id = data
    print("My ID:", my_id)

@sio.event
def joined_game(data):
    """Confirmation that we joined a room"""
    global current_room, previous_player_count
    
    current_room = data["room"]
    player_count = data["players"]
    previous_player_count = player_count
    
    print(f"Successfully joined room: {data['room']}")
    
    # Force UI initialization onto the main Tkinter thread
    def setup_ui():
        global render_loop_running, send_input_running
        initialize_game(data)
        
        try:
            window.getcanvas().focus_set()
            window.listen()
        except:
            pass
        
        if not render_loop_running:
            render_loop_running = True
            render_loop()
        
        if not send_input_running:
            send_input_running = True
            send_input()

    if window:
        window.ontimer(setup_ui, 0)

@sio.event
def state(data):
    global latest_state, instruction_turtle, current_room, previous_player_count
    
    with state_lock:
        latest_state = data.copy()
        # Removed the hideturtle() loop from here—UI updates must stay out of background threads!

    current_player_count = len(data)
    if current_player_count != previous_player_count and instruction_turtle and current_room:
        previous_player_count = current_player_count
        
        def update_instructions():
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
                
        if window:
            window.ontimer(update_instructions, 0)


def render_loop():
    if not running or not render_loop_running:
        return
    
    try:
        with state_lock:
            current_state = latest_state.copy()
        
        if my_id is not None and current_state and current_room is not None:
            # Render existing/new players
            for player_id, p in current_state.items():
                try:
                    # Fix 2: Force string conversion to ensure IDs match
                    if str(player_id) == str(my_id):
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

            # Cleanup disconnected players safely on the main thread
            for pid in list(players.keys()):
                if pid not in current_state:
                    try:
                        players[pid].turt.hideturtle()
                        del players[pid]
                    except:
                        pass

        window.update()
    except Exception as e:
        pass
    
    if window and render_loop_running:
        try:
            window.ontimer(render_loop, 16)
        except:
            pass

 
def send_input():
    if not running or not send_input_running:
        return
    
    if sio.connected and current_room is not None:
        sio.emit("input", keys.copy())

    # Schedule next input safely
    if window and send_input_running:
        try:
            window.ontimer(send_input, 30)
        except:
            pass

    
def connect_to_server(tunnel_address):
    """Connect to the server with improved error handling"""
    global connection_state

    # Reset connection state
    connection_state = {
        "connected": False,
        "reconnecting": False,
        "last_room": None,
        "reconnect_attempts": 0,
        "max_reconnect_attempts": 5,
        "reconnect_delay": 1000,
        "max_reconnect_delay": 30000
    }

    try:
        url = tunnel_address if tunnel_address else "http://147.182.235.138.nip.io:80"
        print(f"Attempting to connect to: {url}")

        sio.connect(
            url,
            transports=['polling'],
            wait_timeout=30
        )

        print("Connected successfully!")

    except socketio.exceptions.ConnectionError as e:
        print(f"Connection error: {e}")
        if window:
            window.bye()
        messagebox.showerror("Connection Error", f"Couldn't connect to server: {e}")
        menu.go_to_menu()
    except Exception as e:
        print(f"Unexpected connection error: {e}")
        if window:
            window.bye()
        messagebox.showerror("Connection Error", f"Unexpected error: {e}")
        menu.go_to_menu()


def run_game(tunnel_address):
    # Reset join status for new session
    global already_joined, window, local_player
    already_joined = False
    
    # 1. Create the turtle window but IMMEDIATELY hide it
    window = turtle.Screen()
    window.getcanvas().winfo_toplevel().withdraw() # Hides the blank screen
    
    window.tracer(0)
    
    # Set up key bindings early (they will become active when revealed)
    window.onkeypress(press_w, "w")
    window.onkeyrelease(release_w, "w")
    window.onkeypress(press_a, "a")
    window.onkeyrelease(release_a, "a")
    window.onkeypress(press_s, "s")
    window.onkeyrelease(release_s, "s")
    window.onkeypress(press_d, "d")
    window.onkeyrelease(release_d, "d")
    window.onkeypress(quit_game, "Escape")
    
    # Connect to server
    connect_to_server(tunnel_address)
    
    # After connection, ask for room selection
    # (Because the main window is hidden, ONLY the room selector will show up)
    prompt_for_room()
    
    # Start turtle mainloop
    turtle.mainloop()
    
if __name__=="__main__":
    run_game()
