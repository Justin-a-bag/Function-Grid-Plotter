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
TEXTBOX_Y = 50
TEXTBOX_WIDTH, TEXTBOX_HEIGHT = 300, 50
TEXTBOX_COLOR = (240, 240, 240)
INDENT_COLOR = (200, 200, 200)
TEXT_COLOR = (10, 10, 10)
TABS_WIDTH, TABS_HEIGHT = 60, 50
PANELS = ['Functions', 'Colours', 'Restrictions', 'Draw', 'Settings']
current_panel = 'Functions'

# --- GLOBAL STATE ---
# Note: IDs here do NOT contain the semicolon.
# Semicolons are only used inside the math strings (e.g., "sin(;eq)")
functionsList = [
        ("eq", "sin(x)"),
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


class DataEntryField:
    """
    Replaces the Textbox. Acts as a State Machine for each list item.
    """

    def __init__(self, index: int, list_ref: list):
        self.index = index
        self.y = TEXTBOX_Y + (index * TEXTBOX_HEIGHT)
        self.rect = pygame.Rect(0, self.y, TEXTBOX_WIDTH, TEXTBOX_HEIGHT)

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

        # 1. Error Flagging
        # Fetch the color from our global error_states dict based on this field's index.
        # Defaults to Grey if not found.
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
        clip_area = pygame.Rect(0, 0, self.data_rect.width - 5, self.data_rect.height)
        if data_surf.get_width() > clip_area.width and is_active:
            clip_area.x = data_surf.get_width() - clip_area.width

        surface.blit(data_surf, (self.data_rect.x + 5, self.data_rect.y + 7), clip_area)

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
        if self.editing_id:
            if event.key == pygame.K_BACKSPACE:
                self.id_str = self.id_str[:-1]
            else:
                self.id_str += event.unicode
        elif self.editing_data:
            if event.key == pygame.K_BACKSPACE:
                self.data_str = self.data_str[:-1]
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

        # Rule 1: NO Semicolons in the declaration box!
        if ';' in u_id:
            error_states[i] = ((200, 50, 50),
                               "Variable names cannot contain ';'. Use ';' only when referencing them in equations.")
            continue  # Kill the ID

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
    surface.fill((255, 255, 255))
    cell_w = (DRAW_MAX_X - DRAW_MIN_X) / len(xpoints)
    cell_h = (DRAW_MAX_Y - DRAW_MIN_Y) / len(ypoints)

    for i in range(len(xpoints)):
        for j in range(len(ypoints)):
            math_x = xpoints[i]
            math_y = ypoints[j]
            for curFunc in drawFinal:
                if curFunc[2].inBounds(math_x, math_y):
                    z = curFunc[0].evaluate(math_x, math_y)
                    squarecolor = curFunc[1].getColorTuple(z)
                    screen_x = DRAW_MIN_X + i * cell_w
                    screen_y = DRAW_MAX_Y - ((j + 1) * cell_h)

                    if squarecolor != (-1, -1, -1):
                        pygame.draw.rect(surface, squarecolor, (screen_x, screen_y, max(1.0, cell_w), max(1.0, cell_h)))


# --- MAIN EXECUTION ---
if __name__ == "__main__":
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Render Engine")

    GRID_RESOLUTION = 100
    MATH_MIN, MATH_MAX = -15.0, 15.0
    step = (MATH_MAX - MATH_MIN) / GRID_RESOLUTION
    x_coords = [MATH_MIN + 1 + i * step for i in range(GRID_RESOLUTION)]
    y_coords = [MATH_MIN + j * step for j in range(GRID_RESOLUTION)]

    # Generate a static surface to hold the math grid so UI doesn't lag
    grid_surface = pygame.Surface((WIDTH, HEIGHT))

    update_functions()
    print("Initial render calculating...")
    render_grid(grid_surface, x_coords, y_coords)

    # Initialize UI Fields (Length of functionsList + 1 empty field for adding)
    ui_fields = [DataEntryField(i, functionsList) for i in range(len(functionsList) + 1)]

    running = True
    while running:
        # 1. ALWAYS BLIT THE CACHED MATH GRID FIRST
        screen.blit(grid_surface, (0, 0))

        # 2. DRAW SIDEBAR BACKGROUND OVER IT
        pygame.draw.rect(screen, (220, 220, 220), (0, 0, TEXTBOX_WIDTH, HEIGHT))

        # 3. HANDLE EVENTS
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()

                # Check if user clicked inside any UI field
                clicked_any_field = False
                for field in ui_fields:
                    if field.rect.collidepoint(mouse_pos):
                        clicked_any_field = True
                        needs_redraw = field.handle_click(mouse_pos)

                        # If confirmed, recalculate grid and regenerate UI list to add the next empty block
                        if needs_redraw:
                            print("Recalculating Math...")
                            render_grid(grid_surface, x_coords, y_coords)
                            ui_fields = [DataEntryField(i, functionsList) for i in range(len(functionsList) + 1)]

                    else:
                        # If they clicked another field, cancel the edit on this one
                        if field.editing_id or field.editing_data:
                            field.cancel()

                # If they clicked entirely outside the UI sidebar, cancel everything
                if not clicked_any_field:
                    for field in ui_fields: field.cancel()

            if event.type == pygame.KEYDOWN:
                for field in ui_fields:
                    field.handle_keydown(event)

        # 4. DRAW ALL UI FIELDS
        for field in ui_fields:
            field.draw(screen)

        pygame.display.flip()

    pygame.quit()
    sys.exit()
