import tkinter as tk
import main
import client
import sys
import os
from tkinter import messagebox, simpledialog
import pyautogui

def start_game():
    global menu_root
    menu_root.destroy()
    main.start_game()

def start_multiplayer():
    global menu_root
    connect_method = pyautogui.confirm("How would you like to connect to the server", buttons=["Public Server", "Cloudflare","Local Host"])
    if connect_method == "Cloudflare":
        #messagebox.showinfo("Server connection", "To run on local host type: http://localhost:5555.\nOtherwise, use tunnel address for server.")
        tunnel_address = simpledialog.askstring(
                "Tunnel address", 
                "Enter tunnel address:",
                parent=menu_root
            )
        menu_root.destroy()
        client.run_game(tunnel_address)
    elif connect_method == "Public Server":
        menu_root.destroy()
        client.run_game(tunnel_address=None)
    elif connect_method == "Local Host":
        menu_root.destroy()
        client.run_game("http://localhost:5555")

    
def go_to_menu():
    python = sys.executable
    os.execl(python, python, "menu.py")
def run_menu():
    global menu_root
    
    menu_root = tk.Tk()
    welcome_label = tk.Label(menu_root,text="Welcome to Arrow Chase",font=("Roboto",35,"bold"))
    welcome_label.place(x=50,y=50,width=750,height=100)
    menu_root.title("Menu")
    menu_root.geometry("800x600")
    start_game_button = tk.Button(menu_root,text="Play single player", command=start_game,font=("Roboto",15,"bold"))
    start_game_button.place(x=300,y=300,width=220,height=30)
    start_multiplayer_button = tk.Button(menu_root,text="Play multiplayer",command=start_multiplayer,font=("Roboto",15,"bold"))
    start_multiplayer_button.place(x=300,y=355,width=220,height=30)
    quit_button = tk.Button(menu_root,text="Quit",command=sys.exit,font=("Roboto",15,"bold"))
    quit_button.place(x=300,y=405,width=220,height=30)
    menu_root.mainloop()


if __name__ == "__main__":
    run_menu()

