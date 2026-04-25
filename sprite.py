
import turtle
import math
class sprite:
    
    def __init__(self):
        self.turt = turtle.Turtle()
        self.turt.penup()
        
    def find_angle_to(self, other_posX: float, other_posY:float,offset=0):
        xcor,ycor = self.turt.pos()
        dx = other_posX - xcor
        dy = other_posY - ycor
        
        target_angle = math.degrees(math.atan2(dy, dx))
        current_angle = (self.turt.heading() + offset) % 360
        
        angle = target_angle - current_angle
        angle = (angle + 180) % 360 - 180
        
        return angle
    def find_angle_to_player_view(self, x, y):
        angle = self.find_angle_to(x, y)
        return (angle + 180) % 360 - 180