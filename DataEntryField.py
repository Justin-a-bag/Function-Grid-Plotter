import pygame
from Visualizer import TEXTBOX_Y, TEXTBOX_HEIGHT, TEXTBOX_WIDTH


class DataEntryField:
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

        # Backups for when the user clicks off (Cancels)
        self.backup_id = self.id_str
        self.backup_data = self.data_str

        # State flags
        self.editing_id = False
        self.editing_data = False

    def draw(self, surface: pygame.Surface):
        raise NotImplementedError()

    def handle_click(self, mouse_pos) -> bool:
        """Returns True if the 'Enter' button was clicked and confirmed."""
        raise NotImplementedError()

    def handle_keydown(self, event):
        raise NotImplementedError()

    def cancel(self):
        """Reverts the field to what it had originally without changing data."""
        self.id_str = self.backup_id
        self.data_str = self.backup_data
        self.editing_id = False
        self.editing_data = False

    def confirm(self) -> bool:
        """Changes list indices and triggers dict rebuild."""
        raise NotImplementedError()
