from __future__ import annotations  # MUST be at the very top of the file
import pygame
import sys

# Import your custom classes
from Equation import Equation
from Color import Color
from Boundary import Boundary

# Define screen and drawing boundaries
WIDTH, HEIGHT = 800, 800
DRAW_MIN_X, DRAW_MAX_X = 0, WIDTH
DRAW_MIN_Y, DRAW_MAX_Y = 0, HEIGHT


def render_grid(screen: pygame.Surface, drawFunc: Equation, color: Color, boundary: Boundary, xpoints: list[float],
                ypoints: list[float]):
    """
    Evaluates the equation at every math coordinate and draws the corresponding color block to the screen.
    """
    # Calculate how wide and tall each grid square should be on the screen
    cell_w = (DRAW_MAX_X - DRAW_MIN_X) / len(xpoints)
    cell_h = (DRAW_MAX_Y - DRAW_MIN_Y) / len(ypoints)

    for i in range(len(xpoints)):
        for j in range(len(ypoints)):
            math_x = xpoints[i]
            math_y = ypoints[j]

            # 1. Check if the point is within the user's defined mathematical boundary
            if boundary.inBounds(math_x, math_y):

                # 2. Evaluate the equation
                z = drawFunc.evaluate(math_x, math_y)


                # 3. Get the color from your Color class
                squarecolor = color.getColorTuple(z)

                # 4. Calculate where this rectangle actually goes on the computer screen
                screen_x = DRAW_MIN_X + i * cell_w
                # Invert the Y axis so standard math (+y is up) matches Pygame (+y is down)
                screen_y = DRAW_MAX_Y - ((j + 1) * cell_h)

                # 5. Draw it!

                pygame.draw.rect(screen, squarecolor, (screen_x, screen_y, max(1,cell_w), max(1,cell_h)))

if __name__ == "__main__":
    # --- 1. PYGAME SETUP ---
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Jingwei Render Engine")

    # --- 2. MATH SETUP ---
    # Create the equation. Try changing this to "sin(x) + cos(y)"!
    eq = Equation("2\sin\left(-2x-\frac{1}{8}y+\cos\left(3y-x-\sin\left(\cos\left(\sin\left(\sin\left(x*y\right)+x\right)\right)+x-y+arccot\left(x\right)\arctan\left(y\right)\right)\right)\right)+\frac{\left(x^{2}+\frac{y^{2}}{14}\right)}{3}-\left(\frac{100}{x^{2}+y^{2}}\right)+e^{-4-y}")  #
    r = Equation("255((x-(cos(3.7(x+0.8))/3))/2.8+1.28)")
    g = Equation("255(sin(1.5(x+pi/2))/2.8+0.5)")
    b = Equation("255(e^(-(3(x+0.99))^2)/3-x/9+0.1)")
    eq2 = Equation("arctan(2sin(-2x-y/8+cos(3y-x-sin(cos(sin( sin(x*y) + x )+x-y+arctan(y)))))+\frac{\left(x^{2}+\frac(y^2,14)+0\right)}{3}-100/(x^2+y^2)+2.71828^(-4-y))")  #
    my_color = Color(r,g,b)
    my_boundary = Boundary(Equation("arctan(2sin(-2x-y/8+cos(3y-x-sin(cos(sin( sin(x*y) + x )+x-y+arctan(y)))))+\frac{\left(x^{2}+\frac(y^2,14)+0\right)}{3}-100/(x^2+y^2)+2.71828^(-4-y))-1.45"),True)
    my_boundary = Boundary()

    # Generate the coordinate grid (e.g., from -10 to 10)
    # Using a 100x100 resolution for the bare minimum test
    GRID_RESOLUTION = 400
    MATH_MIN, MATH_MAX = -15.0, 15.0

    # This creates a list of evenly spaced numbers from MATH_MIN to MATH_MAX
    step = (MATH_MAX - MATH_MIN) / GRID_RESOLUTION
    x_coords = [MATH_MIN + 1 + i * step for i in range(GRID_RESOLUTION)]
    y_coords = [MATH_MIN + j * step for j in range(GRID_RESOLUTION)]

    x_coords2 = [MATH_MIN - 12 + i * step for i in range(GRID_RESOLUTION)]
    y_coords2 = [MATH_MIN + j * step for j in range(GRID_RESOLUTION)]

    # --- 3. RENDER ONCE ---
    screen.fill((0, 0, 0))  # Fill background with black
    print("Rendering grid...")
    renderingtime = GRID_RESOLUTION ** 2 * (eq.size() + r.size() + g.size() + b.size()) / 1000000
    print("estimated rendering time: "+str(renderingtime)+" seconds")
    print("Note: the power of your device will affect runtime speeds.")

    render_grid(screen, eq2, my_color, my_boundary, x_coords, y_coords)
    #render_grid(screen, eq2, my_color, my_boundary, x_coords2, y_coords2)
      # Pushes the drawing to the actual monitor
    pygame.display.flip()

    print("Done!")

    # --- 4. MAIN EVENT LOOP ---
    # This keeps the window open until you click the red 'X'
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

    pygame.quit()
    sys.exit()
