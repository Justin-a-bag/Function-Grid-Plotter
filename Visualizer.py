from __future__ import annotations  # MUST be at the very top of the file
import pygame
import sys

# Import your custom classes
from Equation import Equation
from Color import Color
from Boundary import Boundary

# Define screen and drawing boundaries
#when making the thing these will be changed
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

                pygame.draw.rect(screen, squarecolor, (screen_x, screen_y, cell_w, cell_h))


if __name__ == "__main__":
    # --- 1. PYGAME SETUP ---
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("eeg")


    #Everything below this is my sample code: you will need to remove this
    #this is what stuff looks like before you render it
    # --- 2. MATH SETUP ---
    # Create the equation. Try changing this to "sin(x) + cos(y)"!
    eq = Equation("arctan(2sin(-2x-y/8+cos(3y-x-sin(cos(sin( sin(x*y) + x )+x-y+arctan(y)))))+(x^2+y^2/14)/3-100/(x^2+y^2)+2.71828^(-4-y))")#
    r=Equation("255((x-(cos(3.7(x+0.8))/3))/2.8+1.28)")
    g=Equation("255(sin(1.5(x+1.5708))/2.8+0.5)")
    b=Equation("255(2.71828^(-(3(x+0.99))^2)/3-x/9+0.1)")
    print(eq.size())
    print(r.size())
    print(g.size())
    print(b.size())
    my_color = Color(r,g,b)
    my_boundary = Boundary()

    # Generate the coordinate grid (e.g., from -10 to 10)
    # Using a 100x100 resolution for the bare minimum test
    #Grid resolution
    GRID_RESOLUTION = 100
    MATH_MIN, MATH_MAX = -15.0, 15.0
    # This creates a list of evenly spaced numbers from MATH_MIN to MATH_MAX
    step = (MATH_MAX - MATH_MIN) / GRID_RESOLUTION
    x_coords = [MATH_MIN + i * step for i in range(GRID_RESOLUTION)]
    y_coords = [MATH_MIN + j * step for j in range(GRID_RESOLUTION)]

    #rendering time
    # --- 3. RENDER ONCE ---
    screen.fill((0, 0, 0))  # Fill background with black
    
    print("Rendering grid... this might take a second for complex equations.")
    #now it draws the thing
    #loop through once for each drawn function
    render_grid(screen, eq, my_color, my_boundary, x_coords, y_coords)
    # Pushes the drawing to the actual monitor
    pygame.display.flip()
    
    print("Done!")

    # --- 4. MAIN EVENT LOOP ---
    # This keeps the window open until you click the red 'X'
    #This part will need to be adjusted
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

    pygame.quit()
    sys.exit()
