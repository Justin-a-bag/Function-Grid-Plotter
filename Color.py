from __future__ import annotations 
import math

from Equation import Equation
class Color:
  """
  A wrapper class that maps values to colors
  """
  red: Equation
  green: Equation
  blue: Equation

  def __init__(self, red: Equation, green: Equation, blue: Equation):
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
    return (int(self.red.evaluate(zval,0)),int(self.green.evaluate(zval,0)),int(self.blue.evaluate(zval,0)))

