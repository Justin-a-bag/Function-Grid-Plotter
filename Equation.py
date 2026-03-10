# write your imports here
from __future__ import annotations # Fixes the "Unresolved Reference" for Node
import math
class Equation:
    # represents one equation f(x,y) = z
    # contains one tree
    # evaluate(self,x:float, y:float)->float:
    # only returns value for a single point
    # as_string(self)->string:

    tree: Node

    def tokenize(self, eq: str) -> list:
        """
        Reads the equation string from left to right, grouping characters
        into 'tokens' based on their type.
        this allows us to then turn these individual tokens into the tree.
        """

        tokens = []
        i = 0
        # when taking in latex, convert all the latex stuff into standard
        # also i didn't account stuff that takes in multiple inputs in separate brackets so we might need to adjust this tokenizer

        equation = eq.replace('{', '(').replace('}', ')').replace(' ', '').replace('(-','(0-')
        if equation.startswith('-'):
            equation = '0' + equation
        while i < len(equation):
            char = equation[i]

            # Numbers and decimals
            #if it sees a number then it reads the full number and makes it a token
            if char.isdigit() or char == '.':
                unit = ""
                while i < len(equation) and (equation[i].isdigit() or equation[i] == '.'):
                    unit += equation[i]
                    i += 1
                tokens.append(unit)
                # since i has already been incremented we can just leave it like this

            # Handle LaTeX/Functions (starts with \ or is a word)
            # \\ is just '\'
            #if it sees a word or smth it makes it a token
            elif char.isalpha() or char == '\\':
                unit = ""
                # If it starts with \, keep the backslash but keep going
                if char == '\\':
                    unit += char
                    i += 1
                # Keep grabbing letters until we hit a symbol or number
                while i < len(equation) and equation[i].isalpha():
                    unit += equation[i]
                    i += 1

                # Clean up: remove the leading backslash because we don't need it
                unit = unit.lstrip('\\')
                tokens.append(unit)

            # 4. Handle Single Symbols (+, -, *, /, ^, (, ))
            # if it sees a symbol immediately turn it into a token
            #Note: this implementation might need to be changed if you want to allow ** as an input for ^ or smth like that
            elif char in "+-*/^()":
                tokens.append(char)
                i += 1

            else:
                # skip bad symbols
                i += 1

        #making it so that you can do stuff like 2x instead of 2*x
        final_tokens = []
        for j in range(len(tokens)):
            #runs through the full list and adds tokens to the list
            final_tokens.append(tokens[j])
            if j < len(tokens) - 1:
                curr_token = tokens[j]
                next_token = tokens[j+1]
                # If the token that was just added is a digit/x/y/) and the next digit is a letter/(
                #there are other cases of this but i'm too lazy to implement that
                if (curr_token.replace('.', '', 1).isdigit() or curr_token in ('x', 'y', ')')) and (next_token.isalpha() or next_token == '('):
                    final_tokens.append('*')

        return final_tokens

    def __init__(self, infix_string: str):
        # guys guys femtanyl reference
        tokenized_input = self.tokenize(infix_string)

        # 1. Tokenize -> 2. Shunting-Yard -> 3. Stack-based Build


        """
        Hi guys if you're reading this that means you're working on the project
        yeah uh this is the thing that takes in input and allows you to do stuff with it i guess
        Precedence is all the stuff that involves bedmas and also input requirements
        replaceable is meant moreso for alternative ways of writing the same function multiple times
        for instance, in desmos copying '*' becomes '\cdot'
        """
        PRECEDENCE = {
            '+': (1, 2), '-': (1, 2),
            '*': (2, 2), '/': (2, 2),
            '^': (3, 2),
            'sin': (4, 1), 'cos': (4, 1), 'tan': (4, 1), 'sec': (4, 1), 'csc': (4, 1), 'cot': (4, 1),
            'arcsin': (4, 1), 'arccos': (4, 1), 'arctan': (4, 1), 'arcsec': (4, 1), 'arccsc': (4, 1), 'arccot': (4, 1),
            'log': (4, 1), 'ln': (4, 1),
            'sqrt': (4, 1), 
            'pi': (5, 0), 'e': (5, 0)

        }
        REPLACEABLE = {
            'cdot':'*', 'times':'*'
        }

        output_stack = []  # This stores our completed Tree Nodes
        operator_stack = []  # This stores operators that are waiting for their children

        """
        For instance, 2x+y-3y/x^2 becomes 2*x+y-3*y/x^2
        this then gets turned into 2 x * y + 3 - y * x 2 ^ /
        which then gets squeeshed in the right way into (((((2 x *) y +) 3 -) y *) (x 2 ^) /)
        and that's what the tree looks like basically
        """


        #putting the def inside init because i want it to see the variables and stuff
        #i am describing everything like i'm an israeli soldier in Gaza
        def apply_operator():
            """Pops an operator and its required children to create a sub-tree."""
            op = operator_stack.pop()
            num_args = PRECEDENCE[op][1]

            # Kill children in reverse order starting with the youngest (since stacks are Last-In-First-Out)
            
            children = []
            for _ in range(num_args):
                #take the children from their old family, put them in a new family
                children.append(output_stack.pop())
            #make it so that the eldest is arranged first, since it's easier to abduct them younger
            children.reverse()

            # Create a new family and put it back on the output to fend for themselves
            output_stack.append(Node(op, children))

        for token in tokenized_input:
            #remember, all children go in the output stack pile
            # STEP 1: If it's a Number, it's a child
            if token.replace('.', '', 1).isdigit():
                output_stack.append(Node(float(token)))

            # STEP 2: If it's x or y, don't let its size deceive you, it's still a child
            elif token in ('x', 'y'):
                output_stack.append(Node(token))

            # STEP 3: Handle Parentheses
            #parentheses aren't human, they're put in a separate stack
            elif token == '(':
                operator_stack.append(token)

            #okay but this guy is special because if this guy appears you gotta kill a bunch of people
            elif token == ')':
                # Loop through and add combine families until you're done
                while operator_stack and operator_stack[-1] != '(':
                    apply_operator()
                operator_stack.pop()  # Remove the '('

            # STEP 4: Handle Operators/Functions
            #everything here deals with operators/functions
            elif token in PRECEDENCE:
                #there are special types of people we gotta look out for
                # While the operator at the top of the stack is "stronger" than current token,
                # we must solve that one first.
                while (operator_stack and operator_stack[-1] != '(' and PRECEDENCE[operator_stack[-1]][0] >=
                       PRECEDENCE[token][0]):
                    apply_operator()
                operator_stack.append(token)
                
            elif token in REPLACEABLE:
                #you see, these people aren't citizens so we have to look at their birth certificates to find their real identities
                # Same as above, only it looks at REPLACEABLE to find the correct symbol
                while (operator_stack and operator_stack[-1] != '(' and PRECEDENCE[operator_stack[-1]][0] >=
                       PRECEDENCE[REPLACEABLE[token]][0]):
                    apply_operator()
                operator_stack.append(REPLACEABLE[token])
                

            # STEP 5: Final Cleanup
            #kill any surviving residents
            # Solve any remaining operators in the stack
        while operator_stack:
            apply_operator()

        # The very last item on the output stack is the Root of our tree
        self.tree = output_stack[0]

    def evaluate(self, x: float, y: float) -> float:
        # this is the tree traversal step; the entire thing should return a float
        # evaluate the trees on the upper levels then evaluate this bottom node you get the point
        return self.tree.evaluate(x, y)
    #returns size of the tree (number of nodes)
    def size(self):
        return self.tree.size()

