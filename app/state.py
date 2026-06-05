from enum import Enum

class Tool(Enum):
    SELECT = "Select"
    HIGHLIGHT = "Highlight"
    PEN = "Pen"
    TEXT = "Text"
    SQUARE = "Square"
    ARROW = "Arrow"
    ERASER = "Eraser"

# Define 5 lightened/pastel colors as RGB floats for PyMuPDF and ints for QColor
# Arranged as requested: Yellow, Blue, Green, Red, Black
COLORS = {
    1: {"name": "Yellow", "pdf": (1.0, 0.98, 0.75), "rgb": (255, 250, 190)},
    2: {"name": "Blue",   "pdf": (0.59, 0.82, 1.0),  "rgb": (150, 210, 255)},
    3: {"name": "Green",  "pdf": (0.57, 0.94, 0.67), "rgb": (145, 240, 170)},
    4: {"name": "Red",    "pdf": (0.99, 0.59, 0.59), "rgb": (252, 150, 150)},
    5: {"name": "Black",  "pdf": (0.0, 0.0, 0.0),    "rgb": (0, 0, 0)},
}

class AppState:
    def __init__(self):
        self._active_tool = Tool.SELECT
        self._active_color_index = 1  # Default to Yellow
        self.active_font_size = 12  # Default font size for text annotations
        self.active_line_width = 2  # Default line width for drawings (Pen/Shapes)
        self.rect_select_mode = False  # Toggle for rectangle selection mode
        
        # Tool-specific last-used colors map
        self.tool_colors = {
            Tool.HIGHLIGHT: 1, # Default: Yellow
            Tool.PEN: 2,       # Default: Blue
            Tool.TEXT: 5,      # Default: Black
            Tool.SQUARE: 4,    # Default: Red
            Tool.ARROW: 4,     # Default: Red
        }
        
    @property
    def active_tool(self):
        return self._active_tool

    @active_tool.setter
    def active_tool(self, tool):
        self._active_tool = tool
        if tool in self.tool_colors:
            self._active_color_index = self.tool_colors[tool]

    @property
    def active_color_index(self):
        return self._active_color_index

    @active_color_index.setter
    def active_color_index(self, index):
        self._active_color_index = index
        if self._active_tool in self.tool_colors:
            self.tool_colors[self._active_tool] = index

    @property
    def active_color_pdf(self):
        return COLORS[self.active_color_index]["pdf"]
        
    @property
    def active_color_rgb(self):
        return COLORS[self.active_color_index]["rgb"]

    @property
    def active_color_name(self):
        return COLORS[self.active_color_index]["name"]
