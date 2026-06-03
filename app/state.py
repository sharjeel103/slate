from enum import Enum

class Tool(Enum):
    SELECT = "Select"
    HIGHLIGHT = "Highlight"
    PEN = "Pen"
    TEXT = "Text"
    ERASER = "Eraser"

# Define 5 lightened/pastel colors as RGB floats for PyMuPDF and ints for QColor
COLORS = {
    1: {"name": "Yellow", "pdf": (1.0, 0.93, 0.44), "rgb": (253, 237, 112)},
    2: {"name": "Red",    "pdf": (0.98, 0.48, 0.48), "rgb": (250, 122, 122)},
    3: {"name": "Green",  "pdf": (0.46, 0.90, 0.58), "rgb": (117, 230, 148)},
    4: {"name": "Blue",   "pdf": (0.48, 0.76, 1.0),  "rgb": (122, 194, 255)},
    5: {"name": "Black",  "pdf": (0.0, 0.0, 0.0),  "rgb": (0, 0, 0)},
}

class AppState:
    def __init__(self):
        self.active_tool = Tool.SELECT
        self.active_color_index = 1  # Default to Yellow
        self.active_font_size = 12  # Default font size for text annotations
        self.rect_select_mode = False  # Toggle for rectangle selection mode
        
    @property
    def active_color_pdf(self):
        return COLORS[self.active_color_index]["pdf"]
        
    @property
    def active_color_rgb(self):
        return COLORS[self.active_color_index]["rgb"]

    @property
    def active_color_name(self):
        return COLORS[self.active_color_index]["name"]
