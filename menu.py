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
    welcome_label = tk.Label(menu_root,text="Welcome to Arrow Chase",font=("Times",40,"bold"))
    welcome_label.place(x=90,y=50,width=600,height=100)
    menu_root.title("Menu")
    menu_root.geometry("800x600")
    start_game_button = tk.Button(menu_root,text="Play single player", command=start_game)
    start_game_button.place(x=320,y=300,width=100,height=25)
    start_multiplayer_button = tk.Button(menu_root,text="Play multiplayer",command=start_multiplayer)
    start_multiplayer_button.place(x=320,y=350,width=100,height=25)
    quit_button = tk.Button(menu_root,text="Quit",command=sys.exit)
    quit_button.place(x=320,y=400,width=100,height=20)
    menu_root.mainloop()

if __name__ == "__main__":
    run_menu()

