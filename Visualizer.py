from __future__ import annotations  # MUST be at the very top of the file
import pygame
import sys

# Import your custom classes
from Equation import Equation
from Color import Color
from Boundary import Boundary

#Performance improvements
sys.setrecursionlimit(5000)

# Define screen and drawing boundaries
WIDTH, HEIGHT = 1100, 800
DRAW_MIN_X, DRAW_MAX_X = 300, WIDTH
DRAW_MIN_Y, DRAW_MAX_Y = 0, HEIGHT
TEXTBOX_Y = 50
TEXTBOX_WIDTH, TEXTBOX_HEIGHT = 300, 50
TEXTBOX_COLOR = (240, 240, 240)
INDENT_COLOR = (200, 200, 200)
TEXT_COLOR = (10, 10, 10)
TABS_WIDTH, TABS_HEIGHT = 60, 50
PANELS = ['Functions', 'Colours', 'Restrictions', 'Draw', 'Settings']
current_panel = 'Functions'

# Settings & AST Globals
ANGLE_MODE = "radians"
SHOW_AST = False
AST_SELECTED_ID = None
SCREEN_SIZE_OPTIONS = [(900, 700), (1100, 800), (1280, 900), (1400, 1000), (1600, 1000)]
SCREEN_SIZE_INDEX = 1
settings_buttons = {}
ast_buttons = {}
# I have temporarily disabled this feature since it isn't what we're looking for
# toggle_ast_button = pygame.Rect(180, 0, 120, 30)
GRAPH_SURFACE = None
AST_WRAP_WIDTH = 55

scroll_y_vals=[0,0,0,0]
#use scroll_y_vals for the scrolling amounts on each tab

# --- GLOBAL STATE ---
# Note: IDs here do NOT contain the semicolon.
# Semicolons are only used inside the math strings (e.g., "sin(;eq)")
functionsList = [
    ("eq",
     "arctan(2sin(-2x-y/8+cos(3y-x-sin(cos(sin(sin(x*y)+x))+x-y+arccot(x)*arctan(y))))+frac{(x^{2}+\frac{y^{2}}{14})}{3}-(\frac{100}{x^{2}+y^{2}})+e^{-4-y})"),
    ("r", "255((x-(cos(3.7(x+0.8))/3))/2.8+1.28)"),
    ("g", "255(sin(1.5(x+pi/2))/2.8+0.5)"),
    ("b", "255(e^(-(3(x+0.99))^2)/3-x/9+0.1)"),
    ("rest", "1")
]

functionsDict = {}
colorsList = [("my_color", "r", "g", "b")]
colorsDict = {}
restrictionsList = [("rest", "rest", False)]
restrictionsDict = {}
drawList = [("eq", "my_color", "rest")]
drawFinal = []

# Maps list index -> ((R, G, B), "Error Message")
error_states = {}

pygame.init()
font = pygame.font.SysFont(None, 24)
small_font = pygame.font.SysFont(None, 18)


def calculate_draw_bounds():
    """
    Forces the drawing area to remain the correct ratio to prevent stretching.
    This will need to be edited to allow for rectangular grids
    """
    # TODO: calculate draw bounds based on the dimensions of the grid rather than a square
    global DRAW_MIN_X, DRAW_MAX_X, DRAW_MIN_Y, DRAW_MAX_Y

    # Calculate available space outside the 300px sidebar
    available_w = max(1, WIDTH - TEXTBOX_WIDTH)
    available_h = max(1, HEIGHT)

    # The grid will be a square based on the smallest available dimension
    grid_size = min(available_w, available_h)

    # Center the square in the available space
    DRAW_MIN_X = TEXTBOX_WIDTH + (available_w - grid_size) // 2
    DRAW_MAX_X = DRAW_MIN_X + grid_size
    DRAW_MIN_Y = (available_h - grid_size) // 2
    DRAW_MAX_Y = DRAW_MIN_Y + grid_size


