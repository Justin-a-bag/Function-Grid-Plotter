# write your imports here
from __future__ import annotations  # Fixes the "Unresolved Reference" for Node
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
        # \u and \x are danger characters so be careful

        REPLACEMENTS = {
            '{': '(', '}': ')','(-': '(0-',
        '\a': '`a', '\b': '`b', '\f': '`f', '\n': '`n', '\r': '`r', '\t': '`t', '\v': '`v', '\s': '`s', '\l': '`l',
            '\left(':'(','\right)':')'
        }

        equation = eq.replace('}{',',').replace(' ','')
        for x in REPLACEMENTS:
            equation = equation.replace(x, REPLACEMENTS[x])
        if equation.startswith('-'):
            equation = '0' + equation
        while i < len(equation):
            char = equation[i]

            # Numbers and decimals
            # if it sees a number then it reads the full number and makes it a token
            if char.isdigit() or char == '.':
                unit = ""
                while i < len(equation) and (equation[i].isdigit() or equation[i] == '.'):
                    unit += equation[i]
                    i += 1
                tokens.append(unit)
                # since i has already been incremented we can just leave it like this

            # Handle LaTeX/Functions (starts with \ or is a word)
            # \\ is just '\'
            # if it sees a word or smth it makes it a token
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
                # allows for input of \left( and \right)
                if unit != 'left' and unit != 'right':
                    tokens.append(unit)

            # 4. Handle Single Symbols (+, -, *, /, ^, (, ))
            # if it sees a symbol immediately turn it into a token
            # Note: this implementation might need to be changed if you want to allow ** as an input for ^ or smth like that
            elif char in "+-*/^(),":
                tokens.append(char)
                i += 1

            else:
                # skip bad symbols
                i += 1

        # making it so that you can do stuff like 2x instead of 2*x
        final_tokens = []
        for j in range(len(tokens)):
            # runs through the full list and adds tokens to the list
            final_tokens.append(tokens[j])
            if j < len(tokens) - 1:
                curr_token = tokens[j]
                next_token = tokens[j + 1]
                # If the token that was just added is a digit/x/y/) and the next digit is a letter/(
                # there are other cases of this but i'm too lazy to implement that
                if (curr_token.replace('.', '', 1).isdigit() or curr_token in ('x', 'y', ')', 'pi', 'e')) and (
                        next_token.isalpha() or next_token in ('x', 'y', '(', 'pi', 'e')):
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
            '^': (3, 2), '%': (2, 2),
            'exp': (4, 1), 'frac': (2, 2),
            'sin': (4, 1), 'cos': (4, 1), 'tan': (4, 1), 'sec': (4, 1), 'csc': (4, 1), 'cot': (4, 1),
            'arcsin': (4, 1), 'arccos': (4, 1), 'arctan': (4, 1), 'arcsec': (4, 1), 'arccsc': (4, 1), 'arccot': (4, 1),
            'sinh': (4, 1), 'cosh': (4, 1), 'tanh': (4, 1), 'sech': (4, 1), 'csch': (4, 1), 'coth': (4, 1),
            'arcsinh': (4, 1), 'arccosh': (4, 1), 'arctanh': (4, 1), 'arcsech': (4, 1), 'arccsch': (4, 1),
            'arccoth': (4, 1),
            'log': (4, 2), 'ln': (4, 1),
            'sqrt': (4, 1), 'cbrt': (4, 1),
            'abs': (4, 1), 'sign': (4, 1),
            'floor': (4, 1), 'ceil': (4, 1), 'round': (4, 1),
            'min': (4, 2), 'max': (4, 2), 'clamp': (4, 3),
            'pi': (5, 0), 'e': (5, 0)

        }
        REPLACEABLE = {
            'cdot': '*', 'times': '*'
        }
        potato = False
        output_stack = []  # This stores our completed Tree Nodes
        operator_stack = []  # This stores operators that are waiting for their children

        """
        For instance, 2x+y-3y/x^2 becomes 2*x+y-3*y/x^2
        this then gets turned into 2 x * y + 3 - y * x 2 ^ /
        which then gets squeeshed in the right way into (((((2 x *) y +) 3 -) y *) (x 2 ^) /)
        and that's what the tree looks like basically
        """

        # putting the def inside init because i want it to see the variables and stuff
        # i am describing everything like i'm an israeli soldier in Gaza
        def apply_operator():
            """Pops an operator and its required children to create a sub-tree."""
            try:
                op = operator_stack.pop()
                num_args = PRECEDENCE[op][1]

                # Kill children in reverse order starting with the youngest (since stacks are Last-In-First-Out)

                children = []
                for _ in range(num_args):
                    # take the children from their old family, put them in a new family
                    children.append(output_stack.pop())
                # make it so that the eldest is arranged first, since it's easier to abduct them younger
                children.reverse()

                # Create a new family and put it back on the output to fend for themselves
                output_stack.append(Node(op, children))
            except IndexError:
                potato = True
                output_stack.append(Node('invalid', []))

        for token in tokenized_input:
            # remember, all children go in the output stack pile
            # STEP 1: If it's a Number, it's a child
            if token.replace('.', '', 1).isdigit():
                output_stack.append(Node(float(token)))

            # STEP 2: If it's x or y, don't let its size deceive you, it's still a child
            elif token in ('x', 'y'):
                output_stack.append(Node(token))

            # STEP 3: Handle Parentheses
            # parentheses aren't human, they're put in a separate stack
            elif token == '(':
                operator_stack.append(token)

            # okay but this guy is special because if this guy appears you gotta kill a bunch of people
            elif token == ')':
                # Loop through and add combine families until you're done
                while operator_stack and operator_stack[-1] != '(':
                    apply_operator()
                operator_stack.pop()  # Remove the '('
            elif token == ',':
                # marks the end of a section
                #finish all operations before this one
                while operator_stack and operator_stack[-1] != '(':
                    apply_operator()

            # STEP 4: Handle Operators/Functions
            # everything here deals with operators/functions
            elif token in PRECEDENCE:
                # there are special types of people we gotta look out for
                # While the operator at the top of the stack is "stronger" than current token,
                # we must solve that one first.
                while (operator_stack and operator_stack[-1] != '(' and PRECEDENCE[operator_stack[-1]][0] >=
                       PRECEDENCE[token][0]):
                    apply_operator()
                # add the operator to the operator stack
                # we do this because functions are in prefix (polish) notation (+ a b) rather than infix notation (a + b)
                # so we need to get all the functions first
                # in theory this means we don't even need brackets to declare a function
                operator_stack.append(token)

            elif token in REPLACEABLE:
                # you see, these people aren't citizens so we have to look at their birth certificates to find their real identities
                # Same as above, only it looks at REPLACEABLE to find the correct symbol
                while (operator_stack and operator_stack[-1] != '(' and PRECEDENCE[operator_stack[-1]][0] >=
                       PRECEDENCE[REPLACEABLE[token]][0]):
                    apply_operator()
                operator_stack.append(REPLACEABLE[token])
            if potato:
                self.tree = Node("potato", [])
                return

            # STEP 5: Final Cleanup
            # kill any surviving residents
            # Solve any remaining operators in the stack
        while operator_stack:
            apply_operator()
            if potato:
                self.tree = Node("potato", [])
                return

        # The very last item on the output stack is the Root of our tree
        self.tree = output_stack[0]

    def evaluate(self, x: float, y: float) -> float:
        # this is the tree traversal step; the entire thing should return a float
        # evaluate the trees on the upper levels then evaluate this bottom node you get the point
        # eliminates possibility of returning a complex value
        result = self.tree.evaluate(x, y)
        return result if not isinstance(result, complex) else 'nan'

    # returns size of the tree (number of nodes)
    def size(self):
        return self.tree.size()


