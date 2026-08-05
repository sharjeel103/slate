from enum import Enum

class Tool(Enum):
    SELECT = "Select"
    HIGHLIGHT = "Highlight"
    CALLOUT = "Callout"
    PEN = "Pen"
    TEXT = "Text"
    SQUARE = "Square"
    ARROW = "Arrow"
    ERASER = "Eraser"
    LINE = "Line"

# Define 5 lightened/pastel colors as RGB floats for PyMuPDF and ints for QColor
# Arranged as requested: Yellow, Blue, Green, Red, Black
COLORS = {
    1: {
        "name": "Yellow", 
        "shades": [
            {"pdf": (1.0, 1.0, 0.0),    "rgb": (255, 255, 0)},   # Pure
            {"pdf": (1.0, 1.0, 0.5),    "rgb": (255, 255, 128)}, # Medium
            {"pdf": (1.0, 1.0, 0.75),   "rgb": (255, 255, 192)}  # Light
        ]
    },
    2: {
        "name": "Blue",
        "shades": [
            {"pdf": (0.0, 0.5, 1.0),    "rgb": (0, 128, 255)},   # Pure
            {"pdf": (0.5, 0.75, 1.0),   "rgb": (128, 192, 255)}, # Medium
            {"pdf": (0.75, 0.88, 1.0),  "rgb": (192, 224, 255)}  # Light
        ]
    },
    3: {
        "name": "Green",
        "shades": [
            {"pdf": (0.0, 0.8, 0.0),    "rgb": (0, 204, 0)},     # Pure
            {"pdf": (0.5, 0.9, 0.5),    "rgb": (128, 230, 128)}, # Medium
            {"pdf": (0.75, 0.95, 0.75), "rgb": (192, 242, 192)}  # Light
        ]
    },
    4: {
        "name": "Red",
        "shades": [
            {"pdf": (1.0, 0.0, 0.0),    "rgb": (255, 0, 0)},     # Pure
            {"pdf": (1.0, 0.5, 0.5),    "rgb": (255, 128, 128)}, # Medium
            {"pdf": (1.0, 0.75, 0.75),  "rgb": (255, 192, 192)}  # Light
        ]
    },
    5: {
        "name": "Black",
        "shades": [
            {"pdf": (0.0, 0.0, 0.0),    "rgb": (0, 0, 0)},       # Black
            {"pdf": (0.3, 0.3, 0.3),    "rgb": (76, 76, 76)},    # Dark Gray
            {"pdf": (0.6, 0.6, 0.6),    "rgb": (153, 153, 153)}  # Light Gray
        ]
    }
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
            Tool.CALLOUT: 4,   # Default: Red
            Tool.LINE: 4,      # Default: Red
        }
        
        # Shade preferences per tool (index 0=Dark, 1=Medium, 2=Light/Gray)
        self.tool_shade_prefs = {tool: 1 for tool in Tool}
        self.tool_shade_prefs[Tool.TEXT] = 0
        self.tool_shade_prefs[Tool.PEN] = 1
        self.tool_shade_prefs[Tool.LINE] = 1
        
        self.load_prefs()

    def save_prefs(self):
        import json
        import os
        config_dir = os.path.expanduser("~/.config/slate")
        os.makedirs(config_dir, exist_ok=True)
        path = os.path.join(config_dir, "prefs.json")
        
        prefs = {
            "font_size": self.active_font_size,
            "line_width": self.active_line_width,
            "tool_colors": {t.name: c for t, c in self.tool_colors.items()},
            "tool_shades": {t.name: s for t, s in self.tool_shade_prefs.items()}
        }
        try:
            with open(path, "w") as f:
                json.dump(prefs, f)
        except Exception as e:
            print(f"Error saving preferences: {e}")

    def load_prefs(self):
        import json
        import os
        path = os.path.expanduser("~/.config/slate/prefs.json")
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    prefs = json.load(f)
                    
                if "font_size" in prefs:
                    self.active_font_size = prefs["font_size"]
                if "line_width" in prefs:
                    self.active_line_width = prefs["line_width"]
                    
                if "tool_colors" in prefs:
                    for t_name, color_idx in prefs["tool_colors"].items():
                        try:
                            tool = Tool[t_name]
                            self.tool_colors[tool] = color_idx
                        except KeyError:
                            pass
                            
                if "tool_shades" in prefs:
                    for t_name, shade_idx in prefs["tool_shades"].items():
                        try:
                            tool = Tool[t_name]
                            self.tool_shade_prefs[tool] = shade_idx
                        except KeyError:
                            pass
            except Exception as e:
                print(f"Error loading preferences: {e}")
                
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
    def active_shade_index(self):
        return self.tool_shade_prefs.get(self.active_tool, 1)

    @active_shade_index.setter
    def active_shade_index(self, shade_idx):
        self.tool_shade_prefs[self.active_tool] = shade_idx
        
    @property
    def active_color_pdf(self):
        return COLORS[self.active_color_index]["shades"][self.active_shade_index]["pdf"]
        
    @property
    def active_color_rgb(self):
        return COLORS[self.active_color_index]["shades"][self.active_shade_index]["rgb"]

    @property
    def active_color_name(self):
        return COLORS[self.active_color_index]["name"]
