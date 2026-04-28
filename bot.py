import turtle
import random 
import math
import time
from sprite import sprite
class bot(sprite):
    CALM_SPEED = 1.5
    RAGE_SPEED = 3
    def __init__(self, id):
        super().__init__()
        self.ID = id
        self.turt.color("grey")
        self.rage = False
        self.angle = random.uniform(0, 360)
        self.turn_speed = 2
        self.speed = self.CALM_SPEED
        self.time_of_rage = time.time()
        self.time_wait = random.randint(1,15)

    def randomize_shape(self):
        colors = ["blue", "green", "purple", "orange", "yellow"]
        shapes = ["arrow", "classic", "triangle", "turtle"]
        self.turt.color(random.choice(colors))
        self.turt.shape(random.choice(shapes))
    
    def step(self, X: float, Y:float,screen_height,screen_width):
        if self.rage: 
            angle = super().find_angle_to(X,Y)
            self.turt.left(angle)
            self.turt.forward(self.speed)
        else:
            self.move(screen_height,screen_width)
        self.update()
    
    def move(self,screen_height,screen_width):
        
        x, y = self.turt.pos()
        
        x = max(-screen_width/2, min(screen_width/2, x))
        y = max(-screen_height/2, min(screen_height/2, y))
        
        
        if x <= -screen_width/2 or x >= screen_width/2 or y >= screen_height/2 or y <= -screen_height/2:
            if x <= -screen_width/2 or x >= screen_width/2:
                self.angle = 180 -self.angle
            if y >= screen_height/2 or y <= -screen_height/2:
                self.angle = -self.angle
        else: self.angle += random.uniform(-self.turn_speed, self.turn_speed)
        
        rad = math.radians(self.angle)

        self.vx = math.cos(rad) * self.speed
        self.vy = math.sin(rad) * self.speed

        
        self.turt.seth(self.angle)
        self.turt.goto(x + self.vx, y + self.vy)
        
    def rage_on(self):
        self.rage = True
        self.turt.color('red')
        self.speed = self.RAGE_SPEED
        self.time_of_rage = time.time()
        self.time_wait = random.randint(1,15)

    
    def rage_off(self):
        self.rage = False
        self.turt.color('grey')
        self.speed = self.CALM_SPEED
        self.time_of_rage = time.time()
        self.time_wait = random.randint(1,15)
    
    def update(self):
        if self.rage and time.time() - self.time_of_rage > self.time_wait:
            self.rage_off()
        elif not self.rage and time.time()- self.time_of_rage > self.time_wait:
            self.rage_on() #add update method in main
    


        
        
            
    
        
    
        
        
    
        
        
    
        