class Node:
    # op is either a string (the operation) or a value (a number or x or y)
    op: str
    children: list

    def __init__(self, op: str, children=None):
        self.op = op
        # children must be an ordered list
        self.children = children if children is not None else []

    def size(self):
        # Quality of life method: returns size of the tree
        return 1 + sum([c.size() for c in self.children])

    def evaluate(self, x, y):
        # Evaluate children first
        vals = [c.evaluate(x, y) for c in self.children]

        if self.op == 'invalid' or any(c == 'invalid' for c in vals):
            # invalid input error
            return 'invalid'
        if self.op == 'nan' or any(c == 'nan' for c in vals):
            # not a number error
            return 'nan'

        # Every time you add a function to PRECEDENCE add its implementation down here
        # base cases
        if isinstance(self.op, float):
            return float(self.op)
        # this is a surprise tool that will help us later
        if isinstance(self.op, complex):
            return complex(self.op)
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

        # simple operations
        if self.op == '+':
            return vals[0] + vals[1]
        if self.op == '-':
            return vals[0] - vals[1]
        if self.op == '*':
            return vals[0] * vals[1]
        if self.op == '/':
            return vals[0] / vals[1] if vals[1] != 0 else 'nan'
        # ive decided that we will allow complex values when returning this thing because i'm lazy
        if self.op == '^':
            return vals[0] ** vals[1]
        if self.op == '%':
            return vals[0] % vals[1] if vals[1] > 0 else 'nan'

        # variations on transcendentals
        if self.op == 'exp':
            return math.e ** vals[0]
        if self.op == 'frac':
            return vals[0]/vals[1] if vals[1] != 0 else 'nan'
        if self.op == 'ln':
            return math.log(vals[0]) if vals[0] > 0 else 'nan'
        if self.op == 'log':
            return math.log(vals[1], vals[0]) if (vals[0] > 0 and vals[0]!=1 and vals[1]>0) else 'nan'
        if self.op == 'sqrt':
            return math.sqrt(vals[0]) if vals[0] >= 0 else 'nan'
        if self.op == 'cbrt':
            return vals[0] ** (1 / 3)

        # unrestricted trig
        if self.op == 'sin':
            return math.sin(vals[0])
        if self.op == 'cos':
            return math.cos(vals[0])
        if self.op == 'arctan':
            return math.atan(vals[0])
        if self.op == 'arccot':
            return math.pi / 2 - math.atan(vals[0])

        # trig with bad values
        if self.op == 'cot':
            return math.tan(math.pi / 2 - vals[0]) if math.sin(vals[0]) != 0.0 else 'nan'
        if self.op == 'tan':
            return math.tan(vals[0]) if math.cos(vals[0]) != 0.0 else 'nan'
        if self.op == 'csc':
            return 1 / math.sin(vals[0]) if math.sin(vals[0]) != 0.0 else 'nan'
        if self.op == 'sec':
            return 1 / math.cos(vals[0]) if math.cos(vals[0]) != 0.0 else 'nan'
        if self.op == 'arcsin':
            return math.asin(vals[0]) if x ** 2 <= 1 else 'nan'
        if self.op == 'arccos':
            return math.acos(vals[0]) if x ** 2 <= 1 else 'nan'
        if self.op == 'arcsec':
            return math.acos(1 / vals[0]) if x ** 2 >= 1 else 'nan'
        if self.op == 'arccsc':
            return math.asin(1 / vals[0]) if x ** 2 >= 1 else 'nan'

        # unrestricted hyperbolic trig
        if self.op == 'sinh':
            return math.sinh(vals[0])
        if self.op == 'cosh':
            return math.cosh(vals[0])
        if self.op == 'tanh':
            return math.tanh(vals[0])
        if self.op == 'sech':
            return 1 / math.cosh(vals[0])
        if self.op == 'arcsinh':
            return math.asinh(vals[0])

        # hyperbolic trig with bad values
        if self.op == 'csch':
            return 1 / math.sin(vals[0]) if vals[0] != 0.0 else 'nan'
        if self.op == 'coth':
            return 1 / math.tan(math.pi / 2) if vals[0] != 0.0 else 'nan'
        if self.op == 'arccosh':
            return math.acosh(vals[0]) if x >= 1 else 'nan'
        if self.op == 'arcsech':
            return math.acosh(1 / vals[0]) if x > 1 else 'nan'
        if self.op == 'arccsch':
            return math.asin(1 / vals[0]) if x ** 2 != 1 else 'nan'
        if self.op == 'arctanh':
            return math.atanh(vals[0]) if x ** 2 < 1 else 'nan'
        if self.op == 'arccoth':
            return math.atanh(1 / vals[0]) if x ** 2 > 1 else 'nan'

        # number theory
        if self.op == 'abs':
            return abs(vals[0])
        if self.op == 'sign':
            return -1 if vals[0] < 0 else 1 if vals[0] > 0 else 0
        if self.op == 'floor':
            return float(math.floor(vals[0]))
        if self.op == 'ceil':
            return float(math.ceil(vals[0]))
        if self.op == 'round':
            return float(round(vals[0]))
        if self.op == 'min':
            return min(vals[0], vals[1])
        if self.op == 'max':
            return max(vals[0], vals[1])
        if self.op == 'clamp':
            return min(max(vals[0], vals[1]), vals[2])

        # Add other things after here
        # grammar isn't too important in this step since we can make the grammar whatever we want
        return 'invalid'
if __name__ == "__main__":
    eq=Equation("log{2,x}")
    print(eq.evaluate(1,0))
