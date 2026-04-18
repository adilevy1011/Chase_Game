import turtle
import math
class player:
    
    def __init__(self):
        self.turt = turtle.Turtle()
        self.turt.penup()
        self.vx = 0
        self.vy = 0
        
        self.acc = 1
        self.friction = 0.9
        
        self.dx = 0
        self.dy = 0
        
    def update(self,right,left,bottom,top):
        
       
        
        
        length = math.hypot(self.dx, self.dy)

        if length != 0:
            self.dx /= length
            self.dy /= length
        self.vx += self.dx*self.acc
        self.vy += self.dy*self.acc
        
        self.vx *= self.friction
        self.vy *= self.friction
        x, y = self.turt.pos()
        if x > right or x < left or y < bottom or y > top:
            if x > right:
                self.turt.setx(x-1)
            elif x < left:
                self.turt.setx(x+1)
            if y < bottom:
                self.turt.sety(y+1)
            elif y > top:
                self.turt.sety(y-1)
            
        else:
            self.turt.goto(x + self.vx, y + self.vy)

        if self.vx != 0 or self.vy != 0:
            angle = math.degrees(math.atan2(self.vy, self.vx))
            self.turt.seth(angle)
        
        # self.vx = 0
        # self.vy = 0
        
        self.dx = 0
        self.dy = 0
        