class DataEntryField:
    """
    Replaces the Textbox. Acts as a State Machine for each list item.
    """

    def __init__(self, index: int, list_ref: list):
        self.index = index
        self.Y = TEXTBOX_Y + (index * TEXTBOX_HEIGHT)
        self.y = self.Y
        self.rect = pygame.Rect(0, self.y, TEXTBOX_WIDTH, TEXTBOX_HEIGHT)
        #TODO: autoscroll text to the right when you click on it
        self.scroll_x = 0

        # Determine if this is a populated field or the "New" generation field at the bottom
        if index < len(list_ref):
            self.id_str = list_ref[index][0]
            self.data_str = list_ref[index][1]
        else:
            self.id_str = ""
            self.data_str = ""

        # Backups for when the user clicks off (Cancels)
        self.backup_id = self.id_str
        self.backup_data = self.data_str

        # State flags
        self.editing_id = False
        self.editing_data = False

        # Sub-rectangles for hit-testing
        self.id_rect = pygame.Rect(30, self.y + 10, 50, 30)
        self.data_rect = pygame.Rect(85, self.y + 10, 150, 30)
        self.btn_enter = pygame.Rect(240, self.y + 10, 50, 30)

    def draw(self, surface: pygame.Surface):
        # Draw background
        is_active = self.editing_id or self.editing_data
        bg_color = INDENT_COLOR if is_active else TEXTBOX_COLOR
        pygame.draw.rect(surface, bg_color, self.rect)
        pygame.draw.rect(surface, (150, 150, 150), self.rect, 1)  # Border

        #Added for Scrolling, not sure if it's correct
        self.y = self.Y+scroll_y_vals[0]
        self.rect.y = self.y
        self.id_rect.y = self.y + 10
        self.data_rect.y = self.y + 10
        self.btn_enter.y = self.y + 10

        if self.y + TEXTBOX_HEIGHT < TABS_HEIGHT or self.y > HEIGHT:
            return
            
        # 1. Error Flagging
        # Fetch the color from our global error_states dict based on this field's index.
        # Defaults to Grey if not found.
        #TODO: blue flagging if a function is too large
        flag_color = error_states.get(self.index, ((150, 150, 150), ""))[0]
        pygame.draw.circle(surface, flag_color, (15, self.y + 25), 6)

        # 2. Draw ID Field
        pygame.draw.rect(surface, (255, 255, 255) if self.editing_id else bg_color, self.id_rect)
        id_surf = font.render(self.id_str, True, TEXT_COLOR)
        surface.blit(id_surf, (self.id_rect.x + 5, self.id_rect.y + 7))

        # 3. Draw Data Field (With Scrolling/Clipping)
        pygame.draw.rect(surface, (255, 255, 255) if self.editing_data else bg_color, self.data_rect)

        # ast_to_string logic: if NOT editing, show the formatted AST string
        display_str = self.data_str
        if not is_active and self.id_str in functionsDict:
            try:
                display_str = functionsDict[self.id_str].ast_to_string()
            except AttributeError:
                pass

        data_surf = font.render(display_str, True, TEXT_COLOR)

        # Scroll through text entry field natively via subsurface clipping
        # Added horizantal scrolling(left and right key)
        clip_area = pygame.Rect(self.scroll_x, 0, self.data_rect.width - 5, self.data_rect.height)
        surface.blit(data_surf, (self.data_rect.x + 5, self.data_rect.y + 7), clip_area)

        max_scroll = max(0, data_surf.get_width() - (self.data_rect.width - 5))
        self.scroll_x = max(0, min(self.scroll_x, max_scroll))

        # 4. Draw Confirm "Enter" Button
        if is_active:
            pygame.draw.rect(surface, (100, 200, 100), self.btn_enter)
            btn_txt = small_font.render("ENTER", True, (0, 0, 0))
            surface.blit(btn_txt, (self.btn_enter.x + 5, self.btn_enter.y + 10))
        
    def handle_click(self, mouse_pos) -> bool:
        """Returns True if the 'Enter' button was clicked and confirmed."""
        if self.id_rect.collidepoint(mouse_pos):
            self.editing_id = True
            self.editing_data = False
        elif self.data_rect.collidepoint(mouse_pos):
            self.editing_data = True
            self.editing_id = False
        elif self.btn_enter.collidepoint(mouse_pos) and (self.editing_id or self.editing_data):
            return self.confirm()
        return False

    def handle_keydown(self, event):
        # TODO: improve quality of life (holding backspace & arrow keys)

        

        #TODO: editing inside of the line instead of strictly at the end
        if self.editing_id:
            if event.key == pygame.K_BACKSPACE:
                self.id_str = self.id_str[:-1]
            else:
                self.id_str += event.unicode
                
        elif self.editing_data:
            if event.key == pygame.K_BACKSPACE:
                self.data_str = self.data_str[:-1]
            elif event.key == pygame.K_LEFT:
                self.scroll_x -= 10
            elif event.key == pygame.K_RIGHT:
                self.scroll_x += 10
            else:
                self.data_str += event.unicode
                
    def cancel(self):
        """Reverts the field to what it had originally without changing data."""
        self.id_str = self.backup_id
        self.data_str = self.backup_data
        self.editing_id = False
        self.editing_data = False

    def confirm(self) -> bool:
        """Changes list indices and triggers dict rebuild."""
        global functionsList
        if self.index < len(functionsList):
            functionsList[self.index] = (self.id_str, self.data_str)
        else:
            if self.id_str.strip() != "":
                functionsList.append((self.id_str, self.data_str))

        self.backup_id = self.id_str
        self.backup_data = self.data_str
        self.editing_id = False
        self.editing_data = False

        update_functions()
        return True  # Signals the main loop that we need to recalculate the math grid


