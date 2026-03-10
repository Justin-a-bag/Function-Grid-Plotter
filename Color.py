from __future__ import annotations 
import math

from Equation import Equation
class Color:
  """
  A wrapper class that maps values to colors
  Improvements: changing the output for nan/invalid
  """
  red: Equation
  green: Equation
  blue: Equation

  def __init__(self, red = Equation("x"), green = Equation("x"), blue = Equation("x")):
    self.red=red
    self.green=green
    self.blue=blue
  def getColorTuple(self,zval:float)->tuple:
    """
    returns the color tuple that corresponds to the color at any specific location
    remember that color is a tuple of 3 integers representing rgb values
    since color drawing uses integers, cast the value to an integer (surely a 1 point drop in color doesn't actually matter riiigghhhttt?)
    Hey guys uh if you're reading this idk how we should scale the color values 
    can you guys decide if we should just drop immediately to 0/255 or use a 1-1 mapping system?
    also if we should check for absolute max/min values and scale values accordingly?
    """
    #doing it this way since we need to check the values of stuff
    rval,gval,bval=self.red.evaluate(zval,0),self.green.evaluate(zval,0),self.blue.evaluate(zval,0)

    #yeah fuck you for wanting to read the code
    if any(c==d for c in [rval,gval,bval] for d in ['invalid','nan']):
        #THIS SHOULD RETURN A BASE NULL VALUE
        #i'm using black as the base value but you can choose anything 
        #(i will note some color schemes don't allow black but thats the point lowkey)
        return (0,0,0)
    #final casting
    #fuck marry kill r value, g value, b value?
    return (int(rval),int(gval),int(bval))

