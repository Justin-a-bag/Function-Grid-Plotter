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
PANELS = ['Functions', 'Colors', 'Restrictions', 'Draw', 'Settings']
current_panel = 'Functions'

# Settings & AST Globals
ANGLE_MODE = "radians"
SCREEN_SIZE_OPTIONS = [(900, 700), (1100, 800), (1280, 900), (1400, 1000), (1600, 1000)]
SCREEN_SIZE_INDEX = 1

WARNING_TOTAL_GRID_POINTS = 90000
MAX_TOTAL_GRID_POINTS = 4194304
settings_buttons = {}
settings_values = {
    "x_min": "-15.0",
    "x_points": "100",
    "x_max": "15.0",
    "y_min": "-15.0",
    "y_points": "100",
    "y_max": "15.0",
    "max_recursion": "0"
}

active_settings_field = None

GRAPH_SURFACE = None

MAX_DEPTH = 100
scroll_y_vals = [0, 0, 0, 0]
# use scroll_y_vals for the scrolling amounts on each tab

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
settings_error_states = {}
restriction_error_states = {}
draw_error_states = {}

pygame.init()
pygame.key.set_repeat(500, 50)
font = pygame.font.SysFont(None, 24)
small_font = pygame.font.SysFont(None, 18)


def calculate_draw_bounds(xrange: float, yrange: float):
    """
    Forces the drawing area to remain the correct ratio to prevent stretching.
    This will need to be edited to allow for rectangular grids
    """
    global DRAW_MIN_X, DRAW_MAX_X, DRAW_MIN_Y, DRAW_MAX_Y

    # Calculate available space outside the 300px sidebar
    available_w = max(1, WIDTH - TEXTBOX_WIDTH)
    available_h = max(1, HEIGHT)

    # grid size horizontally
    grid_size_x = min(available_w, available_h * xrange / yrange)
    grid_size_y = min(available_w * yrange / xrange, available_h)

    # Center the square in the available space
    DRAW_MIN_X = TEXTBOX_WIDTH + (available_w - grid_size_x) // 2
    DRAW_MAX_X = DRAW_MIN_X + grid_size_x
    DRAW_MIN_Y = (available_h - grid_size_y) // 2
    DRAW_MAX_Y = DRAW_MIN_Y + grid_size_y


class FunctionsEntryField:
    """
    Replaces the Textbox. Acts as a State Machine for each list item.
    """

    def __init__(self, index: int, list_ref: list):
        self.index = index
        self.Y = TEXTBOX_Y + (index * TEXTBOX_HEIGHT)
        self.y = self.Y
        self.rect = pygame.Rect(0, self.y, TEXTBOX_WIDTH, TEXTBOX_HEIGHT)
        # TODO: autoscroll text to the right when you click on it (Cindy)
        self.scroll_x = 0

        # Determine if this is a populated field or the "New" generation field at the bottom
        if index < len(list_ref):
            self.id_str = list_ref[index][0]
            self.data_str = list_ref[index][1]
        else:
            self.id_str = ""
            self.data_str = ""
        # Create a Cursor
        self.cursor_position = len(self.data_str)

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

        # Added for Scrolling, not sure if it's correct
        self.y = self.Y + scroll_y_vals[0]
        self.rect.y = self.y
        self.id_rect.y = self.y + 10
        self.data_rect.y = self.y + 10
        self.btn_enter.y = self.y + 10

        if self.y + TEXTBOX_HEIGHT < TABS_HEIGHT or self.y > HEIGHT:
            return

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

        if self.editing_data:
            cursor_x = self.data_rect.x + 5 + font.size(self.data_str[:self.cursor_position])[0] - self.scroll_x
            cursor_y = self.data_rect.y + 5
            pygame.draw.line(surface, (0, 0, 0), (cursor_x, cursor_y), (cursor_x, cursor_y + 20), 2)


    def handle_click(self, mouse_pos) -> bool:
        """Returns True if the 'Enter' button was clicked and confirmed."""
        if self.id_rect.collidepoint(mouse_pos):
            self.editing_id = True
            self.editing_data = False
        elif self.data_rect.collidepoint(mouse_pos):
            self.editing_data = True
            self.editing_id = False
            # Find cursor position
            cursor_pos = mouse_pos[0] - (self.data_rect.x + 5) + self.scroll_x
            display_str = self.data_str
            font_widths = [font.size(display_str[:i])[0] for i in range(len(display_str) + 1)]
            # Set the cursor to the nearest character
            self.cursor_position = min(range(len(font_widths)), key=lambda i: abs(font_widths[i] - cursor_pos))
            # Autoscroll text such that the cursor remains visible
            cursor_pixel = font.size(self.data_str[:self.cursor_position])[0]

            if cursor_pixel > self.data_rect.width - 10:
                self.scroll_x = cursor_pixel - (self.data_rect.width - 10)
            else:
                self.scroll_x = 0

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
                if self.cursor_position > 0:
                    self.data_str = (
                            self.data_str[:self.cursor_position - 1] +
                            self.data_str[self.cursor_position:]
                    )
                    self.cursor_position -= 1

            elif event.key == pygame.K_LEFT:
                self.cursor_position = max(0, self.cursor_position - 1)
            elif event.key == pygame.K_RIGHT:
                self.cursor_position = min(len(self.data_str), self.cursor_position + 1)
            else :
                self.data_str = (
                    self.data_str[:self.cursor_position] +
                    event.unicode +
                    self.data_str[self.cursor_position:])
                self.cursor_position += 1

            cursor_pixel = font.size(self.data_str[:self.cursor_position])[0]
            visible_width = self.data_rect.width - 10

            if cursor_pixel - self.scroll_x > visible_width:
                self.scroll_x = cursor_pixel - visible_width

            elif cursor_pixel - self.scroll_x < 0:
                self.scroll_x = cursor_pixel

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