def update_functions() -> None:
    """Rebuilds all dictionaries and runs error checking validation."""
    global functionsDict, colorsDict, restrictionsDict, drawFinal, error_states

    functionsDict.clear()
    error_states.clear()
    seen_ids = set()

    # --- 1. BUILD FUNCTIONS AND CHECK ERRORS ---
    for i, item in enumerate(functionsList):
        u_id, u_str = item[0], item[1]

        if not u_id:
            error_states[i] = ((150, 150, 150), "")  # Grey (Empty)
            continue

        # Rule 1: NO Tildes in the declaration box!
        if ';' in u_id:
            error_states[i] = ((200, 50, 50),
                               "Variable names cannot contain ';'. Use ';' only when referencing them in equations.")
            continue  # Fucking Kill the ID

        # Rule 2: Duplicate Check
        if u_id in seen_ids:
            error_states[i] = ((200, 200, 50), "Duplicate ID: Using the first declared value.")
            continue  # Skip adding to dict

        seen_ids.add(u_id)

        # Rule 3: Compile the math and check tree integrity
        eq = Equation(u_str)
        functionsDict[u_id] = eq

        # Check for Math Errors vs Size Warnings
        if eq.tree.op == 'invalid' or eq.tree.op == 'potato':
            error_states[i] = ((200, 50, 50), "Math Error: Invalid syntax or missing arguments.")
        elif eq.size() > 100:
            error_states[i] = ((50, 100, 200), "Warning: Large function tree. May impact performance.")
        else:
            error_states[i] = ((50, 200, 50), "Valid")  # Green

    # --- 2. BUILD SECONDARY DICTS ---
    colorsDict.clear()
    for x in colorsList:
        if x[0] not in colorsDict:
            if all(x[c] in functionsDict for c in [1, 2, 3]):
                colorsDict[x[0]] = Color(functionsDict[x[1]], functionsDict[x[2]], functionsDict[x[3]])

    restrictionsDict.clear()
    for x in restrictionsList:
        if x[0] not in restrictionsDict:
            if x[1] in functionsDict:
                restrictionsDict[x[0]] = Boundary(functionsDict[x[1]], x[2])

    drawFinal.clear()
    for x in drawList:
        if x[0] in functionsDict and x[1] in colorsDict and x[2] in restrictionsDict:
            drawFinal.append((functionsDict[x[0]], colorsDict[x[1]], restrictionsDict[x[2]]))