class Node:
    # op is either a string (the operation) or a value (a number or x or y)
    op: str
    children: list

    def __init__(self, op: str, children = None):
        self.op = op
        # children must be an ordered list
        self.children = children if children is not None else []
    
    def size(self):
        #Quality of life method: returns size of the tree
        return 1 + sum([c.size() for c in self.children])

    def evaluate(self, x, y):
        # Evaluate children first
        vals = [c.evaluate(x, y) for c in self.children]

        if self.op == 'invalid' or any(c=='invalid' for c in vals):
            # invalid input error
            return 'invalid'
        if self.op == 'nan' or any(c=='nan' for c in vals):
            # not a number error
            return 'nan'


        #Every time you add a function to PRECEDENCE add its implementation down here
        if isinstance(self.op, float):
            return float(self.op)
        if self.op == '':
            return 0.0
        if self.op == 'x':
            return x
        if self.op == 'y':
            return y
        if self.op == 'pi':
            return math.pi
        if self.op == 'e':
            return math.e
        if self.op == '+':
            return vals[0] + vals[1]
        if self.op == '-' or self.op == 'frac':
            return vals[0] - vals[1]
        if self.op == '*':
            return vals[0] * vals[1]
        if self.op == '/':
            return vals[0] / vals[1] if vals[1] != 0 else 'nan'
        if self.op == '^':
            return vals[0] ** vals[1]
        
        if self.op == 'sin':
            return math.sin(vals[0])
        if self.op == 'cos':
            return math.cos(vals[0])
        
        if self.op == 'arctan':
            return math.atan(vals[0])
        if self.op == 'arccot':
            return math.pi/2-math.atan(vals[0])
        if self.op == 'ln':
            return math.log(vals[0])if vals[0]>0 else 'nan'
        if self.op == 'sqrt':
            return math.sqrt(vals[0]) if vals[0]>=0 else 'nan'
        # Add other things after here
        # grammar isn't too important in this step since we can make the grammar whatever we want
        return 'invalid'


