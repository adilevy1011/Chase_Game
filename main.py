import turtle
import keyboard
import tkinter as tk
import sys
from bot import bot
import math
import random

import pygame

window = turtle.Screen()
window.title("Chase Game")
window.tracer(0)
#window.setup(width=1.0, height=1.0)
window.bgcolor("white")
screen_width = window.window_width()-15
screen_height = window.window_height()-15
left   = -screen_width / 2 
right  =  screen_width / 2 -10
bottom = -screen_height / 2 + 10
top    =  screen_height / 2
tur = turtle.Turtle()
tur.penup()


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
    
    turX,turY = tur.pos()
    #=====MOVEMENT==================================================================================================================
    vx = 0
    vy = 0
    
    acc = 2
    friction = 0.9
    
    dx = 0
    dy = 0

    
    if keyboard.is_pressed('w') or keyboard.is_pressed('W'):
        dy += 1
    if keyboard.is_pressed('s'):
        dy -= 1
    if keyboard.is_pressed('a'):
        dx -= 1
    if keyboard.is_pressed('d'):
        dx += 1

    length = math.hypot(dx, dy)

    if length != 0:
        dx /= length
        dy /= length
    vx += dx*acc
    vy += dy*acc
    
    vx *= friction
    vy *= friction
    x, y = tur.pos()
    if x > right or x < left or y < bottom or y > top:
        if x > right:
            tur.setx(x-1)
        elif x < left:
            tur.setx(x+1)
        if y < bottom:
            tur.sety(y+1)
        elif y > top:
            tur.sety(y-1)
        
    else:
        tur.goto(x + vx, y + vy)

    if vx != 0 or vy != 0:
        angle = math.degrees(math.atan2(vy, vx))
        tur.seth(angle)
    
    #=====================================================================================================================

    for bt in bots:
        bt.step(turX,turY,screen_height,screen_width)
        bx,by = bt.turt.pos()
        if bt.rage and get_distance(bx,by,x,y) < 5:
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

    
        
        
        