def render_grid(surface: pygame.Surface, xpoints: list[float], ypoints: list[float]):
    # WHITE LINE BUG FIXED
    surface.fill((255, 255, 255))
    cell_w = (DRAW_MAX_X - DRAW_MIN_X) / len(xpoints)
    cell_h = (DRAW_MAX_Y - DRAW_MIN_Y) / len(ypoints)

    for i in range(len(xpoints)):
        for j in range(len(ypoints)):
            math_x = xpoints[i]
            math_y = ypoints[j]
            for curFunc in drawFinal:
                if curFunc[2].inBounds(math_x, math_y,ANGLE_MODE,functionsDict,0):
                    z = curFunc[0].evaluate(math_x, math_y,ANGLE_MODE,functionsDict,0)
                    squarecolor = curFunc[1].getColorTuple(z)
                    screen_x = round(DRAW_MIN_X + i * cell_w)
                    next_x = round(DRAW_MIN_X + (i + 1) * cell_w)

                    screen_y_top = round(DRAW_MAX_Y - ((j + 1) * cell_h))
                    screen_y_bottom = round(DRAW_MAX_Y - (j * cell_h))

                    rect_w = max(1, next_x - screen_x)
                    rect_h = max(1, screen_y_bottom - screen_y_top)
                    # break it into x y components and then do a rectangle draw for each one to prevent the white lines from appearing
                    if squarecolor != (-1, -1, -1):
                        pygame.draw.rect(surface, squarecolor, (screen_x, screen_y_top, rect_w, rect_h))


# TODO: add comments to this god forsaken code stretch
def rerender_graph_surface(x_coords, y_coords):
    global GRAPH_SURFACE
    GRAPH_SURFACE = pygame.Surface((WIDTH, HEIGHT))
    GRAPH_SURFACE.fill((255, 255, 255))
    render_grid(GRAPH_SURFACE, x_coords, y_coords)

#Draws the top 5 label things
def render_tab_labels(screen: pygame.Surface, font: pygame.font.Font) -> None:
    for i in range(len(PANELS)):
        rect = pygame.Rect(TABS_WIDTH * i, 0, TABS_WIDTH, TABS_HEIGHT)
        pygame.draw.rect(screen, (225, 225, 225), rect)
        if PANELS[i] == current_panel:
            pygame.draw.rect(screen, (180, 180, 180), rect)
        pygame.draw.rect(screen, (0, 0, 0), rect, 1)
        label = font.render(PANELS[i][:4], True, (0, 0, 0))
        screen.blit(label, (rect.x + 4, rect.y + 15))


def draw_button(screen: pygame.Surface, font: pygame.font.Font, rect: pygame.Rect, label: str) -> None:
    pygame.draw.rect(screen, (225, 225, 225), rect)
    pygame.draw.rect(screen, (70, 70, 70), rect, 2)
    text_surface = font.render(label, True, (0, 0, 0))
    text_rect = text_surface.get_rect(center=rect.center)
    screen.blit(text_surface, text_rect)


# TODO: the UI for the other 3 tabs
# (should probably use something similar to render_tab_labels and draw_button for this?)

# if you need to render a screen make the functions for that screen here
# TODO: update and rework settings overlay
def render_settings_overlay(screen: pygame.Surface, font: pygame.font.Font) -> None:
    global settings_buttons
    settings_buttons = {}
    if current_panel != 'Settings': return

    title = font.render("SETTINGS", True, (0, 0, 0))
    screen.blit(title, (50, 60))

    mode_text = font.render("Angle mode: " + ANGLE_MODE, True, (0, 0, 0))
    size_text = font.render(f"Window: {WIDTH} x {HEIGHT}", True, (0, 0, 0))
    ast_text = font.render("AST visible: " + str(SHOW_AST), True, (0, 0, 0))
    selected_text = font.render("AST ID: " + str(AST_SELECTED_ID), True, (0, 0, 0))

    screen.blit(mode_text, (50, 90))
    screen.blit(size_text, (50, 115))
    screen.blit(ast_text, (50, 140))
    screen.blit(selected_text, (50, 165))

    settings_buttons["angle_toggle"] = pygame.Rect(50, 195, 110, 35)
    settings_buttons["size_prev"] = pygame.Rect(50, 240, 50, 35)
    settings_buttons["size_next"] = pygame.Rect(100, 240, 50, 35)

    draw_button(screen, font, settings_buttons["angle_toggle"], "Toggle Mode")
    draw_button(screen, font, settings_buttons["size_prev"], "<")
    draw_button(screen, font, settings_buttons["size_next"], ">")


