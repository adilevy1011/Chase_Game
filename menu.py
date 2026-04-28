import tkinter as tk
import main
import client
import sys
import os
from tkinter import messagebox, simpledialog


def start_game():
    global menu_root
    menu_root.destroy()
    main.start_game()

def start_multiplayer():
    global menu_root
    messagebox.showinfo("Server connection", "To run on local host type: http://localhost:5555 or simply press cancel.\nOtherwise, use tunnel address for server.")
    tunnel_address = simpledialog.askstring(
            "Tunnel address", 
            "Enter tunnel address:",
            parent=menu_root
        )
    menu_root.destroy()
    client.init_game()
    client.run_game(tunnel_address)
    
def go_to_menu():
    python = sys.executable
    os.execl(python, python, "menu.py")
def run_menu():
    global menu_root
    
    menu_root = tk.Tk()
    welcome_label = tk.Label(menu_root,text="Welcome to Arrow Chase",font=("Roboto",40,"bold"))
    welcome_label.place(x=90,y=50,width=700,height=100)
    menu_root.title("Menu")
    menu_root.geometry("800x600")
    start_game_button = tk.Button(menu_root,text="Play single player", command=start_game,font=("Roboto",12,"bold"))
    start_game_button.place(x=320,y=300,width=150,height=25)
    start_multiplayer_button = tk.Button(menu_root,text="Play multiplayer",command=start_multiplayer,font=("Roboto",12,"bold"))
    start_multiplayer_button.place(x=320,y=350,width=150,height=25)
    quit_button = tk.Button(menu_root,text="Quit",command=sys.exit,font=("Roboto",12,"bold"))
    quit_button.place(x=320,y=400,width=150,height=20)
    menu_root.mainloop()


if __name__ == "__main__":
    run_menu()

