from __future__ import annotations

from Equation import Equation


class Boundary:
    """
    A boolean restriction condition that evaluates an Equation to check if a specific spatial coordinate falls inside or outside accepted bounds.
    """
    bounder: Equation
    checkSmaller: bool

    def __init__(self, boundary=Equation("1"), checksmaller=False):

        self.bounder = boundary
        self.checkSmaller = checksmaller

    def inBounds(self, x: float, y: float, angle_mode="potato", env: dict = None, depth=0) -> bool:
        """
        Calculates the equation at (x, y) and returns whether it satisfies the boundary condition.
        Returns True if (value >= 0) when checkSmaller is False.
        Returns True if (value <= 0) when checkSmaller is True.
        """
        squarevalue = float(self.bounder.evaluate(x, y, angle_mode, env, depth))
        if self.checkSmaller == False:
            return squarevalue >= 0
        else:
            return squarevalue <= 0