class ColorsEntryField(FunctionsEntryField):
    """
    Replaces the Textbox. Acts as a State Machine for each list item. Contains vital information for hitboxes in Pygame
    """
    data_index: int

    def __init__(self, index: int, list_ref: list):
        super().__init__(index, list_ref)

        # three data_str (including data_str) values for r, g, and b values
        if index < len(list_ref):
            self.data_str_g = list_ref[index][2]
            self.data_str_b = list_ref[index][3]
        else:
            self.data_str_g = ""
            self.data_str_b = ""

        # three backups including backup_str
        self.backup_data_g = self.data_str_g
        self.backup_data_b = self.data_str_b

        # Sub-rectangles for hit-testing
        self.id_rect = pygame.Rect(30, self.y + 10, 50, 30)
        self.full_data_rect = pygame.Rect(85, self.y + 10, 150, 30)
        self.data_rect1 = pygame.Rect(85, self.y + 10, 50, 30)
        self.data_rect2 = pygame.Rect(135, self.y + 10, 50, 30)
        self.data_rect3 = pygame.Rect(185, self.y + 10, 50, 30)
        self.btn_enter = pygame.Rect(240, self.y + 10, 50, 30)
        self.data_index = 0

    def draw(self, surface: pygame.Surface) -> None:
        # Draw background
        is_active = self.editing_id or self.editing_data
        bg_color = INDENT_COLOR if is_active else TEXTBOX_COLOR
        pygame.draw.rect(surface, bg_color, self.rect)
        pygame.draw.rect(surface, (150, 150, 150), self.rect, 1)  # Border

        #Added for Scrolling, not sure if it's correct
        self.y = self.Y+scroll_y_vals[1]
        self.rect.y = self.y
        self.id_rect.y = self.y + 10
        self.data_rect1.y = self.y + 10
        self.data_rect2.y = self.y + 10
        self.data_rect3.y = self.y + 10
        self.btn_enter.y = self.y + 10

        if self.y + TEXTBOX_HEIGHT < TABS_HEIGHT or self.y > HEIGHT:
            return

        # 1. Error Flagging
        # Fetch the color from our global error_states dict based on this field's index.
        # Defaults to Grey if not found.
        flag_color = error_states.get(self.index, ((150, 150, 150), ""))[0]
        pygame.draw.circle(surface, flag_color, (15, self.y + 25), 6)

        # 2. Draw ID Field
        pygame.draw.rect(surface, (255, 255, 255) if self.editing_id else bg_color, self.id_rect)
        id_surf = font.render(self.id_str, True, TEXT_COLOR)
        surface.blit(id_surf, (self.id_rect.x + 5, self.id_rect.y + 7))

        # 3. Draw 3 Data Fields (With Scrolling/Clipping)
        pygame.draw.rect(surface, (255, 255, 255) if self.editing_data and self.data_index == 0 else bg_color,
                         self.data_rect1)
        pygame.draw.rect(surface, (255, 255, 255) if self.editing_data and self.data_index == 1 else bg_color,
                         self.data_rect2)
        pygame.draw.rect(surface, (255, 255, 255) if self.editing_data and self.data_index == 2 else bg_color,
                         self.data_rect3)

        # ast_to_string logic: if NOT editing, show the formatted AST string
        display_str = self.data_str
        display_str2 = self.data_str_g
        display_str3 = self.data_str_b

        if not is_active and self.id_str in functionsDict:
            try:
                display_str = colorsDict[self.id_str].ast_to_string()
            except AttributeError:
                pass

        data_surf = font.render(display_str, True, TEXT_COLOR)
        data_surf2 = font.render(display_str2, True, TEXT_COLOR)
        data_surf3 = font.render(display_str3, True, TEXT_COLOR)

        # Scroll through text entry field natively via subsurface clipping
        # Added horizantal scrolling(left and right key)
        clip_area = pygame.Rect(self.scroll_x, 0, self.data_rect1.width - 5, self.data_rect1.height)
        surface.blit(data_surf, (self.data_rect1.x + 5, self.data_rect1.y + 7), clip_area)
        max_scroll = max(0, data_surf.get_width() - (self.data_rect1.width - 5))
        self.scroll_x = max(0, min(self.scroll_x, max_scroll))

        # scroll for rectangle 2 (g)
        clip_area = pygame.Rect(self.scroll_x, 0, self.data_rect2.width - 5, self.data_rect2.height)
        surface.blit(data_surf2, (self.data_rect2.x + 5, self.data_rect2.y + 7), clip_area)
        max_scroll = max(0, data_surf2.get_width() - (self.data_rect2.width - 5))
        self.scroll_x = max(0, min(self.scroll_x, max_scroll))

        # scroll for rectangle 3 (b)
        clip_area = pygame.Rect(self.scroll_x, 0, self.data_rect3.width - 5, self.data_rect3.height)
        surface.blit(data_surf3, (self.data_rect3.x + 5, self.data_rect3.y + 7), clip_area)
        max_scroll = max(0, data_surf3.get_width() - (self.data_rect3.width - 5))
        self.scroll_x = max(0, min(self.scroll_x, max_scroll))

        # 4. Draw Confirm "Enter" Button
        if is_active:
            pygame.draw.rect(surface, (100, 200, 100), self.btn_enter)
            btn_txt = small_font.render("ENTER", True, (0, 0, 0))
            surface.blit(btn_txt, (self.btn_enter.x + 5, self.btn_enter.y + 10))

        if self.editing_data:
            active_str = self.data_str if self.data_index == 0 else (self.data_str_g if self.data_index == 1 else self.data_str_b)
            active_rect = self.data_rect1 if self.data_index == 0 else (self.data_rect2 if self.data_index == 1 else self.data_rect3)
            cursor_x = active_rect.x + 5 + font.size(active_str[:self.cursor_position])[0] - self.scroll_x
            cursor_y = active_rect.y + 5
            pygame.draw.line(surface, (0, 0, 0), (cursor_x, cursor_y), (cursor_x, cursor_y + 20), 2)

    def handle_click(self, mouse_pos) -> bool:
        """Returns True if the 'Enter' button was clicked and confirmed."""
        if self.id_rect.collidepoint(mouse_pos):
            self.editing_id = True
            self.editing_data = False
        elif self.full_data_rect.collidepoint(mouse_pos):
            self.editing_data = True
            self.editing_id = False

            if self.data_rect1.collidepoint(mouse_pos):
                self.data_index = 0
                active_rect = self.data_rect1
                active_str = self.data_str
            elif self.data_rect2.collidepoint(mouse_pos):
                self.data_index = 1
                active_rect = self.data_rect2
                active_str = self.data_str_g
            elif self.data_rect3.collidepoint(mouse_pos):
                self.data_index = 2
                active_rect = self.data_rect3
                active_str = self.data_str_b
            else:
                return False

            cursor_pos = mouse_pos[0] - (active_rect.x + 5) + self.scroll_x
            font_widths = [font.size(active_str[:i])[0] for i in range(len(active_str) + 1)]
            self.cursor_position = min(range(len(font_widths)), key=lambda i: abs(font_widths[i] - cursor_pos))
            cursor_pixel = font.size(active_str[:self.cursor_position])[0]
            if cursor_pixel > active_rect.width - 10:
                self.scroll_x = cursor_pixel - (active_rect.width - 10)
            else:
                self.scroll_x = 0

        elif self.btn_enter.collidepoint(mouse_pos) and (self.editing_id or self.editing_data):
            return self.confirm()
        return False

    def handle_keydown(self, event) -> None:
        # TODO: improve quality of life (holding backspace & arrow keys)



        #TODO: editing inside of the line instead of strictly at the end
        if self.editing_id:
            if event.key == pygame.K_BACKSPACE:
                self.id_str = self.id_str[:-1]
            else:
                self.id_str += event.unicode

        elif self.editing_data:
            if event.key == pygame.K_BACKSPACE:
                if getattr(self, 'cursor_position', 0) > 0:
                    if self.data_index == 0:
                        self.data_str = self.data_str[:self.cursor_position - 1] + self.data_str[self.cursor_position:]
                    elif self.data_index == 1:
                        self.data_str_g = self.data_str_g[:self.cursor_position - 1] + self.data_str_g[self.cursor_position:]
                    elif self.data_index == 2:
                        self.data_str_b = self.data_str_b[:self.cursor_position - 1] + self.data_str_b[self.cursor_position:]
                    self.cursor_position -= 1
            elif event.key == pygame.K_LEFT:
                self.cursor_position = max(0, getattr(self, 'cursor_position', 0) - 1)
            elif event.key == pygame.K_RIGHT:
                active_str = self.data_str if self.data_index == 0 else (self.data_str_g if self.data_index == 1 else self.data_str_b)
                self.cursor_position = min(len(active_str), getattr(self, 'cursor_position', 0) + 1)
            else:
                if self.data_index == 0:
                    self.data_str = self.data_str[:getattr(self, 'cursor_position', 0)] + event.unicode + self.data_str[getattr(self, 'cursor_position', 0):]
                elif self.data_index == 1:
                    self.data_str_g = self.data_str_g[:getattr(self, 'cursor_position', 0)] + event.unicode + self.data_str_g[getattr(self, 'cursor_position', 0):]
                elif self.data_index == 2:
                    self.data_str_b = self.data_str_b[:getattr(self, 'cursor_position', 0)] + event.unicode + self.data_str_b[getattr(self, 'cursor_position', 0):]
                self.cursor_position = getattr(self, 'cursor_position', 0) + 1

            active_str = self.data_str if self.data_index == 0 else (self.data_str_g if self.data_index == 1 else self.data_str_b)
            cursor_pixel = font.size(active_str[:self.cursor_position])[0]
            visible_width = 40  # 50 - 10

            if cursor_pixel - self.scroll_x > visible_width:
                self.scroll_x = cursor_pixel - visible_width
            elif cursor_pixel - self.scroll_x < 0:
                self.scroll_x = cursor_pixel

    def cancel(self):
        """Reverts the field to what it had originally without changing data."""
        self.id_str = self.backup_id
        self.data_str = self.backup_data
        self.data_str_g = self.backup_data_g
        self.data_str_b = self.backup_data_b
        self.editing_id = False
        self.editing_data = False

    def confirm(self) -> bool:
        """Changes list indices and triggers dict rebuild."""
        global colorsList
        if self.index < len(colorsList):
            colorsList[self.index] = (self.id_str, self.data_str, self.data_str_g, self.data_str_b)
        else:
            if self.id_str.strip() != "":
                colorsList.append((self.id_str, self.data_str, self.data_str_g, self.data_str_b))

        self.backup_id = self.id_str
        self.backup_data = self.data_str
        self.backup_data_g = self.data_str_g
        self.backup_data_b = self.data_str_b
        self.editing_id = False
        self.editing_data = False

        update_functions()
        return True  # Signals the main loop that we need to recalculate the math grid