# TODO: decide what to do with the AST rendering section
def render_ast_overlay(screen: pygame.Surface, font: pygame.font.Font) -> None:
    global ast_buttons
    ast_buttons = {}
    if not SHOW_AST: return

    panel_x = 320
    panel_y = 40
    panel_w = max(320, WIDTH - 340)
    panel_h = min(340, HEIGHT - 60)

    overlay_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
    pygame.draw.rect(screen, (245, 245, 245), overlay_rect)
    pygame.draw.rect(screen, (80, 80, 80), overlay_rect, 2)

    title = font.render("AST Visualizer", True, (0, 0, 0))
    screen.blit(title, (panel_x + 10, panel_y + 10))

    # ast_buttons["toggle_ast"] = pygame.Rect(panel_x + panel_w - 110, panel_y + 8, 90, 28)
    ast_buttons["ast_prev"] = pygame.Rect(panel_x + 10, panel_y + 40, 35, 30)
    ast_buttons["ast_next"] = pygame.Rect(panel_x + 50, panel_y + 40, 35, 30)

    # draw_button(screen, font, ast_buttons["toggle_ast"], "Hide")
    draw_button(screen, font, ast_buttons["ast_prev"], "<")
    draw_button(screen, font, ast_buttons["ast_next"], ">")

    selected_line = "Selected: " + str(AST_SELECTED_ID)
    selected_surface = font.render(selected_line, True, (0, 0, 0))
    screen.blit(selected_surface, (panel_x + 95, panel_y + 47))

    if AST_SELECTED_ID is None or AST_SELECTED_ID not in functionsDict:
        no_text = font.render("No selected function", True, (0, 0, 0))
        screen.blit(no_text, (panel_x + 10, panel_y + 85))
        return

    ast_text = functionsDict[AST_SELECTED_ID].ast_to_string()
    lines = []
    for i in range(0, len(ast_text), AST_WRAP_WIDTH):
        lines.append(ast_text[i:i + AST_WRAP_WIDTH])

    max_lines = (panel_h - 100) // 20
    for i in range(min(len(lines), max_lines)):
        line_surface = font.render(lines[i], True, (20, 20, 20))
        screen.blit(line_surface, (panel_x + 10, panel_y + 85 + 20 * i))


def apply_screen_size_from_index(index: int) -> None:
    global SCREEN_SIZE_INDEX, WIDTH, HEIGHT
    SCREEN_SIZE_INDEX = index % len(SCREEN_SIZE_OPTIONS)
    WIDTH, HEIGHT = SCREEN_SIZE_OPTIONS[SCREEN_SIZE_INDEX]
    calculate_draw_bounds()


def cycle_ast_selection(direction: int) -> None:
    global AST_SELECTED_ID
    if len(functionsList) == 0:
        AST_SELECTED_ID = None
        return
    ids = [item[0] for item in functionsList]
    if AST_SELECTED_ID not in ids:
        AST_SELECTED_ID = ids[0]
        return
    current_index = ids.index(AST_SELECTED_ID)
    AST_SELECTED_ID = ids[(current_index + direction) % len(ids)]

    # COMMENTS SHOULD BE ADDED TO SECTION ABOVE


