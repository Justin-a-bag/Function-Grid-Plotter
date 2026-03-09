#Hi guys uh so idk exactly what can and should be here so uh
#so we have everything pygame here
# I suppose we also put like the list of equations and colors and all that jazz in here too?
# And also like we look through and draw stuff in here too? 
# So the Draw() function gets put here?
#we're also gonna have to loop through all the points in here too
#Yeah this file is gonna have a lot of stuff
import pygame
from __future__ import annotations
from Equation import Equation
from Color import Color
from Boundary import Boundary

DRAW_MIN_X:int
DRAW_MAX_X:int
DRAW_MIN_Y:int
DRAW_MAX_Y:int


def render_grid(drawFunc:Equation, color = Color(), boundary = Boundary(), xpoints:list,ypoints:list):

    
    
    for x in range(len(xpoints)):
        for y in range(len(ypoints)):
            if boundary.inBounds(xpoints[x],ypoints[y]):
                squarecolor=color.getColorTuple(drawFunc.evaluate(xpoints[x],ypoints[y]))
                #this drawing function is a hallucination, and isn't actually how ti implement it
                #it's a template for when someone actually makes the drawing thing in pygame but this is the math to draw stuff
                g.draw(DRAW_MIN_X+x*((DRAW_MAX_X-DRAW_MIN_X)/len(xpoints)),DRAW_MIN_Y+y*((DRAW_MAX_Y-DRAW_MIN_Y)/len(ypoints)),squarecolor)
    #this is the grid renderer, you'll need to add other things