class RestrictionsEntryField(FunctionsEntryField):
    """
    Entry field for Restrictions tab: ID, Target ID, and Boolean toggle
    """
    def __init__(self, index: int, list_ref: list):
        super().__init__(index, list_ref)
        if index < len(list_ref):
            self.checkSmaller = list_ref[index][2]
        else:
            self.checkSmaller = False
            
        self.backup_checkSmaller = self.checkSmaller

        # Sub-rectangles for hit-testing
        self.id_rect = pygame.Rect(30, self.y + 10, 50, 30)
        self.full_data_rect = pygame.Rect(85, self.y + 10, 150, 30) # for generic click checking
        self.data_rect1 = pygame.Rect(85, self.y + 10, 110, 30) # for the target func id
        self.bool_rect = pygame.Rect(200, self.y + 10, 35, 30)  # for the boolean toggler
        self.btn_enter = pygame.Rect(240, self.y + 10, 50, 30)

    def draw(self, surface: pygame.Surface) -> None:
        is_active = self.editing_id or self.editing_data
        bg_color = INDENT_COLOR if is_active else TEXTBOX_COLOR
        pygame.draw.rect(surface, bg_color, self.rect)
        pygame.draw.rect(surface, (150, 150, 150), self.rect, 1)

        self.y = self.Y + scroll_y_vals[2]
        self.rect.y = self.y
        self.id_rect.y = self.y + 10
        self.data_rect1.y = self.y + 10
        self.bool_rect.y = self.y + 10
        self.full_data_rect.y = self.y + 10
        self.btn_enter.y = self.y + 10

        if self.y + TEXTBOX_HEIGHT < TABS_HEIGHT or self.y > HEIGHT:
            return

        # Status Flag
        flag_color = restriction_error_states.get(self.index, ((150, 150, 150), ""))[0]
        pygame.draw.circle(surface, flag_color, (15, self.y + 25), 6)

        # ID Field
        pygame.draw.rect(surface, (255, 255, 255) if self.editing_id else bg_color, self.id_rect)
        id_surf = font.render(self.id_str, True, TEXT_COLOR)
        surface.blit(id_surf, (self.id_rect.x + 5, self.id_rect.y + 7))

        # Target Func Field
        pygame.draw.rect(surface, (255, 255, 255) if self.editing_data else bg_color, self.data_rect1)
        data_surf = font.render(self.data_str, True, TEXT_COLOR)
        clip_area = pygame.Rect(self.scroll_x, 0, self.data_rect1.width - 5, self.data_rect1.height)
        surface.blit(data_surf, (self.data_rect1.x + 5, self.data_rect1.y + 7), clip_area)
        max_scroll = max(0, data_surf.get_width() - (self.data_rect1.width - 5))
        self.scroll_x = max(0, min(self.scroll_x, max_scroll))

        # Boolean Field
        pygame.draw.rect(surface, bg_color, self.bool_rect)
        pygame.draw.rect(surface, (0, 0, 0), self.bool_rect, 1)
        # Display <= 0 or >= 0 based on checkSmaller
        bool_str = "<= 0" if self.checkSmaller else ">= 0"
        bool_surf = small_font.render(bool_str, True, TEXT_COLOR)
        surface.blit(bool_surf, (self.bool_rect.x + 2, self.bool_rect.y + 10))

        if is_active:
            pygame.draw.rect(surface, (100, 200, 100), self.btn_enter)
            btn_txt = small_font.render("ENTER", True, (0, 0, 0))
            surface.blit(btn_txt, (self.btn_enter.x + 5, self.btn_enter.y + 10))

        if self.editing_data:
            cursor_x = self.data_rect1.x + 5 + font.size(self.data_str[:getattr(self, 'cursor_position', 0)])[0] - self.scroll_x
            cursor_y = self.data_rect1.y + 5
            pygame.draw.line(surface, (0, 0, 0), (cursor_x, cursor_y), (cursor_x, cursor_y + 20), 2)

    def handle_click(self, mouse_pos) -> bool:
        if self.id_rect.collidepoint(mouse_pos):
            self.editing_id = True
            self.editing_data = False
        elif self.data_rect1.collidepoint(mouse_pos):
            self.editing_data = True
            self.editing_id = False
            cursor_pos = mouse_pos[0] - (self.data_rect1.x + 5) + self.scroll_x
            font_widths = [font.size(self.data_str[:i])[0] for i in range(len(self.data_str) + 1)]
            self.cursor_position = min(range(len(font_widths)), key=lambda i: abs(font_widths[i] - cursor_pos))
            cursor_pixel = font.size(self.data_str[:self.cursor_position])[0]
            if cursor_pixel > self.data_rect1.width - 10:
                self.scroll_x = cursor_pixel - (self.data_rect1.width - 10)
            else:
                self.scroll_x = 0
        elif self.bool_rect.collidepoint(mouse_pos):
            self.checkSmaller = not self.checkSmaller 
            self.editing_data = True
            self.editing_id = False
        elif self.btn_enter.collidepoint(mouse_pos) and (self.editing_id or self.editing_data):
            return self.confirm()
        return False

    def handle_keydown(self, event) -> None:
        if self.editing_id:
            if event.key == pygame.K_BACKSPACE:
                self.id_str = self.id_str[:-1]
            else:
                self.id_str += event.unicode
        elif self.editing_data:
            if event.key == pygame.K_BACKSPACE:
                if getattr(self, 'cursor_position', 0) > 0:
                    self.data_str = self.data_str[:self.cursor_position - 1] + self.data_str[self.cursor_position:]
                    self.cursor_position -= 1
            elif event.key == pygame.K_LEFT:
                self.cursor_position = max(0, getattr(self, 'cursor_position', 0) - 1)
            elif event.key == pygame.K_RIGHT:
                self.cursor_position = min(len(self.data_str), getattr(self, 'cursor_position', 0) + 1)
            else:
                self.data_str = self.data_str[:getattr(self, 'cursor_position', 0)] + event.unicode + self.data_str[getattr(self, 'cursor_position', 0):]
                self.cursor_position = getattr(self, 'cursor_position', 0) + 1

            cursor_pixel = font.size(self.data_str[:getattr(self, 'cursor_position', 0)])[0]
            visible_width = self.data_rect1.width - 10
            if cursor_pixel - self.scroll_x > visible_width:
                self.scroll_x = cursor_pixel - visible_width
            elif cursor_pixel - self.scroll_x < 0:
                self.scroll_x = cursor_pixel

    def cancel(self):
        self.id_str = self.backup_id
        self.data_str = self.backup_data
        self.checkSmaller = self.backup_checkSmaller
        self.editing_id = False
        self.editing_data = False

    def confirm(self) -> bool:
        global restrictionsList
        if self.index < len(restrictionsList):
            restrictionsList[self.index] = (self.id_str, self.data_str, self.checkSmaller)
        else:
            if self.id_str.strip() != "":
                restrictionsList.append((self.id_str, self.data_str, self.checkSmaller))

        self.backup_id = self.id_str
        self.backup_data = self.data_str
        self.backup_checkSmaller = self.checkSmaller
        self.editing_id = False
        self.editing_data = False

        update_functions()
        return True

