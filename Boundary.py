from __future__ import annotations 
import math

from Equation import Equation
class Boundary:
  """
  A wrapper class that maps values to colors
  Improvements: can allow for the input of 2 functions to compare values between them (memory saving and maybe time saving?)
  Alterations for inclusive/exclusive check; restricting to a line
  """
  bounder: Equation
  checkSmaller: bool

  def __init__(self, boundary = Equation("1"), checkSmaller=False):
    self.boundary=boundary
    self.checkSmaller=checkSmaller
  def inBounds(self,x:float,y:float)->bool:
    """
    returns whether or not the x and y values are in bounds as specified by the boundary provided earlier
    """
    #i think the code is pretty readable just like look at it ig
    squarevalue=self.bounder.evaluate(x,y)
    #you guys can decide if we actually want an inclusive/exclusive check for squarevalue right now it's inclusive
    if self.checkSmaller==False:
      return squarevalue>=0
    else:
      return squarevalue<=0
      
      
