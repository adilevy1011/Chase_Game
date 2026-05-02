import turtle
import tkinter as tk
import sys
from bot import bot
import math
import random
from player import player
import os
import menu

#==========
bots : list[bot] = []
#===========

BOTS_ON = True
def init_game():
    
    global pen 
    pen = turtle.Turtle()
    global player 
    player = player()  
    
    global bot_count
    bot_count = 0
    
    global window 
    window = turtle.Screen()
    window.title("Chase Game")
    window.tracer(0)
    #window.setup(width=1.0, height=1.0)
    window.bgcolor("white")
    global screen_width 
    screen_width = window.window_width()-15 #640 - 15 = 625
    global screen_height 
    screen_height = window.window_height()-15 # 480 - 15 = 465
    global left   
    left = -screen_width / 2 # = -312
    global right 
    right =  screen_width / 2 - 5 # 307
    global bottom 
    bottom = -screen_height / 2 + 10 # -222
    global top    
    top =  screen_height / 2 #232
    
    pen.hideturtle()
    pen.penup()

    window.listen()
    window.onkey(spawn_bot, "Up")
    
    # Add these for player movement
    window.onkeypress(lambda: set_move("w", True), "w")
    window.onkeyrelease(lambda: set_move("w", False), "w")
    window.onkeypress(lambda: set_move("s", True), "s")
    window.onkeyrelease(lambda: set_move("s", False), "s")
    window.onkeypress(lambda: set_move("a", True), "a")
    window.onkeyrelease(lambda: set_move("a", False), "a")
    window.onkeypress(lambda: set_move("d", True), "d")
    window.onkeyrelease(lambda: set_move("d", False), "d")
    window.onkeypress(lambda: set_move("Escape", True), "Escape")
    window.onkeyrelease(lambda: set_move("Escape", False), "Escape")
    # Position the label
    pen.goto(left, top-10)
    if BOTS_ON:
        window.listen()
        window.onkey(spawn_bot, "Up")
    
pressed_keys = {"w": False, "s": False, "a": False, "d": False,"Escape":False}

def set_move(key, state):
    pressed_keys[key] = state
def add_gameover_screen():
    root = tk.Tk()
    root.title("Game Over")
    root.geometry("800x600")
    root.config(bg='red')
    label = tk.Label(root,text = "Game Over",font=("Arial", 40, "bold"),bg='red')
    label.place(x=200,y=200,width=400,height=100)
    killerLabel = tk.Label(root,text=f"Killed by bot number {killer.ID}",font=("Arial", 15),bg='red')
    killerLabel.pack(expand=True)
    restart_btn = tk.Button(text="Restart game",command=restart_game)
    restart_btn.place(x=325,y=450,width=100,height=35)
    qt_btn = tk.Button(text="Back to menu",command=menu.go_to_menu)
    qt_btn.place(x=325,y=500,width=100,height=35)
    root.mainloop()
def restart_game():
    python = sys.executable
    os.execl(python, python, "main.py")

def spawn_bot():
    global bot_count
    bot_count = bot_count + 1
    b = bot(bot_count)
    bots.append(b)
    b.turt.goto(random.randint(-300,300),random.randint(-300,300))
#When player DIES and NOT when Escape key is pressed 
def terminate_game():
    window.bye()
    add_gameover_screen()
def get_distance(x1,y1,x2,y2):
    return math.sqrt(math.pow((x1-x2),2) + math.pow(y1-y2,2))
def game_loop():
    #=====PLAYER==================================================================================================================
    turX,turY = player.turt.pos()
    if pressed_keys['w']:
        player.dy += 1
    if pressed_keys['s']:
        player.dy -= 1
    if pressed_keys['a']:
        player.dx -= 1
    if pressed_keys['d']:
        player.dx += 1

    player.update(right,left,bottom,top)
    #=====================================================================================================================

    
    for index,bt in enumerate(bots):
        bt.step(turX,turY,screen_height,screen_width)
        bx,by = bt.turt.pos()
        if bt.rage and get_distance(bx,by,turX,turY) < 5:
            angle = player.find_angle_to_player_view(bx,by)
            #angle = (angle + 180) % 360 - 180
            print("angle:", angle, "heading:", player.turt.heading())
            if -90 < angle < 90:
                bt.turt.hideturtle()
                bots.pop(index)
            else:
                global killer
                killer = bt
                terminate_game()
            
        
            
    #Close program
    if pressed_keys['Escape']:
        window.bye()
        menu.go_to_menu()
        
        
    # Write the label text
    pen.clear()
    pen.write(f"number of bots: {len(bots)}",  font=("Verdana", 9))
    
    window.update()
    window.ontimer(game_loop, 16) 
    
def start_game():
    init_game()
    game_loop()
    turtle.mainloop()

if __name__ == "__main__":
    start_game()


    
        
        
        





