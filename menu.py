import tkinter as tk
import main
import client
import sys
import os

def start_game():
    global menu_root
    menu_root.destroy()
    main.start_game()

def start_multiplayer():
    global menu_root
    menu_root.destroy()
    client.init_game()
    client.run_game()
    
def go_to_menu():
    python = sys.executable
    os.execl(python, python, "menu.py")
def run_menu():
    global menu_root
    menu_root = tk.Tk()
    menu_root.title("Menu")
    menu_root.geometry("800x600")
    start_game_button = tk.Button(menu_root,text="Play single player", command=start_game)
    start_game_button.pack(expand=True)
    start_multiplayer_button = tk.Button(menu_root,text="Play multiplayer",command=start_multiplayer)
    start_multiplayer_button.pack(expand=True)
    quit_button = tk.Button(menu_root,text="Quit",command=sys.exit)
    quit_button.pack(expand=True)
    menu_root.mainloop()

if __name__ == "__main__":
    run_menu()

