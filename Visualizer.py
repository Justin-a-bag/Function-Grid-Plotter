from __future__ import annotations  # MUST be at the very top of the file
import pygame
import sys

# Import your custom classes
from Equation import Equation
from Color import Color
from Boundary import Boundary

# Define screen and drawing boundaries
WIDTH, HEIGHT = 1100, 800
DRAW_MIN_X, DRAW_MAX_X = 300, WIDTH
DRAW_MIN_Y, DRAW_MAX_Y = 0, HEIGHT
TEXTBOX_Y = 30
TEXTBOX_WIDTH, TEXTBOX_HEIGHT = 300, 50
TEXTBOX_COLOR = (210, 210, 210)
INDENT_COLOR = (TEXTBOX_COLOR[0]-30, TEXTBOX_COLOR[1]-30, TEXTBOX_COLOR[2]-30)
TB_INDT = 5
TABS_WIDTH, TABS_HEIGHT = 60, 50
PANELS = ['Functions', 'Colours', 'Restrictions', 'Draw', 'Settings']
current_panel = 'Functions'

#Stores which functions are at what locations
#grammar: ID, string

functionsList=[
    ("eq","arctan(2\sin\left(-2x-\frac{1}{8}y+\cos\left(3y-x-\sin\left(\cos\left(\sin\left(\sin\left(x*y\right)+x\right)\right)+x-y+arccot\left(x\right)\arctan\left(y\right)\right)\right)\right)+\frac{\left(x^{2}+\frac{y^{2}}{14}\right)}{3}-\left(\frac{100}{x^{2}+y^{2}}\right)+e^{-4-y})"),
    ("r","255((x-(cos(3.7(x+0.8))/3))/2.8+1.28)"),
    ("g","255(sin(1.5(x+pi/2))/2.8+0.5)"),
    ("b","255(e^(-(3(x+0.99))^2)/3-x/9+0.1)"),
    ("rest","1")
]
#direct map of all usable functions
#grammar: ID: list
functionsDict={}
#Stores which colors are at what locations
#Grammar: ID, red, green, blue
colorsList=[("my_color","r","g","b")]
#direct map of all usable colors
#Grammar: ID: color
colorsDict={}
#Stores which restrictions are at what locations
#Grammar: ID, restriction, greaterorlessthan
restrictionsList=[("rest","rest",False)]
#direct map of all usable restrictions
#grammar: ID, boundary class
restrictionsDict={}
#all inputted draw stuff
#Grammar: function ID, color, restriction
drawList=[("eq","my_color","rest")]
#List of all functions to draw
#A separate list outside of drawList to make sure everything is allowed
drawFinal=[]

# textbox object
class Textbox:
    """
    a textbox object to condense the information needed to create an iterable, mutable textbox
    """
    text: str
    rect: pygame.Rect
    color: pygame.Color
    active = bool

    def __init__(self, new_text: str, new_rect: pygame.Rect, new_color: pygame.Color):
        self.text = new_text
        self.rect = new_rect
        self.color = new_color

    def update_rect(self, new_y: int):
        if self.rect.y != new_y:
            self.rect.move(self.rect.x, new_y)

    def update_text(self, passed_ev: pygame.event.Event):
        if passed_ev.type == pygame.K_BACKSPACE:
            self.text = self.text[:-1]
        else:
            self.text += passed_ev.unicode

def update_functions() -> None:
    """
    takes the lists and makes sure that everything is working as intended
    """
    global functionsList
    global functionsDict
    global colorsList
    global colorsDict
    global restrictionsList
    global restrictionsDict
    global drawList
    global drawFinal
    functionsDict={}
    for x in functionsList:

        if x[0] not in functionsDict:

            functionTree=Equation(x[1])
            #note: this implementation means that you can have bad functions
            #this is accounted for in error checking but you will need to error flag check here
            functionsDict[x[0]]=functionTree
    colorsDict = {}
    for x in colorsList:

        if x[0] not in colorsDict:

            if all(x[c] in functionsDict for c in [1,2,3]):

                newColor = Color(functionsDict[x[1]],functionsDict[x[2]],functionsDict[x[3]])
                # note: this implementation means that you can have bad colors with bad functions
                # this is accounted for in error checking but you will need to error flag check here
                colorsDict[x[0]] = newColor
    restrictionsDict = {}
    for x in restrictionsList:
        if x[0] not in restrictionsDict:
            if x[1] in functionsDict:
                newRestriction = Boundary(functionsDict[x[1]],x[2])
                # note: this implementation means that you can have bad colors with bad functions
                # this is accounted for in error checking but you will need to error flag check here
                restrictionsDict[x[0]] = newRestriction
    drawFinal=[]
    for x in drawList:

        if x[0] in functionsDict and x[1] in colorsDict and x[2] in restrictionsDict:
            drawFinal.append((functionsDict[x[0]],colorsDict[x[1]],restrictionsDict[x[2]]))
    