class DrawEntryField(FunctionsEntryField):
    """
    Entry field for Draw tab: Func ID, Color ID, Rest ID
    """
    def __init__(self, index: int, list_ref: list):
        super().__init__(index, list_ref)
        if index < len(list_ref):
            self.data_str_c = list_ref[index][1]
            self.data_str_r = list_ref[index][2]
        else:
            self.data_str_c = ""
            self.data_str_r = ""
            
        self.backup_data_c = self.data_str_c
        self.backup_data_r = self.data_str_r

        self.id_rect = pygame.Rect(30, self.y + 10, 60, 30)   # func id
        self.full_data_rect = pygame.Rect(95, self.y + 10, 140, 30)
        self.data_rect1 = pygame.Rect(95, self.y + 10, 65, 30) # color id
        self.data_rect2 = pygame.Rect(165, self.y + 10, 70, 30) # rest id
        self.btn_enter = pygame.Rect(240, self.y + 10, 50, 30)
        self.data_index = 0

    def draw(self, surface: pygame.Surface) -> None:
        is_active = self.editing_id or self.editing_data
        bg_color = INDENT_COLOR if is_active else TEXTBOX_COLOR
        pygame.draw.rect(surface, bg_color, self.rect)
        pygame.draw.rect(surface, (150, 150, 150), self.rect, 1)

        self.y = self.Y + scroll_y_vals[3]
        self.rect.y = self.y
        self.id_rect.y = self.y + 10
        self.data_rect1.y = self.y + 10
        self.data_rect2.y = self.y + 10
        self.full_data_rect.y = self.y + 10
        self.btn_enter.y = self.y + 10

        if self.y + TEXTBOX_HEIGHT < TABS_HEIGHT or self.y > HEIGHT:
            return

        # Status Flag
        flag_color = draw_error_states.get(self.index, ((150, 150, 150), ""))[0]
        pygame.draw.circle(surface, flag_color, (15, self.y + 25), 6)

        # Func ID (stored in id_str basically from super class)
        pygame.draw.rect(surface, (255, 255, 255) if self.editing_id else bg_color, self.id_rect)
        id_surf = font.render(self.id_str, True, TEXT_COLOR)
        surface.blit(id_surf, (self.id_rect.x + 5, self.id_rect.y + 7))

        # Color ID
        pygame.draw.rect(surface, (255, 255, 255) if self.editing_data and self.data_index == 0 else bg_color, self.data_rect1)
        data_surf1 = font.render(self.data_str_c, True, TEXT_COLOR)
        surface.blit(data_surf1, (self.data_rect1.x + 5, self.data_rect1.y + 7))

        # Rest ID
        pygame.draw.rect(surface, (255, 255, 255) if self.editing_data and self.data_index == 1 else bg_color, self.data_rect2)
        data_surf2 = font.render(self.data_str_r, True, TEXT_COLOR)
        surface.blit(data_surf2, (self.data_rect2.x + 5, self.data_rect2.y + 7))

        if is_active:
            pygame.draw.rect(surface, (100, 200, 100), self.btn_enter)
            btn_txt = small_font.render("ENTER", True, (0, 0, 0))
            surface.blit(btn_txt, (self.btn_enter.x + 5, self.btn_enter.y + 10))

        if self.editing_data:
            active_str = self.data_str_c if self.data_index == 0 else self.data_str_r
            active_rect = self.data_rect1 if self.data_index == 0 else self.data_rect2
            cursor_x = active_rect.x + 5 + font.size(active_str[:getattr(self, 'cursor_position', 0)])[0] - self.scroll_x
            cursor_y = active_rect.y + 5
            pygame.draw.line(surface, (0, 0, 0), (cursor_x, cursor_y), (cursor_x, cursor_y + 20), 2)

    def handle_click(self, mouse_pos) -> bool:
        if self.id_rect.collidepoint(mouse_pos):
            self.editing_id = True
            self.editing_data = False
        elif self.full_data_rect.collidepoint(mouse_pos):
            self.editing_data = True
            self.editing_id = False
            if self.data_rect1.collidepoint(mouse_pos):
                self.data_index = 0
                active_rect = self.data_rect1
                active_str = self.data_str_c
            elif self.data_rect2.collidepoint(mouse_pos):
                self.data_index = 1
                active_rect = self.data_rect2
                active_str = self.data_str_r
            else:
                return False

            cursor_pos = mouse_pos[0] - (active_rect.x + 5) + self.scroll_x
            font_widths = [font.size(active_str[:i])[0] for i in range(len(active_str) + 1)]
            self.cursor_position = min(range(len(font_widths)), key=lambda i: abs(font_widths[i] - cursor_pos))
            cursor_pixel = font.size(active_str[:self.cursor_position])[0]
            if cursor_pixel > active_rect.width - 10:
                self.scroll_x = cursor_pixel - (active_rect.width - 10)
            else:
                self.scroll_x = 0
        elif self.btn_enter.collidepoint(mouse_pos) and (self.editing_id or self.editing_data):
            return self.confirm()
        return False

    def handle_keydown(self, event) -> None:
        if self.editing_id:
            if event.key == pygame.K_BACKSPACE:
                self.id_str = self.id_str[:-1]
            else:
                self.id_str += event.unicode
        elif self.editing_data:
            if event.key == pygame.K_BACKSPACE:
                if getattr(self, 'cursor_position', 0) > 0:
                    if self.data_index == 0:
                        self.data_str_c = self.data_str_c[:self.cursor_position - 1] + self.data_str_c[self.cursor_position:]
                    else:
                        self.data_str_r = self.data_str_r[:self.cursor_position - 1] + self.data_str_r[self.cursor_position:]
                    self.cursor_position -= 1
            elif event.key == pygame.K_LEFT:
                self.cursor_position = max(0, getattr(self, 'cursor_position', 0) - 1)
            elif event.key == pygame.K_RIGHT:
                active_str = self.data_str_c if self.data_index == 0 else self.data_str_r
                self.cursor_position = min(len(active_str), getattr(self, 'cursor_position', 0) + 1)
            else:
                if self.data_index == 0:
                    self.data_str_c = self.data_str_c[:getattr(self, 'cursor_position', 0)] + event.unicode + self.data_str_c[getattr(self, 'cursor_position', 0):]
                else:
                    self.data_str_r = self.data_str_r[:getattr(self, 'cursor_position', 0)] + event.unicode + self.data_str_r[getattr(self, 'cursor_position', 0):]
                self.cursor_position = getattr(self, 'cursor_position', 0) + 1

            active_str = self.data_str_c if self.data_index == 0 else self.data_str_r
            active_rect = self.data_rect1 if self.data_index == 0 else self.data_rect2
            cursor_pixel = font.size(active_str[:getattr(self, 'cursor_position', 0)])[0]
            visible_width = active_rect.width - 10

            if cursor_pixel - self.scroll_x > visible_width:
                self.scroll_x = cursor_pixel - visible_width
            elif cursor_pixel - self.scroll_x < 0:
                self.scroll_x = cursor_pixel

    def cancel(self):
        self.id_str = self.backup_id
        self.data_str_c = self.backup_data_c
        self.data_str_r = self.backup_data_r
        self.editing_id = False
        self.editing_data = False

    def confirm(self) -> bool:
        global drawList
        if self.index < len(drawList):
            drawList[self.index] = (self.id_str, self.data_str_c, self.data_str_r)
        else:
            if self.id_str.strip() != "":
                drawList.append((self.id_str, self.data_str_c, self.data_str_r))

        self.backup_id = self.id_str
        self.backup_data_c = self.data_str_c
        self.backup_data_r = self.data_str_r
        self.editing_id = False
        self.editing_data = False

        update_functions()
        return True


