import turtle
import keyboard
import tkinter as tk
import sys
from bot import bot
import math
import random
from player import player
window = turtle.Screen()
window.title("Chase Game")
window.tracer(0)
#window.setup(width=1.0, height=1.0)
window.bgcolor("white")
screen_width = window.window_width()-15
screen_height = window.window_height()-15
left   = -screen_width / 2 
right  =  screen_width / 2 - 5
bottom = -screen_height / 2 + 10
top    =  screen_height / 2

player = player()

bots : list[bot] = []
        
def add_gameover_screen():
    root = tk.Tk()
    root.geometry("800x600")
    root.config(bg='red')
    label = tk.Label(root,text = "Game Over",font=("Arial", 40, "bold"),bg='red')
    label.place(x=200,y=200,width=400,height=100)
    qt_btn = tk.Button(text="Quit",command=sys.exit)
    qt_btn.place(x=350,y=500,width=50,height=35)
    root.mainloop()

def spawn_bot():
    b = bot()
    bots.append(b)
    b.turt.goto(random.randint(-300,300),random.randint(-300,300))
    
    

window.listen()
window.onkey(spawn_bot, "Up")

#When player DIES and NOT when Escape key is pressed 
def terminate_game():
    window.bye()
    add_gameover_screen()
def get_distance(x1,y1,x2,y2):
    return math.sqrt(math.pow((x1-x2),2) + math.pow(y1-y2,2))
def game_loop():
    
    
    #=====PLAYER==================================================================================================================
    turX,turY = player.turt.pos()
    if keyboard.is_pressed('w') or keyboard.is_pressed('W'):
        player.dy += 1
    if keyboard.is_pressed('s'):
        player.dy -= 1
    if keyboard.is_pressed('a'):
        player.dx -= 1
    if keyboard.is_pressed('d'):
        player.dx += 1

    player.update(right,left,bottom,top)
    #=====================================================================================================================

    for bt in bots:
        bt.step(turX,turY,screen_height,screen_width)
        bx,by = bt.turt.pos()
        if bt.rage and get_distance(bx,by,turX,turY) < 5:
            terminate_game()
            
    #Close program
    if keyboard.is_pressed('Escape'):
        game_on = False
        window.bye()
        sys.exit()
        
    
    window.update()
    window.ontimer(game_loop, 16) 
    



game_loop()
turtle.mainloop()

    
        
        
        





