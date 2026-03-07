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
    def __init__(self, op: str, left: Equation, right: ExprNode = None):
        self.op = op
        self.left = left
        self.right = right

    def evaluate(self, x, y):
        # Implementation of math logic (e.g., if self.op == '+': ...)
        #evaluate part of a subtree
        

  