def update_functions() -> None:

    """Rebuilds all dictionaries and runs error checking validation."""
    global functionsDict, colorsDict, restrictionsDict, drawFinal, error_states, restriction_error_states, draw_error_states

    functionsDict.clear()
    error_states.clear()
    restriction_error_states.clear()
    draw_error_states.clear()
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
        elif eq.size(functionsDict, MAX_DEPTH) > 100:
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
    for i, x in enumerate(restrictionsList):
        if not x[0]:
            restriction_error_states[i] = ((150, 150, 150), "")
            continue
        if x[0] in restrictionsDict:
            restriction_error_states[i] = ((200, 200, 50), "Duplicate ID")
            continue
        if x[1] not in functionsDict:
            restriction_error_states[i] = ((200, 50, 50), "Function ID not found")
        else:
            restrictionsDict[x[0]] = Boundary(functionsDict[x[1]], x[2])
            restriction_error_states[i] = ((50, 200, 50), "Valid")

    drawFinal.clear()
    for i, x in enumerate(drawList):
        if not x[0]:
            draw_error_states[i] = ((150, 150, 150), "")
            continue
            
        errs = []
        if x[0] not in functionsDict: errs.append("Function ID not found")
        if x[1] not in colorsDict: errs.append("Color ID not found")
        if x[2] not in restrictionsDict: errs.append("Restriction ID not found")
        
        if len(errs) > 0:
            draw_error_states[i] = ((200, 50, 50), ", ".join(errs))
        else:
            drawFinal.append((functionsDict[x[0]], colorsDict[x[1]], restrictionsDict[x[2]]))
            draw_error_states[i] = ((50, 200, 50), "Valid")


def render_grid(surface: pygame.Surface, xpoints: list[float], ypoints: list[float]):
    # TODO: fix the new white lines appearing bug (Lingnan)
    surface.fill((255, 255, 255))
    cell_w = (DRAW_MAX_X - DRAW_MIN_X) / len(xpoints)
    cell_h = (DRAW_MAX_Y - DRAW_MIN_Y) / len(ypoints)
    for i in range(len(xpoints)):
        for j in range(len(ypoints)):
            math_x = xpoints[i]
            math_y = ypoints[j]
            for curFunc in drawFinal:
                if curFunc[2].inBounds(math_x, math_y, ANGLE_MODE, functionsDict, MAX_DEPTH):
                    z = curFunc[0].evaluate(math_x, math_y, ANGLE_MODE, functionsDict, MAX_DEPTH)
                    squarecolor = curFunc[1].getColorTuple(z, ANGLE_MODE, functionsDict, MAX_DEPTH)
                    screen_x = round(DRAW_MIN_X + i * cell_w)
                    next_x = round(DRAW_MIN_X + (i + 1) * cell_w)

                    screen_y_top = round(DRAW_MAX_Y - ((j + 1) * cell_h))
                    screen_y_bottom = round(DRAW_MAX_Y - (j * cell_h))

                    rect_w = max(1, next_x - screen_x)
                    rect_h = max(1, screen_y_bottom - screen_y_top)
                    # break it into x y components and then do a rectangle draw for each one to prevent the white lines from appearing
                    if squarecolor != (-1, -1, -1):
                        pygame.draw.rect(surface, squarecolor, (screen_x, screen_y_top, rect_w, rect_h))


# redraws the functions
def rerender_graph_surface(x_coords, y_coords):
    global GRAPH_SURFACE
    GRAPH_SURFACE = pygame.Surface((WIDTH, HEIGHT))
    GRAPH_SURFACE.fill((255, 255, 255))
    render_grid(GRAPH_SURFACE, x_coords, y_coords)


# Draws the top 5 label things
def render_tab_labels(screen: pygame.Surface, font: pygame.font.Font) -> None:
    for i in range(len(PANELS)):
        rect = pygame.Rect(TABS_WIDTH * i, 0, TABS_WIDTH, TABS_HEIGHT)
        pygame.draw.rect(screen, (225, 225, 225), rect)
        if PANELS[i] == current_panel:
            pygame.draw.rect(screen, (180, 180, 180), rect)
        pygame.draw.rect(screen, (0, 0, 0), rect, 1)
        label = font.render(PANELS[i][:4], True, (0, 0, 0))
        screen.blit(label, (rect.x + 4, rect.y + 15))


# draws a button that you can click
def draw_button(screen: pygame.Surface, font: pygame.font.Font, rect: pygame.Rect, label: str) -> None:
    pygame.draw.rect(screen, (225, 225, 225), rect)
    pygame.draw.rect(screen, (70, 70, 70), rect, 2)
    text_surface = font.render(label, True, (0, 0, 0))
    text_rect = text_surface.get_rect(center=rect.center)
    screen.blit(text_surface, text_rect)


# TODO: the UI for the other 3 tabs (Justin)
# (should probably use something similar to render_tab_labels and draw_button for this?)

