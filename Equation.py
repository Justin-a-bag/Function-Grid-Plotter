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

    def tokenize(eq: str) -> list:
        """
        Reads the equation string from left to right, grouping characters
        into 'tokens' based on their type.
        this allows us to then turn these individual tokens into the tree.
        """

        tokens = []
        i = 0
        # when taking in latex, convert all the latex stuff into standard
        # also i didn't account stuff that takes in multiple inputs in separate brackets so we might need to adjust this tokenizer

        equation = eq.replace('{', '(').replace('}', ')').replace(' ', '')

        while i < len(equation):
            char = equation[i]

            # Numbers and decimals
            if char.isdigit() or char == '.':
                unit = ""
                while i < len(equation) and (equation[i].isdigit() or equation[i] == '.'):
                    unit += equation[i]
                    i += 1
                tokens.append(unit)
                # since i has already been incremented we can just leave it like this

            # Handle LaTeX/Functions (starts with \ or is a word)
            # \\ is just '\'
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
            elif char in "+-*/^()":
                tokens.append(char)
                i += 1

            else:
                # skip bad symbols
                i += 1

        return tokens

    def __init__(self, infix_string: str):
        # guys guys femtanyl reference
        tokenized_input = self.tokenize(infix_string)

        # 1. Tokenize -> 2. Shunting-Yard -> 3. Stack-based Build
        PRECEDENCE = {
            '+': (1, 2), '-': (1, 2),
            '*': (2, 2), '/': (2, 2),
            '^': (3, 2),
            'sin': (4, 1), 'cos': (4, 1), 'tan': (4, 1),
            'log': (4, 2), 'ln': (4, 1)
        }

        output_stack = []  # This stores our completed Tree Nodes
        operator_stack = []  # This stores operators that are waiting for their children

        def apply_operator():
            """Pops an operator and its required children to create a sub-tree."""
            op = operator_stack.pop()
            num_args = PRECEDENCE[op][1]

            # Pop children in reverse order (since stacks are Last-In-First-Out)
            children = []
            for _ in range(num_args):
                children.append(output_stack.pop())
            children.reverse()

            # Create a new branch and put it back on the output
            output_stack.append(Node(op, children))

        for token in tokenized_input:
            # STEP 1: If it's a Number, make it a leaf and push to output
            if token.replace('.', '', 1).isdigit():
                output_stack.append(Node(float(token)))

            # STEP 2: If it's x or y, make it a variable leaf
            elif token in ('x', 'y'):
                output_stack.append(Node(token))

            # STEP 3: Handle Parentheses
            elif token == '(':
                operator_stack.append(token)

            elif token == ')':
                # Solve everything inside the brackets
                while operator_stack and operator_stack[-1] != '(':
                    apply_operator()
                operator_stack.pop()  # Remove the '('

            # STEP 4: Handle Operators/Functions
            elif token in PRECEDENCE:
                # While the operator at the top of the stack is "stronger" than current token,
                # we must solve that one first.
                while (operator_stack and operator_stack[-1] != '(' and PRECEDENCE[operator_stack[-1]][0] >=
                       PRECEDENCE[token][0]):
                    apply_operator()
                operator_stack.append(token)

            # STEP 5: Final Cleanup
            # Solve any remaining operators in the stack
        while operator_stack:
            apply_operator()

        # The very last item on the output stack is the Root of our tree
        return output_stack[0]

    def evaluate(self, x: float, y: float) -> float:
        # this is the tree traversal step; the entire thing should return a float
        # evaluate the trees on the upper levels then evaluate this bottom node you get the point
        return self.tree.evaluate(x, y)

class Node:
    # op is either a string (the operation) or a value (a number or x or y)
    op: str
    children: list

    def __init__(self, op: str, children = None):
        self.op = op
        # children must be an ordered list
        self.children = children if children is not None else []

    def evaluate(self, x, y):
        # Evaluate children first
        vals = [c.evaluate(x, y) for c in self.children]

        if self.op == 'nan':
            # not a number error
            return 'nan'
        if self.op == 'invalid':
            # invalid input error
            return 'invalid'

        if isinstance(self.op, float):
            return float(self.op)
        if self.op == '':
            return 0.0
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
        # grammar isn't too important in this step since we can make the grammar whatever we want
        return 'invalid'