# --- MAIN EXECUTION ---
if __name__ == "__main__":
    calculate_draw_bounds()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Render Engine")

    GRID_RESOLUTION = 100
    MATH_MIN, MATH_MAX = -15.0, 15.0
    step = (MATH_MAX - MATH_MIN) / GRID_RESOLUTION
    x_coords = [MATH_MIN + 1 + i * step for i in range(GRID_RESOLUTION)]
    y_coords = [MATH_MIN + j * step for j in range(GRID_RESOLUTION)]

    # Generate a static surface to hold the math grid so UI doesn't lag

    update_functions()
    if len(functionsList) > 0:
        AST_SELECTED_ID = functionsList[0][0]
    rerender_graph_surface(x_coords, y_coords)

    ui_fields = [DataEntryField(i, functionsList) for i in range(len(functionsList) + 1)]

    running = True
    while running:
        # 1. ALWAYS BLIT THE CACHED MATH GRID FIRST
        if GRAPH_SURFACE is not None:
            screen.blit(GRAPH_SURFACE, (0, 0))
        

        pygame.draw.rect(screen, (220, 220, 220), (0, TABS_HEIGHT, TEXTBOX_WIDTH, HEIGHT))
        # 3. HANDLE EVENTS
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.VIDEORESIZE:
                WIDTH, HEIGHT = event.w, event.h
                calculate_draw_bounds()  # Recalculate aspect ratio
                screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
                rerender_graph_surface(x_coords, y_coords)

            if event.type == pygame.MOUSEBUTTONDOWN:
                # TODO (optional): resizing side menu
                mouse_pos = pygame.mouse.get_pos()

                for i in range(5):
                    if pygame.Rect(TABS_WIDTH * i, 0, TABS_WIDTH, TABS_HEIGHT).collidepoint(mouse_pos):
                        current_panel = PANELS[i]
                        break

                # Check if user clicked inside any UI field
                if current_panel == 'Functions':
                    if event.button == 4:
                        scroll_y_vals[0] -= 5
                    elif event.button == 5:
                        scroll_y_vals[0] = min(0,scroll_y_vals[0]+5)

                    clicked_any_field = False
                    
                    for field in ui_fields:
                        # TODO: allow users to move around entry fields (applies for all 4 tabs) and when one gets deleted, it removes that text thing and shifts the others
                        if field.rect.collidepoint(mouse_pos):
                            clicked_any_field = True
                            needs_redraw = field.handle_click(mouse_pos)

                            # If confirmed, recalculate grid and regenerate UI list to add the next empty block
                            if needs_redraw:
                                print("Recalculating Math...")
                                rerender_graph_surface(x_coords, y_coords)
                                ui_fields = [DataEntryField(i, functionsList) for i in range(len(functionsList) + 1)]

                        else:
                            # If they clicked another field, cancel the edit on this one
                            if field.editing_id or field.editing_data:
                                field.cancel()

                    # If they clicked entirely outside the UI sidebar, cancel everything
                    if not clicked_any_field:
                        for field in ui_fields: field.cancel()

                # TODO: the other 3 panels
                if current_panel == 'Colours':
                    # deal with buttons here
                    continue

                if current_panel == 'Restricions':
                    # deal with buttons here
                    continue

                if current_panel == 'Draw':
                    # deal with buttons here
                    continue

                if current_panel == 'Settings':
                    # TODO: import-export of text
                    # Remember that import should just create new lines
                    if settings_buttons.get("angle_toggle") and settings_buttons["angle_toggle"].collidepoint(
                            mouse_pos):
                        ANGLE_MODE = "degrees" if ANGLE_MODE == "radians" else "radians"
                        update_functions()
                        rerender_graph_surface(x_coords, y_coords)
                    elif settings_buttons.get("size_prev") and settings_buttons["size_prev"].collidepoint(mouse_pos):
                        apply_screen_size_from_index(SCREEN_SIZE_INDEX - 1)
                        screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
                        rerender_graph_surface(x_coords, y_coords)
                    elif settings_buttons.get("size_next") and settings_buttons["size_next"].collidepoint(mouse_pos):
                        apply_screen_size_from_index(SCREEN_SIZE_INDEX + 1)
                        screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
                        rerender_graph_surface(x_coords, y_coords)

                # if SHOW_AST:
                # if ast_buttons.get("toggle_ast") and ast_buttons["toggle_ast"].collidepoint(mouse_pos):
                #    SHOW_AST = False
                #    if ast_buttons.get("ast_prev") and ast_buttons["ast_prev"].collidepoint(mouse_pos):
                #        cycle_ast_selection(-1)
                #    elif ast_buttons.get("ast_next") and ast_buttons["ast_next"].collidepoint(mouse_pos):
                #        cycle_ast_selection(1)
                # if toggle_ast_button.collidepoint(mouse_pos) and current_panel == 'Functions':
                #    SHOW_AST = not SHOW_AST

            if event.type == pygame.KEYDOWN:
                if current_panel == 'Functions':
                    for field in ui_fields:
                        field.handle_keydown(event)

        # 4. DRAW APPROPRIATE UI OVERLAYS
        if current_panel == 'Functions':
            for field in ui_fields:
                field.draw(screen)
            # pygame.draw.rect(screen, (225, 225, 225), toggle_ast_button)
            # pygame.draw.rect(screen, (0, 0, 0), toggle_ast_button, 2)
            # label = font.render("Toggle AST", True, (0, 0, 0))
            # screen.blit(label, (195, 7))
        elif current_panel == 'Settings':
            render_settings_overlay(screen, font)

        # 2. DRAW UI TABS AND ACTIVE PANEL BACKGROUND
        render_tab_labels(screen, font)
        
        render_ast_overlay(screen, font)

        pygame.display.flip()

    pygame.quit()
    sys.exit()
