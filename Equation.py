#write your imports here

class Equation:
  #represents one equation f(x,y) = z
  #contains one tree
  #evaluate(self,x:float, y:float)->float:
  #only returns value for a single point
  #as_string(self)->string:


  #this is chatgpted so you can change these implementations
  def __init__(infix_string: str):
    
    # 1. Tokenize -> 2. Shunting-Yard -> 3. Stack-based Build
    
    
  def evaluate(self, x: float, y: float) -> float:
      #this is the tree traversal step; the entire thing should return a float
      #evaluate the trees on the upper levels then evaluate this bottom node you get the point

  class OperatorNode(ExprNode):
    #op is either a string (the operation) or a value (a number or x or y)
    op: str
    children: list
    
    def __init__(self, op: str, children: list):
        self.op = op
        #children must be an ordered list
        self.children = children

    
    
    def evaluate(self, x, y):
        # Implementation of math logic (e.g., if self.op == '+': ...)
        #evaluate part of a subtree
        def evaluate(self, x, y):
        # Evaluate children first
        vals = [c.evaluate(x, y) for c in self.children]

        if self.op == 'nan':
          return 'nan'
        if self.op == 'invalid':
          return 'invalid'
      
        if c in '1234567890.-' for c in self.op: 
          return float(self.op)
        if self.op == 'x':
          return x
        if self.op == 'y':
          return y
        if self.op == '+': 
          return vals[0] + vals[1]
        if self.op == '-': 
          return vals[0] - vals[1]
        if self.op == '*': 
          return vals[0] * vals[1]
        if self.op == '/': 
          return vals[0] / vals[1] if vals[1] != 0 else 'nan'
        if self.op == '^': 
          return vals[0] ** vals[1]
        # Add other things after here
        #grammar isn't too important in this step since we can make the grammar whatever we want
        return 0.0

  