# if you need to render a screen make the functions for that screen here
# TODO: update and rework settings overlay (Lingnan)
def render_settings_overlay(screen: pygame.Surface, font: pygame.font.Font) -> None:
    """
    Draw the Settings tab UI inside the fixed left sidebar.


    This version also draws live textbox contents and stores the
    textbox/button rects so they can be clicked and edited.
    """
    global settings_buttons
    settings_buttons = {}

    if current_panel != 'Settings':
        return

    update_settings_error_states()

    panel_rect = pygame.Rect(0, TABS_HEIGHT, TEXTBOX_WIDTH, HEIGHT - TABS_HEIGHT)
    pygame.draw.rect(screen, (220, 230, 240), panel_rect)
    pygame.draw.rect(screen, (70, 70, 70), panel_rect, 1)

    sidebar_w = TEXTBOX_WIDTH
    sidebar_h = HEIGHT - TABS_HEIGHT

    margin_x = 18
    content_w = sidebar_w - 2 * margin_x

    title_font = pygame.font.SysFont(None, max(21, min(25, int(sidebar_h * 0.033))))
    label_font = pygame.font.SysFont(None, max(15, min(18, int(sidebar_h * 0.023))))
    small_label_font = pygame.font.SysFont(None, max(13, min(16, int(sidebar_h * 0.021))))
    button_font = pygame.font.SysFont(None, max(13, min(16, int(sidebar_h * 0.021))))
    text_font = pygame.font.SysFont(None, max(16, min(18, int(sidebar_h * 0.022))))

    section_gap = max(24, min(38, int(sidebar_h * 0.05)))
    row_gap = max(12, min(18, int(sidebar_h * 0.02)))

    col_gap = 10
    col_w = (content_w - 2 * col_gap) // 3

    box_w = max(54, min(84, col_w - 10))
    box_h = 26

    def draw_input_box(field_key: str, x: int, y: int, w: int = box_w, h: int = box_h) -> pygame.Rect:
        """
        Draw one editable settings textbox and its current contents.
        """
        rect = pygame.Rect(x, y, w, h)
        settings_buttons[field_key] = rect

        bg = (255, 255, 255) if active_settings_field == field_key else (235, 240, 246)
        pygame.draw.rect(screen, bg, rect)
        pygame.draw.rect(screen, (95, 95, 95), rect, 2)

        value = settings_values.get(field_key, "")
        text_surface = text_font.render(value, True, (0, 0, 0))
        screen.blit(text_surface, (rect.x + 5, rect.y + 5))

        return rect

    def draw_confirm_button(button_key: str, field_key: str, x: int, y: int, w: int = 46, h: int = 24) -> pygame.Rect:
        """
        Draw a green ENTER button only when its matching textbox is active.
        """
        rect = pygame.Rect(x, y, w, h)
        settings_buttons[button_key] = rect

        # Only show this ENTER button if the user is currently editing this field
        if active_settings_field == field_key:
            pygame.draw.rect(screen, (100, 200, 100), rect)
            pygame.draw.rect(screen, (70, 70, 70), rect, 2)

            btn_txt = button_font.render("ENTER", True, (0, 0, 0))
            screen.blit(btn_txt, btn_txt.get_rect(center=rect.center))

        return rect

    def draw_settings_flag(field_key: str, cx: int, cy: int) -> None:
        """
        Draw a small colored status dot for one settings field.
        """
        color = settings_error_states.get(field_key, ((150, 150, 150), ""))[0]
        pygame.draw.circle(screen, color, (cx, cy), 6)

    def draw_axis_section(start_y: int, axis_label: str, prefix: str) -> int:
        """
        Draw one full axis section (X or Y).
        prefix should be 'x' or 'y' so keys become x_min, x_points, x_max...
        """
        screen.blit(title_font.render(f"{axis_label} axis:", True, (0, 0, 0)), (margin_x, start_y))

        label_y = start_y + 34
        box_y = label_y + 26
        enter_y = box_y + box_h + 12

        col1_x = margin_x
        col2_x = margin_x + col_w + col_gap
        col3_x = margin_x + 2 * (col_w + col_gap)

        screen.blit(label_font.render("Lower bound:", True, (0, 0, 0)), (col1_x, label_y))
        screen.blit(label_font.render("# of points:", True, (0, 0, 0)), (col2_x, label_y))
        screen.blit(label_font.render("Upper bound:", True, (0, 0, 0)), (col3_x, label_y))

        box1_x = col1_x + (col_w - box_w) // 2
        box2_x = col2_x + (col_w - box_w) // 2
        box3_x = col3_x + (col_w - box_w) // 2

        draw_input_box(f"{prefix}_min", box1_x, box_y)
        draw_input_box(f"{prefix}_points", box2_x, box_y)
        draw_input_box(f"{prefix}_max", box3_x, box_y)

        # Small colored flags beside each textbox
        draw_settings_flag(f"{prefix}_min", box1_x - 10, box_y + box_h // 2)
        draw_settings_flag(f"{prefix}_points", box2_x - 10, box_y + box_h // 2)
        draw_settings_flag(f"{prefix}_max", box3_x - 10, box_y + box_h // 2)

        enter_w = 46
        enter_h = 24
        draw_confirm_button(f"{prefix}_min_enter", f"{prefix}_min", box1_x + (box_w - enter_w) // 2, enter_y, enter_w,
                            enter_h)
        draw_confirm_button(f"{prefix}_points_enter", f"{prefix}_points", box2_x + (box_w - enter_w) // 2, enter_y,
                            enter_w, enter_h)
        draw_confirm_button(f"{prefix}_max_enter", f"{prefix}_max", box3_x + (box_w - enter_w) // 2, enter_y, enter_w,
                            enter_h)

        return enter_y + enter_h + section_gap

    def draw_current_mode_row(y: int) -> int:
        """
        Draw current angle mode on the left and a mode-toggle button on the right.
        """
        left_x = margin_x
        control_w = 96
        control_h = 32
        control_x = sidebar_w - margin_x - control_w

        screen.blit(label_font.render("Current mode:", True, (0, 0, 0)), (left_x, y))
        screen.blit(label_font.render(ANGLE_MODE, True, (0, 0, 0)), (left_x, y + 20))

        button_text = "Use degrees" if ANGLE_MODE == "radians" else "Use radians"

        btn_rect = pygame.Rect(control_x, y + 1, control_w, control_h)
        settings_buttons["angle_toggle"] = btn_rect
        draw_button(screen, button_font, btn_rect, button_text)

        return y + 44

    def draw_max_depth_row(y: int) -> int:
        """
        Draw max recursive depth row with editable box and ENTER button.
        """
        left_x = margin_x

        screen.blit(small_label_font.render("Maximum recursive", True, (0, 0, 0)), (left_x, y + 2))
        screen.blit(small_label_font.render("depth:", True, (0, 0, 0)), (left_x, y + 18))

        input_w = 52
        input_h = 28
        enter_w = 46
        enter_h = 24
        gap = 8
        right_margin = 12

        enter_x = sidebar_w - right_margin - enter_w
        box_x = enter_x - gap - input_w
        box_y = y + 8

        draw_input_box("max_recursion", box_x, box_y, input_w, input_h)
        draw_settings_flag("max_recursion", box_x - 10, box_y + input_h // 2)
        draw_confirm_button("max_recursion_enter", "max_recursion", enter_x, box_y + (input_h - enter_h) // 2, enter_w,
                            enter_h)

        return y + 48

    current_y = TABS_HEIGHT + 14
    current_y = draw_axis_section(current_y, "X", "x")
    current_y = draw_axis_section(current_y, "Y", "y")
    current_y += 2
    current_y = draw_current_mode_row(current_y)
    current_y += row_gap
    current_y = draw_max_depth_row(current_y + 4)

    bottom_y = HEIGHT - 46
    settings_buttons["size_prev"] = pygame.Rect(margin_x, bottom_y, 36, 26)
    settings_buttons["size_next"] = pygame.Rect(margin_x + 44, bottom_y, 36, 26)

    draw_button(screen, button_font, settings_buttons["size_prev"], "<")
    draw_button(screen, button_font, settings_buttons["size_next"], ">")


def apply_settings_from_text() -> None:
    """
    Read the text from the Settings tab textboxes and apply them.


    Large grids are allowed.
    Only clamp when total grid points exceed MAX_TOTAL_GRID_POINTS.


    If the total is too large, clamp the field the user is currently editing.
    """
    global X_GRID_RESOLUTION, X_MATH_MIN, X_MATH_MAX
    global Y_GRID_RESOLUTION, Y_MATH_MIN, Y_MATH_MAX
    global xstep, ystep, x_coords, y_coords, MAX_DEPTH

    try:
        new_x_min = float(settings_values["x_min"])
        new_x_max = float(settings_values["x_max"])
        new_x_points = int(settings_values["x_points"])

        new_y_min = float(settings_values["y_min"])
        new_y_max = float(settings_values["y_max"])
        new_y_points = int(settings_values["y_points"])

        new_max_depth = int(settings_values["max_recursion"])

        if new_x_points <= 0 or new_y_points <= 0:
            update_settings_error_states()
            return
        if new_x_min >= new_x_max or new_y_min >= new_y_max:
            update_settings_error_states()
            return
        if new_max_depth < 0:
            update_settings_error_states()
            return

        total_points = new_x_points * new_y_points

        if total_points > MAX_TOTAL_GRID_POINTS:
            # Clamp whichever field is currently being edited
            if active_settings_field == "x_points":
                new_x_points = max(1, MAX_TOTAL_GRID_POINTS // new_y_points)
            elif active_settings_field == "y_points":
                new_y_points = max(1, MAX_TOTAL_GRID_POINTS // new_x_points)
            else:
                # fallback: clamp y if we don't know which one caused it
                new_y_points = max(1, MAX_TOTAL_GRID_POINTS // new_x_points)

            # Sync the textboxes to the clamped values
            settings_values["x_points"] = str(new_x_points)
            settings_values["y_points"] = str(new_y_points)

        X_MATH_MIN = new_x_min
        X_MATH_MAX = new_x_max
        X_GRID_RESOLUTION = new_x_points

        Y_MATH_MIN = new_y_min
        Y_MATH_MAX = new_y_max
        Y_GRID_RESOLUTION = new_y_points

        MAX_DEPTH = new_max_depth
        settings_values["max_recursion"] = str(MAX_DEPTH)

        xstep = (X_MATH_MAX - X_MATH_MIN) / X_GRID_RESOLUTION
        ystep = (Y_MATH_MAX - Y_MATH_MIN) / Y_GRID_RESOLUTION

        x_coords = [X_MATH_MIN + 1 + i * xstep for i in range(X_GRID_RESOLUTION)]
        y_coords = [Y_MATH_MIN + j * ystep for j in range(Y_GRID_RESOLUTION)]

        update_settings_error_states()
        rerender_graph_surface(x_coords, y_coords)


    except ValueError:
        update_settings_error_states()


def handle_settings_textbox_click(mouse_pos) -> None:
    """
    Activate whichever settings textbox was clicked.
    """
    global active_settings_field

    textbox_keys = [
        "x_min", "x_points", "x_max",
        "y_min", "y_points", "y_max",
        "max_recursion"
    ]

    active_settings_field = None
    for key in textbox_keys:
        if key in settings_buttons and settings_buttons[key].collidepoint(mouse_pos):
            active_settings_field = key
            break


def handle_settings_keydown(event) -> None:
    """
    Send keyboard input into the currently active settings textbox.
    """
    global active_settings_field

    if active_settings_field is None:
        return

def update_settings_error_states() -> None:
    """
    Rebuild the color state for settings fields.


    Meanings:
    - Red: invalid
    - Blue: warning
    - Green: normal valid
    - Grey: blank / can't evaluate yet
    """
    global settings_error_states
    settings_error_states = {}

    GREY = (150, 150, 150)
    RED = (200, 50, 50)
    BLUE = (50, 100, 200)
    GREEN = (50, 200, 50)

    keys = ["x_min", "x_points", "x_max", "y_min", "y_points", "y_max", "max_recursion"]

    for key in keys:
        settings_error_states[key] = (GREY, "")

    # X bounds
    try:
        x_min = float(settings_values["x_min"])
        x_max = float(settings_values["x_max"])
        if x_min > x_max:
            settings_error_states["x_min"] = (RED, "Lower bound is greater than upper bound.")
            settings_error_states["x_max"] = (RED, "Upper bound is less than lower bound.")
        else:
            settings_error_states["x_min"] = (GREEN, "Valid")
            settings_error_states["x_max"] = (GREEN, "Valid")
    except ValueError:
        pass

    # Y bounds
    try:
        y_min = float(settings_values["y_min"])
        y_max = float(settings_values["y_max"])
        if y_min > y_max:
            settings_error_states["y_min"] = (RED, "Lower bound is greater than upper bound.")
            settings_error_states["y_max"] = (RED, "Upper bound is less than lower bound.")
        else:
            settings_error_states["y_min"] = (GREEN, "Valid")
            settings_error_states["y_max"] = (GREEN, "Valid")
    except ValueError:
        pass

    # X points
    try:
        x_points = int(settings_values["x_points"])
        if x_points > 0:
            settings_error_states["x_points"] = (GREEN, "Valid")
    except ValueError:
        pass

    # Y points
    try:
        y_points = int(settings_values["y_points"])
        if y_points > 0:
            settings_error_states["y_points"] = (GREEN, "Valid")
    except ValueError:
        pass

    # Total grid size warning / hard max
    try:
        x_points = int(settings_values["x_points"])
        y_points = int(settings_values["y_points"])
        total_points = x_points * y_points

        if x_points > 0 and y_points > 0:
            if total_points > MAX_TOTAL_GRID_POINTS:
                settings_error_states["x_points"] = (BLUE, "Total grid exceeds hard limit and will be clamped.")
                settings_error_states["y_points"] = (BLUE, "Total grid exceeds hard limit and will be clamped.")
            elif total_points > WARNING_TOTAL_GRID_POINTS:
                settings_error_states["x_points"] = (BLUE, "Total grid is very large.")
                settings_error_states["y_points"] = (BLUE, "Total grid is very large.")
    except ValueError:
        pass

    # Max recursion
    try:
        max_depth = int(settings_values["max_recursion"])
        if max_depth < 0:
            settings_error_states["max_recursion"] = (GREY, "")
        elif max_depth < 3 or max_depth > 20:
            settings_error_states["max_recursion"] = (BLUE, "Recursion depth is outside the normal range.")
        else:
            settings_error_states["max_recursion"] = (GREEN, "Valid")
    except ValueError:
        pass


def apply_screen_size_from_index(index: int, xrange: float, yrange: float) -> None:
    global SCREEN_SIZE_INDEX, WIDTH, HEIGHT
    SCREEN_SIZE_INDEX = index % len(SCREEN_SIZE_OPTIONS)
    WIDTH, HEIGHT = SCREEN_SIZE_OPTIONS[SCREEN_SIZE_INDEX]
    calculate_draw_bounds(xrange, yrange)


# --- MAIN EXECUTION ---
if __name__ == "__main__":
    X_GRID_RESOLUTION = 100
    X_MATH_MIN, X_MATH_MAX = -15.0, 15.0
    Y_GRID_RESOLUTION = 100
    Y_MATH_MIN, Y_MATH_MAX = -15.0, 15.0
    calculate_draw_bounds(X_MATH_MAX - X_MATH_MIN, Y_MATH_MAX - Y_MATH_MIN)
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("Render Engine")

    settings_values["x_min"] = str(X_MATH_MIN)
    settings_values["x_points"] = str(X_GRID_RESOLUTION)
    settings_values["x_max"] = str(X_MATH_MAX)
    settings_values["y_min"] = str(Y_MATH_MIN)
    settings_values["y_points"] = str(Y_GRID_RESOLUTION)
    settings_values["y_max"] = str(Y_MATH_MAX)
    settings_values["max_recursion"] = str(MAX_DEPTH)
    update_settings_error_states()
    xstep = (X_MATH_MAX - X_MATH_MIN) / X_GRID_RESOLUTION
    # HOLY SHIT IS THAT A GEOMETRY DASH REFERENCE???????????
    ystep = (Y_MATH_MAX - Y_MATH_MIN) / Y_GRID_RESOLUTION
    x_coords = [X_MATH_MIN + 1 + i * xstep for i in range(X_GRID_RESOLUTION)]
    y_coords = [Y_MATH_MIN + j * ystep for j in range(Y_GRID_RESOLUTION)]

    # Generate a static surface to hold the math grid so UI doesn't lag

    update_functions()
    if len(functionsList) > 0:
        AST_SELECTED_ID = functionsList[0][0]
    rerender_graph_surface(x_coords, y_coords)

    function_ui_fields = [FunctionsEntryField(i, functionsList) for i in range(len(functionsList) + 1)]
    colors_ui_fields = [ColorsEntryField(i, colorsList) for i in range(len(colorsList) + 1)]

    rest_ui_fields = [RestrictionsEntryField(i, restrictionsList) for i in range(len(restrictionsList) + 1)]
    draw_ui_fields = [DrawEntryField(i, drawList) for i in range(len(drawList) + 1)]

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
                calculate_draw_bounds(X_MATH_MAX - X_MATH_MIN, Y_MATH_MAX - Y_MATH_MIN)  # Recalculate aspect ratio
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
                        scroll_y_vals[0] = min(0, scroll_y_vals[0] + 5)

                    clicked_any_field = False

                    for field in function_ui_fields:
                        # TODO: allow users to move around entry fields (applies for all 4 tabs) and when one gets deleted, it removes that text thing and shifts the others (M)
                        if field.rect.collidepoint(mouse_pos):
                            clicked_any_field = True
                            needs_redraw = field.handle_click(mouse_pos)

                            # If confirmed, recalculate grid and regenerate UI list to add the next empty block
                            if needs_redraw:
                                print("Recalculating Math...")

                                rerender_graph_surface(x_coords, y_coords)
                                function_ui_fields = [FunctionsEntryField(i, functionsList) for i in range(len(functionsList) + 1)]

                        else:
                            # If they clicked another field, cancel the edit on this one
                            if field.editing_id or field.editing_data:
                                field.cancel()

                    # If they clicked entirely outside the UI sidebar, cancel everything
                    if not clicked_any_field:
                        for field in function_ui_fields: field.cancel()

                # TODO: the other 3 panels (Justin)
                if current_panel == 'Colors':
                    if event.button == 4:       # scroll up
                        scroll_y_vals[1] -= 5
                    elif event.button == 5:     # scroll down
                        scroll_y_vals[1] = min(0, scroll_y_vals[1] + 5)

                    clicked_any_field = False
                    for field in colors_ui_fields:
                        if field.rect.collidepoint(mouse_pos):
                            clicked_any_field = True
                            needs_redraw = field.handle_click(mouse_pos)
                            if needs_redraw:
                                rerender_graph_surface(x_coords, y_coords)
                                colors_ui_fields = [ColorsEntryField(i, colorsList) for i in range(len(colorsList) + 1)]
                        else:
                            if field.editing_id or field.editing_data:
                                field.cancel()
                    if not clicked_any_field:
                        for field in colors_ui_fields: field.cancel()

                if current_panel == 'Restrictions':
                    if event.button == 4:       # scroll up
                        scroll_y_vals[2] -= 5
                    elif event.button == 5:     # scroll down
                        scroll_y_vals[2] = min(0, scroll_y_vals[2] + 5)

                    clicked_any_field = False
                    for field in rest_ui_fields:
                        if field.rect.collidepoint(mouse_pos):
                            clicked_any_field = True
                            needs_redraw = field.handle_click(mouse_pos)
                            if needs_redraw:
                                calculate_draw_bounds(X_MATH_MAX - X_MATH_MIN, Y_MATH_MAX - Y_MATH_MIN)
                                rerender_graph_surface(x_coords, y_coords)
                                rest_ui_fields = [RestrictionsEntryField(i, restrictionsList) for i in range(len(restrictionsList) + 1)]
                        else:
                            if field.editing_id or getattr(field, 'editing_data', False):
                                field.cancel()
                    if not clicked_any_field:
                        for field in rest_ui_fields: field.cancel()

                if current_panel == 'Draw':
                    if event.button == 4:       # scroll up
                        scroll_y_vals[3] -= 5
                    elif event.button == 5:     # scroll down
                        scroll_y_vals[3] = min(0, scroll_y_vals[3] + 5)

                    clicked_any_field = False
                    for field in draw_ui_fields:
                        if field.rect.collidepoint(mouse_pos):
                            clicked_any_field = True
                            needs_redraw = field.handle_click(mouse_pos)
                            if needs_redraw:
                                calculate_draw_bounds(X_MATH_MAX - X_MATH_MIN, Y_MATH_MAX - Y_MATH_MIN)
                                rerender_graph_surface(x_coords, y_coords)
                                draw_ui_fields = [DrawEntryField(i, drawList) for i in range(len(drawList) + 1)]
                        else:
                            if field.editing_id or getattr(field, 'editing_data', False):
                                field.cancel()
                    if not clicked_any_field:
                        for field in draw_ui_fields: field.cancel()

                if current_panel == 'Settings':
                    # 1. First check the ENTER button for the currently active field
                    if active_settings_field is not None:
                        active_enter_key = f"{active_settings_field}_enter"
                        if settings_buttons.get(active_enter_key) and settings_buttons[active_enter_key].collidepoint(
                                mouse_pos):
                            calculate_draw_bounds(X_MATH_MAX - X_MATH_MIN, Y_MATH_MAX - Y_MATH_MIN)
                            apply_settings_from_text()
                            active_settings_field = None
                            continue

                    # 2. Then check angle toggle
                    if settings_buttons.get("angle_toggle") and settings_buttons["angle_toggle"].collidepoint(
                            mouse_pos):
                        ANGLE_MODE = "degrees" if ANGLE_MODE == "radians" else "radians"
                        update_functions()
                        rerender_graph_surface(x_coords, y_coords)
                        active_settings_field = None
                        continue

                    # 3. Screen size buttons
                    if settings_buttons.get("size_prev") and settings_buttons["size_prev"].collidepoint(mouse_pos):
                        calculate_draw_bounds(X_MATH_MAX - X_MATH_MIN, Y_MATH_MAX - Y_MATH_MIN)
                        apply_screen_size_from_index(SCREEN_SIZE_INDEX - 1, X_MATH_MAX - X_MATH_MIN,
                                                     Y_MATH_MAX - Y_MATH_MIN)
                        screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
                        rerender_graph_surface(x_coords, y_coords)
                        active_settings_field = None
                        continue

                    if settings_buttons.get("size_next") and settings_buttons["size_next"].collidepoint(mouse_pos):
                        calculate_draw_bounds(X_MATH_MAX - X_MATH_MIN, Y_MATH_MAX - Y_MATH_MIN)
                        apply_screen_size_from_index(SCREEN_SIZE_INDEX + 1, X_MATH_MAX - X_MATH_MIN,
                                                     Y_MATH_MAX - Y_MATH_MIN)
                        screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
                        rerender_graph_surface(x_coords, y_coords)
                        active_settings_field = None
                        continue

                    # 4. Finally, if none of the above were clicked, activate a textbox
                    handle_settings_textbox_click(mouse_pos)

            if event.type == pygame.KEYDOWN:
                if current_panel == 'Functions':
                    for field in function_ui_fields:
                        field.handle_keydown(event)
                elif current_panel == 'Colors':
                    for field in colors_ui_fields:
                        field.handle_keydown(event)
                elif current_panel == 'Restrictions':
                    for field in rest_ui_fields:
                        field.handle_keydown(event)
                elif current_panel == 'Draw':
                    for field in draw_ui_fields:
                        field.handle_keydown(event)
                elif current_panel == 'Settings':
                    handle_settings_keydown(event)
        # 4. DRAW APPROPRIATE UI OVERLAYS
        if current_panel == 'Functions':
            for field in function_ui_fields:
                field.draw(screen)
            # pygame.draw.rect(screen, (225, 225, 225), toggle_ast_button)
            # pygame.draw.rect(screen, (0, 0, 0), toggle_ast_button, 2)
            # label = font.render("Toggle AST", True, (0, 0, 0))
            # screen.blit(label, (195, 7))

        elif current_panel == 'Colors':
            for field in colors_ui_fields:
                field.draw(screen)

        elif current_panel == 'Restrictions':
            for field in rest_ui_fields:
                field.draw(screen)
                
        elif current_panel == 'Draw':
            for field in draw_ui_fields:
                field.draw(screen)

        elif current_panel == 'Settings':
            render_settings_overlay(screen, font)

        # 2. DRAW UI TABS AND ACTIVE PANEL BACKGROUND
        render_tab_labels(screen, font)

        pygame.display.flip()

    pygame.quit()
    sys.exit()