def render_grid(screen: pygame.Surface, xpoints: list[float], ypoints: list[float]): #drawFunc: Equation, color: Color, boundary: Boundary,
    """
    Evaluates the equation at every math coordinate and draws the corresponding color block to the screen.
    """
    # Calculate how wide and tall each grid square should be on the screen

    cell_w = (DRAW_MAX_X - DRAW_MIN_X) / len(xpoints)
    cell_h = (DRAW_MAX_Y - DRAW_MIN_Y) / len(ypoints)
    #draw each square first
    for i in range(len(xpoints)):
        for j in range(len(ypoints)):
            math_x = xpoints[i]
            math_y = ypoints[j]
            #do this for every item in the list
            for curFunc in drawFinal:
                # 1. Check if the point is within the user's defined mathematical boundary
                if curFunc[2].inBounds(math_x, math_y):
                    # 2. Evaluate the equation
                    z = curFunc[0].evaluate(math_x, math_y)

                    # 3. Get the color from your Color class
                    squarecolor = curFunc[1].getColorTuple(z)

                    # 4. Calculate where this rectangle actually goes on the computer screen
                    screen_x = DRAW_MIN_X + i * cell_w
                    # Invert the Y axis so standard math (+y is up) matches Pygame (+y is down)
                    screen_y = DRAW_MAX_Y - ((j + 1) * cell_h)

                    # 5. Draw it!
                    if squarecolor != (-1, -1, -1):
                        pygame.draw.rect(screen, squarecolor, (screen_x, screen_y, max(1.0, cell_w), max(1.0, cell_h)))


def render_textboxes(scr: pygame.Surface, text_lst: list[tuple[Textbox, Equation]], t_index: int) -> None:
    """
    Updates the list and pygame rectangle objects associated to each string in the 2d list
    """
    # updates the rectangle
    for i in range(len(text_lst)):
        text_lst[i][0].update_rect(TEXTBOX_HEIGHT * i)
        tb_rect = text_lst[i][0].rect
        # draws every box
        pygame.draw.rect(scr, TEXTBOX_COLOR, tb_rect)

        # draws a darker inner box to distinguish which box is selected
        if t_index == i:
            pygame.draw.rect(scr, INDENT_COLOR, (tb_rect.x + TB_INDT, tb_rect.y + TB_INDT,
                                                 tb_rect.width - (2 * TB_INDT), tb_rect.height - (2 * TB_INDT)))

def calculate_render_size()->int:
    numbers=0
    for x in drawFinal:
        a,b,c=x[0],x[1],x[2]
        numbers+=a.size()
        d,e,f=b.red,b.green,b.blue
        numbers+=d.size()+e.size()+f.size()
        numbers+=c.bounder.size()
    return numbers


if __name__ == "__main__":
    # --- 1. PYGAME SETUP ---
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Render Engine")

    # --- 2. MATH SETUP ---
    # Create the equation. Try changing this to "sin(x) + cos(y)"!


    # Generate the coordinate grid (e.g., from -10 to 10)
    # Using a 100x100 resolution for the bare minimum test


    GRID_RESOLUTION = 100
    MATH_MIN, MATH_MAX = -15.0, 15.0

    # This creates a list of evenly spaced numbers from MATH_MIN to MATH_MAX
    step = (MATH_MAX - MATH_MIN) / GRID_RESOLUTION
    x_coords = [MATH_MIN + 1 + i * step for i in range(GRID_RESOLUTION)]
    y_coords = [MATH_MIN + j * step for j in range(GRID_RESOLUTION)]

    x_coords2 = [MATH_MIN - 12 + i * step for i in range(GRID_RESOLUTION)]
    y_coords2 = [MATH_MIN + j * step for j in range(GRID_RESOLUTION)]

    # --- 3. RENDER ONCE ---
    update_functions()
    screen.fill((255, 255, 255))  # Fill background with WHITE because we're RACIST
    print("Rendering grid...")
    renderingtime = GRID_RESOLUTION ** 2 * (calculate_render_size()) / 1000000
    print("estimated rendering time: " + str(renderingtime) + " seconds")
    print("Note: the power of your device will affect runtime speeds.")

    #render_grid(screen, eq2, my_color, my_boundary, x_coords, y_coords)
    render_grid(screen, x_coords, y_coords)
    # render_grid(screen, eq2, my_color, my_boundary, x_coords2, y_coords2)
    # Pushes the drawing to the actual monitor
    pygame.display.flip()

    print("Done!")

    # --- 4. MAIN EVENT LOOP ---
    # This keeps the window open until you click the red 'X'

    # a 2d list with each index containing a tuple (Textbox, Equation)
    text_box_lst = list()

    # index keeper to make sure that we know which box we are assigned to (will be assigned to the greatest index)
    # text_index < len(text_box_lst)
    text_index = 0


    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            # keyboard events
            if event.type == pygame.KEYDOWN:
                # text_index has to be smaller than the list amount, will not go outside of it
                if current_panel == 'Functions':
                    if text_index < len(text_box_lst) and text_index >= 0:
                        text_box_lst[text_index][0].update_text(event)  # acts as backspace
                        render_textboxes(screen, text_box_lst, text_index)



            # mouse click events
            if event.type == pygame.mouse.get_pressed():
                mouse_pos = pygame.mouse.get_pos()

                if pygame.Rect(0,0,TABS_WIDTH*5, TABS_HEIGHT).collidepoint(mouse_pos):
                    for i in range(5):
                        if pygame.Rect(0,TABS_WIDTH*i, TABS_WIDTH, TABS_HEIGHT).collidepoint(mouse_pos):
                            current_panel = PANELS[i]
                    render_textboxes(screen, text_box_lst, text_index)

                # in the text box areas
                if pygame.Rect(0, TEXTBOX_Y, TEXTBOX_WIDTH, HEIGHT).collidepoint(mouse_pos):
                    if current_panel == 'Functions':
                        for i in range(len(text_box_lst)):
                            if text_box_lst[i][0].rect.collidepoint(mouse_pos):
                                text_index = i
                        render_textboxes(screen, text_box_lst, text_index)

        pygame.display.flip()


    pygame.quit()
    sys.exit()
