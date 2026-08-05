from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QToolBar, QFileDialog, QLabel, QScrollArea, QStatusBar, QPushButton, QButtonGroup, QSizePolicy, QSpinBox, QSplitter, QTreeWidget, QTreeWidgetItem, QLineEdit, QMenu, QWidgetAction
from PyQt6.QtGui import QAction, QKeySequence, QIcon, QColor, QFont, QShortcut
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QPoint
import os

class SearchLineEdit(QLineEdit):
    esc_pressed = pyqtSignal()
    shift_enter_pressed = pyqtSignal()
    enter_pressed = pyqtSignal()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.esc_pressed.emit()
            event.accept()
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self.shift_enter_pressed.emit()
            else:
                self.enter_pressed.emit()
            event.accept()
        else:
            super().keyPressEvent(event)

class PDFSearchBar(QWidget):
    search_requested = pyqtSignal(str)
    next_match = pyqtSignal()
    prev_match = pyqtSignal()
    closed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SearchBar")
        
        self.setStyleSheet("""
            QWidget#SearchBar {
                background-color: #1f2937; /* Gray 800 */
                border: 1px solid #374151; /* Gray 700 */
                border-radius: 8px;
            }
            QLineEdit {
                background-color: #374151; /* Gray 700 */
                color: #f3f4f6; /* Gray 100 */
                border: 1px solid #4b5563; /* Gray 600 */
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 13px;
                min-width: 180px;
            }
            QLineEdit:focus {
                border: 1px solid #3b82f6; /* Blue 500 */
            }
            QLabel {
                color: #9ca3af; /* Gray 400 */
                font-size: 12px;
                margin: 0 8px;
            }
            QPushButton {
                background-color: transparent;
                color: #d1d5db; /* Gray 300 */
                border: none;
                border-radius: 4px;
                min-width: 24px;
                max-width: 24px;
                min-height: 24px;
                max-height: 24px;
                padding: 0;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #374151; /* Gray 700 */
                color: #ffffff;
            }
            QPushButton:pressed {
                background-color: #4b5563; /* Gray 600 */
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        self.input_field = SearchLineEdit(self)
        self.input_field.setPlaceholderText("Find in document...")
        layout.addWidget(self.input_field)

        self.status_label = QLabel("0 of 0", self)
        layout.addWidget(self.status_label)

        self.btn_prev = QPushButton("↑", self)
        self.btn_prev.setToolTip("Previous match (Shift+Enter)")
        layout.addWidget(self.btn_prev)

        self.btn_next = QPushButton("↓", self)
        self.btn_next.setToolTip("Next match (Enter)")
        layout.addWidget(self.btn_next)

        self.btn_close = QPushButton("✕", self)
        self.btn_close.setToolTip("Close search (Esc)")
        layout.addWidget(self.btn_close)

        self.input_field.textChanged.connect(self.on_text_changed)
        self.input_field.enter_pressed.connect(self.next_match.emit)
        self.input_field.shift_enter_pressed.connect(self.prev_match.emit)
        self.input_field.esc_pressed.connect(self.close_search)
        
        self.btn_prev.clicked.connect(self.prev_match.emit)
        self.btn_next.clicked.connect(self.next_match.emit)
        self.btn_close.clicked.connect(self.close_search)

    def on_text_changed(self, text):
        self.search_requested.emit(text)

    def update_status(self, current, total):
        if total == 0:
            self.status_label.setText("0 of 0")
        else:
            self.status_label.setText(f"{current} of {total}")

    def close_search(self):
        self.hide()
        self.closed.emit()


from app.state import AppState, Tool, COLORS
from app.annotator import PDFDocument
from app.pdf_viewer import PDFViewer

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.state = AppState()
        self.pdf_doc = None
        self.is_dirty = False
        self.pre_ctrl_tool = None
        
        self.setWindowTitle("Slate")
        self.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), "app_icon.png")))
        
        # Apply premium dark theme stylesheet
        self.setStyleSheet("""
            QMainWindow {
                background-color: #111827; /* Tailwind Gray 900 */
            }
            QToolBar {
                background-color: #1f2937; /* Tailwind Gray 800 */
                border-right: 1px solid #374151; /* Tailwind Gray 700 */
                spacing: 8px;
                padding: 6px;
                min-width: 40px;
                max-width: 40px;
            }
            QStatusBar {
                background-color: #1f2937;
                color: #9ca3af;
                border-top: 1px solid #374151;
            }
            QLabel {
                color: #e5e7eb;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QScrollArea {
                border: none;
                background-color: #111827;
            }
            /* Custom styled tool buttons */
            QPushButton {
                background-color: #374151;
                color: #e5e7eb;
                border: 1px solid #4b5563;
                border-radius: 6px;
                padding: 6px 16px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #4b5563;
                border-color: #9ca3af;
            }
            /* Style specific to toolbar buttons */
            QToolBar QPushButton {
                min-width: 28px;
                max-width: 28px;
                min-height: 28px;
                max-height: 28px;
                padding: 0;
                font-size: 14px;
            }
            QToolBar QPushButton:checked {
                background-color: #3b82f6; /* Accent Blue */
                border-color: #60a5fa;
                color: white;
            }
            /* Color circle badges */
            QPushButton#color_btn {
                min-width: 24px;
                max-width: 24px;
                min-height: 24px;
                max-height: 24px;
                border-radius: 12px;
                border: 2px solid transparent;
                padding: 0;
                margin-left: 2px;
            }
            QPushButton#color_btn:checked {
                border: 2px solid white;
            }
            /* Style for spinboxes (font size / page) */
            QSpinBox {
                background-color: #374151;
                color: #e5e7eb;
                border: 1px solid #4b5563;
                border-radius: 6px;
                font-size: 11px;
                font-weight: bold;
            }
        """)

        # Main layout
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        
        layout = QVBoxLayout(self.central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Horizontal Splitter for Outline Sidebar & PDF Viewer
        self.splitter = QSplitter(Qt.Orientation.Horizontal, self)
        self.splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #374151;
                width: 2px;
            }
        """)
        
        # Outline Sidebar widget
        self.outline_tree = QTreeWidget(self)
        self.outline_tree.setHeaderHidden(True)
        self.outline_tree.setObjectName("outline_tree")
        self.outline_tree.installEventFilter(self)
        self.outline_tree.setStyleSheet("""
            QTreeWidget#outline_tree {
                background-color: #1f2937;
                color: #e5e7eb;
                border: none;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 13px;
                padding: 5px;
            }
            QTreeWidget#outline_tree::item {
                padding: 4px;
                border-radius: 4px;
            }
            QTreeWidget#outline_tree::item:hover {
                background-color: #374151;
            }
            QTreeWidget#outline_tree::item:selected {
                background-color: #3b82f6;
                color: white;
            }
        """)
        self.outline_tree.itemClicked.connect(self.on_outline_item_clicked)
        self.splitter.addWidget(self.outline_tree)
        
        # PDF Viewer (native scrolling QGraphicsView)
        self.viewer = PDFViewer(self.state, self)
        self.splitter.addWidget(self.viewer)
        
        # Connect splitter moved signal
        self.splitter.splitterMoved.connect(self.on_splitter_moved)
        
        layout.addWidget(self.splitter)
        
        # Status Bar
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)
        
        # Status label (for ephemeral messages)
        self.status_label = QLabel("Welcome to PDF Annotator. Press Ctrl+O to open a PDF.", self)
        self.status_bar.addWidget(self.status_label)
        
        # Permanent Page label (always visible on the right)
        self.page_label = QLabel("Page: -", self)
        self.status_bar.addPermanentWidget(self.page_label)
        
        # Setup Toolbars & Shortcuts
        self.create_toolbars()
        self.create_actions_and_shortcuts()
        
        # Connect signals
        self.viewer.page_changed.connect(self.on_page_changed)
        self.viewer.status_message.connect(self.show_status_message)
        self.viewer.zoom_changed.connect(self.update_zoom_label)
        self.viewer.document_modified.connect(self.on_document_modified)
        
        # Setup button states to match AppState defaults
        self.update_active_ui_indicators()
        
        # Initialize outline default state
        self.populate_outline()
        
        # Restore window geometry, state, and splitter sizes
        from PyQt6.QtCore import QSettings
        settings = QSettings("Slate", "SlateReader")
        
        geometry = settings.value("geometry")
        state = settings.value("windowState")
        splitter_state = settings.value("splitterState")
        
        if geometry:
            self.restoreGeometry(geometry)
        else:
            self.resize(1100, 850)
            
        if state:
            self.restoreState(state)
            
        if splitter_state:
            self.splitter.restoreState(splitter_state)
        else:
            self.splitter.setSizes([0, 1100])
            
        # Force toolbar visibility so it cannot get permanently hidden
        if hasattr(self, 'main_toolbar'):
            self.main_toolbar.setVisible(True)
            
        # Sync toggle button checked state with the restored splitter
        if hasattr(self, 'btn_outline'):
            sizes = self.splitter.sizes()
            self.btn_outline.setChecked(sizes[0] > 0)

    def create_actions_and_shortcuts(self):
        # Open
        open_action = QAction("Open...", self)
        open_action.setShortcut(QKeySequence("Ctrl+O"))
        open_action.triggered.connect(self.open_file)
        self.addAction(open_action)
        
        # Save
        save_action = QAction("Save", self)
        save_action.setShortcut(QKeySequence("Ctrl+S"))
        save_action.triggered.connect(self.save_file)
        self.addAction(save_action)
        
        # Zoom In / Out
        zoom_in_action = QAction("Zoom In", self)
        zoom_in_action.setShortcut(QKeySequence("Ctrl+="))
        zoom_in_action.triggered.connect(self.viewer.zoom_in)
        self.addAction(zoom_in_action)
        
        zoom_out_action = QAction("Zoom Out", self)
        zoom_out_action.setShortcut(QKeySequence("Ctrl+-"))
        zoom_out_action.triggered.connect(self.viewer.zoom_out)
        self.addAction(zoom_out_action)

        # Copy Selection Shortcut (Ctrl+C)
        copy_action = QAction("Copy Selection", self)
        copy_action.setShortcut(QKeySequence("Ctrl+C"))
        copy_action.triggered.connect(self.copy_selection)
        self.addAction(copy_action)
        
        # Toggle Outline Shortcut (O, 0, or F9)
        outline_action = QAction("Toggle Outline", self)
        outline_action.setShortcuts([
            QKeySequence(Qt.Key.Key_O),
            QKeySequence(Qt.Key.Key_0),
            QKeySequence(Qt.Key.Key_F9)
        ])
        outline_action.triggered.connect(self.toggle_outline)
        self.addAction(outline_action)

        # Search Shortcut (Ctrl+F)
        search_action = QAction("Find...", self)
        search_action.setShortcut(QKeySequence("Ctrl+F"))
        search_action.triggered.connect(self.viewer.show_search_bar)
        self.addAction(search_action)

        # Bind Alt+Shift+[1-5] for toggling color shades
        for idx in range(1, 6):
            shortcut = QShortcut(QKeySequence(f"Alt+Shift+{idx}"), self)
            shortcut.activated.connect(lambda i=idx: self.toggle_color_shade(i))

        # Line tool shortcut
        shortcut_line = QShortcut(QKeySequence("L"), self)
        shortcut_line.activated.connect(lambda: self.set_tool(Tool.LINE))

    def toggle_color_shade(self, color_idx):
        self.state.active_color_index = color_idx
        current_shade = self.state.active_shade_index
        self.state.active_shade_index = (current_shade + 1) % 3
        self.update_active_ui_indicators()

    def show_color_shades_menu(self, pos, color_idx, button_widget):
        menu = QMenu(self)
        menu.setWindowFlags(menu.windowFlags() | Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2b2b2b;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 4px;
            }
        """)
        
        # Create a widget to hold the horizontal layout
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        shades = COLORS[color_idx]["shades"]
        for shade_idx, shade in enumerate(shades):
            btn = QPushButton()
            btn.setFixedSize(24, 24)
            r, g, b = shade["rgb"]
            
            # Highlight the currently active shade for this color/tool
            border = "2px solid white" if (self.state.active_color_index == color_idx and self.state.active_shade_index == shade_idx) else "1px solid #444"
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: rgb({r},{g},{b});
                    border: {border};
                    border-radius: 12px;
                }}
                QPushButton:hover {{
                    border: 2px solid #aaa;
                }}
            """)
            
            # When a shade is clicked, set the color and shade, update UI, and close menu
            def on_shade_clicked(checked=False, c_idx=color_idx, s_idx=shade_idx):
                self.state.active_color_index = c_idx
                self.state.active_shade_index = s_idx
                self.update_active_ui_indicators()
                menu.close()
                
            btn.clicked.connect(on_shade_clicked)
            layout.addWidget(btn)
            
        action = QWidgetAction(menu)
        action.setDefaultWidget(widget)
        menu.addAction(action)
        
        # Show menu at the bottom-left of the color button
        global_pos = button_widget.mapToGlobal(QPoint(0, button_widget.height()))
        menu.exec(global_pos)

    def createPopupMenu(self):
        # Disable the default toolbar/dock context menu entirely
        return None

    def create_toolbars(self):
        toolbar = QToolBar("Tools", self)
        toolbar.setObjectName("Tools")
        toolbar.setMovable(False)
        toolbar.setOrientation(Qt.Orientation.Vertical)
        toolbar.setContextMenuPolicy(Qt.ContextMenuPolicy.PreventContextMenu)
        self.main_toolbar = toolbar
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, toolbar)
        
        # Open and Save Buttons (Visual)
        btn_open = QPushButton("📂", self)
        btn_open.setToolTip("Open PDF (Ctrl+O)")
        btn_open.clicked.connect(self.open_file)
        toolbar.addWidget(btn_open)
        
        btn_save = QPushButton("💾", self)
        btn_save.setToolTip("Save PDF (Ctrl+S)")
        btn_save.clicked.connect(self.save_file)
        toolbar.addWidget(btn_save)
        
        self.btn_outline = QPushButton("☰", self)
        self.btn_outline.setCheckable(True)
        self.btn_outline.setToolTip("Toggle Outline (O, 0, or F9)")
        self.btn_outline.clicked.connect(self.toggle_outline)
        toolbar.addWidget(self.btn_outline)
        
        toolbar.addSeparator()
        
        # Tools Group
        self.tool_group = QButtonGroup(self)
        self.tool_group.setExclusive(True)
        
        self.tool_buttons = {}
        tool_symbols = {
            Tool.SELECT: "⬈",
            Tool.HIGHLIGHT: "🟨",
            Tool.PEN: "🖋️",
            Tool.TEXT: "T",
            Tool.SQUARE: "□",
            Tool.ARROW: "➔",
            Tool.CALLOUT: "💬",
            Tool.ERASER: "🧹",
            Tool.LINE: "−"
        }
        tool_shortcuts = {
            Tool.SELECT: "V",
            Tool.HIGHLIGHT: "H",
            Tool.CALLOUT: "C",
            Tool.PEN: "P",
            Tool.TEXT: "T",
            Tool.SQUARE: "S",
            Tool.ARROW: "A",
            Tool.ERASER: "E",
            Tool.LINE: "L"
        }
        
        for tool in Tool:
            symbol = tool_symbols.get(tool, tool.value[0])
            btn = QPushButton(symbol, self)
            btn.setCheckable(True)
            shortcut = tool_shortcuts.get(tool, "")
            btn.setToolTip(f"{tool.value} Tool ({shortcut})")
            btn.clicked.connect(lambda checked, t=tool: self.set_tool(t))
            self.tool_group.addButton(btn)
            toolbar.addWidget(btn)
            self.tool_buttons[tool] = btn
            
        toolbar.addSeparator()
        
        # Rectangle Selection Mode Toggle Button
        self.btn_rect_mode = QPushButton("⛶", self)
        self.btn_rect_mode.setCheckable(True)
        self.btn_rect_mode.setToolTip("Rectangle Selection Mode (R)")
        self.btn_rect_mode.clicked.connect(self.toggle_rect_select_mode)
        self.btn_rect_mode.setStyleSheet("""
            QPushButton {
                background-color: #374151;
                color: #e5e7eb;
                border: 1px solid #4b5563;
                border-radius: 6px;
                min-width: 28px;
                max-width: 28px;
                min-height: 28px;
                max-height: 28px;
                padding: 0;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:checked {
                background-color: #059669; /* Emerald/Green when active */
                color: white;
            }
        """)
        toolbar.addWidget(self.btn_rect_mode)
        
        toolbar.addSeparator()

        # Colors Group
        self.color_group = QButtonGroup(self)
        self.color_group.setExclusive(True)
        
        self.color_buttons = {}
        for idx, col_info in COLORS.items():
            btn = QPushButton(self)
            btn.setObjectName("color_btn")
            btn.setCheckable(True)
            
            # Use base shade for initial button background
            r, g, b = col_info["shades"][1]["rgb"]
            hex_color = f"rgb({r},{g},{b})"
            btn.setStyleSheet(f"background-color: {hex_color};")
            btn.setToolTip(f"{col_info['name']} Color ({idx})\nRight-click for shades\nAlt+Shift+{idx} to cycle shades")
            
            # Enable custom context menu for right-click
            btn.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            btn.customContextMenuRequested.connect(
                lambda pos, index=idx, b=btn: self.show_color_shades_menu(pos, index, b)
            )
            
            btn.clicked.connect(lambda checked, index=idx: self.set_color(index))
            self.color_group.addButton(btn)
            toolbar.addWidget(btn)
            self.color_buttons[idx] = btn

        toolbar.addSeparator()
        
        # Font Size Selector
        self.font_size_spin = QSpinBox(self)
        self.font_size_spin.setRange(8, 72)
        self.font_size_spin.setValue(self.state.active_font_size)
        self.font_size_spin.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.font_size_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.font_size_spin.setFixedWidth(28)
        self.font_size_spin.setFixedHeight(28)
        self.font_size_spin.setToolTip("Font Size")
        self.font_size_spin.valueChanged.connect(self.set_font_size)
        toolbar.addWidget(self.font_size_spin)

        toolbar.addSeparator()
        
        # Line Width Selector
        self.line_width_spin = QSpinBox(self)
        self.line_width_spin.setRange(1, 20)
        self.line_width_spin.setValue(self.state.active_line_width)
        self.line_width_spin.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.line_width_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.line_width_spin.setFixedWidth(28)
        self.line_width_spin.setFixedHeight(28)
        self.line_width_spin.setToolTip("Line Width (Pen/Shapes)")
        self.line_width_spin.valueChanged.connect(self.set_line_width)
        toolbar.addWidget(self.line_width_spin)

        toolbar.addSeparator()
        
        # Zoom Controls
        btn_zoom_in = QPushButton("+", self)
        btn_zoom_in.clicked.connect(self.viewer.zoom_in)
        btn_zoom_in.setToolTip("Zoom In (Ctrl+=)")
        toolbar.addWidget(btn_zoom_in)
        
        btn_zoom_out = QPushButton("-", self)
        btn_zoom_out.clicked.connect(self.viewer.zoom_out)
        btn_zoom_out.setToolTip("Zoom Out (Ctrl+-)")
        toolbar.addWidget(btn_zoom_out)

        toolbar.addSeparator()
        
        # Page Controls
        self.page_spin = QSpinBox(self)
        self.page_spin.setRange(1, 1)
        self.page_spin.setValue(1)
        self.page_spin.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.page_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_spin.setFixedWidth(28)
        self.page_spin.setFixedHeight(28)
        self.page_spin.setToolTip("Go to Page")
        self.page_spin.valueChanged.connect(self.goto_page)
        toolbar.addWidget(self.page_spin)

    def set_tool(self, tool):
        if hasattr(self.viewer, 'cancel_callout'):
            self.viewer.cancel_callout()
        if hasattr(self.viewer, 'cancel_line'):
            self.viewer.cancel_line()
        self.state.active_tool = tool
        self.update_active_ui_indicators()
        self.show_status_message(f"Selected Tool: {tool.value}")
        
        # If switching tools, clear any active selection overlays
        if tool != Tool.SELECT:
            self.viewer.clear_selection_graphics()
        
        self.viewer.update_cursor()

    def set_color(self, color_idx):
        self.state.active_color_index = color_idx
        self.update_active_ui_indicators()
        self.show_status_message(f"Selected Color: {COLORS[color_idx]['name']}")

    def set_font_size(self, size):
        self.state.active_font_size = size
        self.show_status_message(f"Selected Font Size: {size}")

    def set_line_width(self, width):
        self.state.active_line_width = width
        self.show_status_message(f"Selected Line Width: {width}")

    def toggle_rect_select_mode(self, checked=None):
        if checked is None:
            self.state.rect_select_mode = not self.state.rect_select_mode
        else:
            self.state.rect_select_mode = checked
            
        self.update_active_ui_indicators()
        mode_str = "ON" if self.state.rect_select_mode else "OFF"
        self.show_status_message(f"Rectangle Selection Mode: {mode_str}")
        self.viewer.update_cursor()

    def update_active_ui_indicators(self):
        # Set checked state for tools
        if self.state.active_tool in self.tool_buttons:
            self.tool_buttons[self.state.active_tool].setChecked(True)
            
        # Set checked state for colors
        if self.state.active_color_index in self.color_buttons:
            self.color_buttons[self.state.active_color_index].setChecked(True)
            
        # Update ALL color buttons to reflect their current shade preferences for the active tool
        for idx, btn in self.color_buttons.items():
            # If the button is the active color, it should display the active shade.
            # Otherwise, just display the medium/base shade (index 1) or the last used shade?
            # Actually, the user asked to toggle the shade always on increasing.
            # Let's just always display the currently active shade for the *selected* color, 
            # and the base shade for the unselected colors to keep the palette recognizable.
            if idx == self.state.active_color_index:
                r, g, b = COLORS[idx]["shades"][self.state.active_shade_index]["rgb"]
                btn.setStyleSheet(f"background-color: rgb({r},{g},{b});")
            else:
                r, g, b = COLORS[idx]["shades"][1]["rgb"]
                btn.setStyleSheet(f"background-color: rgb({r},{g},{b});")
            
        # Set checked state for Rect Mode button
        if hasattr(self, 'btn_rect_mode'):
            self.btn_rect_mode.setChecked(self.state.rect_select_mode)

    def on_document_modified(self):
        self.is_dirty = True
        title = self.windowTitle()
        if not title.endswith(" *"):
            self.setWindowTitle(title + " *")

    def get_positions_filepath(self):
        config_dir = os.path.expanduser("~/.config/slate")
        os.makedirs(config_dir, exist_ok=True)
        return os.path.join(config_dir, "positions.json")

    def load_positions(self):
        import json
        path = self.get_positions_filepath()
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def save_current_position(self):
        if not self.pdf_doc:
            return
        import json
        positions = self.load_positions()
        abs_path = os.path.abspath(self.pdf_doc.filepath)
        positions[abs_path] = {
            "zoom": self.viewer.zoom,
            "y_scroll": self.viewer.verticalScrollBar().value(),
            "x_scroll": self.viewer.horizontalScrollBar().value()
        }
        try:
            with open(self.get_positions_filepath(), "w") as f:
                json.dump(positions, f)
        except Exception as e:
            print(f"Error saving position: {e}")

    def restore_position(self):
        if not self.pdf_doc:
            return
        positions = self.load_positions()
        abs_path = os.path.abspath(self.pdf_doc.filepath)
        if abs_path in positions:
            pos_info = positions[abs_path]
            zoom = pos_info.get("zoom", 1.5)
            y_scroll = pos_info.get("y_scroll", 0)
            x_scroll = pos_info.get("x_scroll", 0)
            
            # Apply zoom
            self.viewer.zoom = zoom
            self.viewer.rebuild_layout_with_zoom()
            
            # Restore scroll position after layout settles
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(100, lambda: self.apply_scroll_position(y_scroll, x_scroll))

    def apply_scroll_position(self, y, x):
        self.viewer.verticalScrollBar().setValue(y)
        self.viewer.horizontalScrollBar().setValue(x)
        self.viewer.update_visible_pages()

    def maybe_save_changes(self):
        if not self.is_dirty or not self.pdf_doc:
            return True
            
        from PyQt6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self,
            "Unsaved Changes",
            "You have unsaved changes. Do you want to save them before leaving?",
            QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save
        )
        
        if reply == QMessageBox.StandardButton.Save:
            self.save_file()
            return True
        elif reply == QMessageBox.StandardButton.Discard:
            return True
        else:
            return False

    def closeEvent(self, event):
        if self.maybe_save_changes():
            self.save_current_position()
            self.state.save_prefs()
            
            # Save geometry, state, and splitter sizes
            from PyQt6.QtCore import QSettings
            settings = QSettings("Slate", "SlateReader")
            settings.setValue("geometry", self.saveGeometry())
            settings.setValue("windowState", self.saveState())
            settings.setValue("splitterState", self.splitter.saveState())
            
            event.accept()
        else:
            event.ignore()

    def open_file(self):
        if not self.maybe_save_changes():
            return
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Open PDF Document", "", "PDF Files (*.pdf)"
        )
        if filepath:
            self.open_file_path(filepath)

    def open_file_path(self, filepath):
        if self.is_dirty:
            if not self.maybe_save_changes():
                return
        
        # Save position of previous file before opening new one
        self.save_current_position()
        
        try:
            self.pdf_doc = PDFDocument(filepath)
            self.is_dirty = False
            self.viewer.set_document(self.pdf_doc)
            self.setWindowTitle(f"Slate - {os.path.basename(filepath)}")
            self.show_status_message(f"Opened: {os.path.basename(filepath)}")
            self.restore_position()
            self.populate_outline()
            self.viewer.setFocus()
        except Exception as e:
            self.show_status_message(f"Error opening file: {str(e)}")

    def save_file(self):
        if not self.pdf_doc:
            self.show_status_message("No document loaded.")
            return
            
        try:
            self.pdf_doc.save()
            self.is_dirty = False
            title = self.windowTitle()
            if title.endswith(" *"):
                self.setWindowTitle(title[:-2])
            self.show_status_message("Document saved successfully!")
        except Exception as e:
            self.show_status_message(f"Error saving file: {str(e)}")

    def on_page_changed(self, current, total):
        self.page_spin.blockSignals(True)
        self.page_spin.setRange(1, total)
        self.page_spin.setValue(current)
        self.page_spin.blockSignals(False)
        self.page_label.setText(f"Page {current} of {total}")
        self.update_outline_selection(current)

    def goto_page(self, page_num):
        self.viewer.scroll_to_page(page_num - 1)

    def copy_selection(self):
        text = self.viewer.get_selected_text()
        if text:
            from PyQt6.QtWidgets import QApplication
            QApplication.clipboard().setText(text)
            self.show_status_message(f"Copied text to clipboard.")

    def update_zoom_label(self, zoom_factor):
        percentage = int(zoom_factor * 100)
        self.show_status_message(f"Zoom level: {percentage}%")

    def show_status_message(self, message):
        tool_desc = f"Tool: {self.state.active_tool.value} ({self.state.active_color_name})"
        full_msg = f"{tool_desc}  |  {message}"
        self.status_label.setText(full_msg)

    def populate_outline(self):
        self.outline_tree.clear()
        if not self.pdf_doc or not self.pdf_doc.doc:
            item = QTreeWidgetItem(self.outline_tree)
            item.setText(0, "No outline available")
            item.setForeground(0, QColor("#6b7280"))
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
            return
            
        toc = self.pdf_doc.doc.get_toc()
        if not toc:
            item = QTreeWidgetItem(self.outline_tree)
            item.setText(0, "No outline available")
            item.setForeground(0, QColor("#6b7280"))
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
            return
            
        parent_items = {0: self.outline_tree}
        for level, title, page_num in toc:
            parent_level = level - 1
            while parent_level not in parent_items and parent_level > 0:
                parent_level -= 1
                
            parent = parent_items.get(parent_level, self.outline_tree)
            item = QTreeWidgetItem(parent)
            item.setText(0, title)
            item.setData(0, Qt.ItemDataRole.UserRole, page_num)
            parent_items[level] = item
            
        self.outline_tree.expandToDepth(1)

    def eventFilter(self, obj, event):
        from PyQt6.QtCore import QEvent
        if obj is self.outline_tree and event.type() == QEvent.Type.KeyPress:
            key = event.key()
            if key in (Qt.Key.Key_Enter, Qt.Key.Key_Return):
                item = self.outline_tree.currentItem()
                if item:
                    self.on_outline_item_clicked(item, 0)
                return True
            # If user presses F9, O, 0, or Escape, toggle/close outline
            elif key in (Qt.Key.Key_F9, Qt.Key.Key_O, Qt.Key.Key_0, Qt.Key.Key_Escape):
                self.toggle_outline()
                return True
            # Let J/K/Shift+J/Shift+K scroll/page-nav the PDF viewer even if the outline has focus
            elif key == Qt.Key.Key_J:
                if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                    self.viewer.next_page()
                else:
                    bar = self.viewer.verticalScrollBar()
                    bar.setValue(bar.value() + bar.singleStep() * 3)
                return True
            elif key == Qt.Key.Key_K:
                if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                    self.viewer.prev_page()
                else:
                    bar = self.viewer.verticalScrollBar()
                    bar.setValue(bar.value() - bar.singleStep() * 3)
                return True
        return super().eventFilter(obj, event)

    def on_outline_item_clicked(self, item, column):
        page_num = item.data(0, Qt.ItemDataRole.UserRole)
        if page_num is not None and self.pdf_doc:
            target_idx = max(0, min(page_num - 1, self.pdf_doc.page_count - 1))
            self.viewer.scroll_to_page(target_idx)
            self.viewer.setFocus()

    def toggle_outline(self):
        sizes = self.splitter.sizes()
        if sizes[0] == 0:
            self.splitter.setSizes([250, 850])
            self.show_status_message("Show Outline")
            if hasattr(self, 'btn_outline'):
                self.btn_outline.setChecked(True)
            self.outline_tree.setFocus()
        else:
            self.splitter.setSizes([0, 1100])
            self.show_status_message("Hide Outline")
            if hasattr(self, 'btn_outline'):
                self.btn_outline.setChecked(False)
            self.viewer.setFocus()

    def on_splitter_moved(self, pos, index):
        if index == 1:
            sizes = self.splitter.sizes()
            is_visible = (sizes[0] > 0)
            if hasattr(self, 'btn_outline'):
                self.btn_outline.setChecked(is_visible)

    def update_outline_selection(self, current_page):
        if not self.pdf_doc or self.outline_tree.topLevelItemCount() == 0:
            return
            
        best_item = None
        best_page = -1
        
        def traverse(item):
            nonlocal best_item, best_page
            page = item.data(0, Qt.ItemDataRole.UserRole)
            if page is not None:
                if page <= current_page and page > best_page:
                    best_page = page
                    best_item = item
            
            for i in range(item.childCount()):
                traverse(item.child(i))
                
        for i in range(self.outline_tree.topLevelItemCount()):
            traverse(self.outline_tree.topLevelItem(i))
            
        if best_item:
            self.outline_tree.blockSignals(True)
            self.outline_tree.setCurrentItem(best_item)
            self.outline_tree.scrollToItem(best_item)
            self.outline_tree.blockSignals(False)
        else:
            self.outline_tree.blockSignals(True)
            self.outline_tree.clearSelection()
            self.outline_tree.blockSignals(False)

    def keyPressEvent(self, event):
        key = event.key()
        mods = event.modifiers()
        
        # Block shortcuts if editing text or search bar is focused
        if self.viewer.active_text_widget or (self.viewer.search_bar and self.viewer.search_bar.input_field.hasFocus()):
            super().keyPressEvent(event)
            return

        ctrl_down = bool(mods & Qt.KeyboardModifier.ControlModifier)
        shift_down = bool(mods & Qt.KeyboardModifier.ShiftModifier)

        # Temporary Eraser mode: Hold Ctrl + Shift simultaneously
        if ctrl_down and shift_down:
            if not event.isAutoRepeat():
                if self.pre_ctrl_tool is None:
                    self.pre_ctrl_tool = self.state.active_tool
                    self.set_tool(Tool.ERASER)
            if key in (Qt.Key.Key_Control, Qt.Key.Key_Shift):
                event.accept()
                return

        # Single-letter tool shortcuts (only active when Ctrl is NOT pressed)
        if not ctrl_down:
            if key == Qt.Key.Key_V:
                self.set_tool(Tool.SELECT)
                return
            elif key == Qt.Key.Key_H:
                self.set_tool(Tool.HIGHLIGHT)
                return
            elif key == Qt.Key.Key_P:
                self.set_tool(Tool.PEN)
                return
            elif key == Qt.Key.Key_T:
                self.set_tool(Tool.TEXT)
                return
            elif key == Qt.Key.Key_S:
                self.set_tool(Tool.SQUARE)
                return
            elif key == Qt.Key.Key_A:
                self.set_tool(Tool.ARROW)
                return
            elif key == Qt.Key.Key_E:
                self.set_tool(Tool.ERASER)
                return
            elif key == Qt.Key.Key_C:
                self.set_tool(Tool.CALLOUT)
                return
            elif key == Qt.Key.Key_R:
                self.toggle_rect_select_mode()
                return
            elif key in (Qt.Key.Key_O, Qt.Key.Key_0, Qt.Key.Key_F9):
                self.toggle_outline()
                return
            elif key == Qt.Key.Key_Slash:
                self.viewer.show_search_bar()
                return

        # Vim-style scrolling (J down, K up, Shift+J next page, Shift+K prev page)
        if key == Qt.Key.Key_J:
            if mods & Qt.KeyboardModifier.ShiftModifier:
                self.viewer.next_page()
            else:
                bar = self.viewer.verticalScrollBar()
                bar.setValue(bar.value() + bar.singleStep() * 3)
        elif key == Qt.Key.Key_K:
            if mods & Qt.KeyboardModifier.ShiftModifier:
                self.viewer.prev_page()
            else:
                bar = self.viewer.verticalScrollBar()
                bar.setValue(bar.value() - bar.singleStep() * 3)

        elif key == Qt.Key.Key_1:
            self.set_color(1)
        elif key == Qt.Key.Key_2:
            self.set_color(2)
        elif key == Qt.Key.Key_3:
            self.set_color(3)
        elif key == Qt.Key.Key_4:
            self.set_color(4)
        elif key == Qt.Key.Key_5:
            self.set_color(5)
            
        # Page Navigation
        elif key in (Qt.Key.Key_Right, Qt.Key.Key_PageDown):
            self.viewer.next_page()
        elif key in (Qt.Key.Key_Left, Qt.Key.Key_PageUp):
            self.viewer.prev_page()
            
        else:
            super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        # Block if editing text or search bar is focused
        if self.viewer.active_text_widget or (self.viewer.search_bar and self.viewer.search_bar.input_field.hasFocus()):
            super().keyReleaseEvent(event)
            return

        if event.key() in (Qt.Key.Key_Control, Qt.Key.Key_Shift):
            if not event.isAutoRepeat():
                if hasattr(self, 'pre_ctrl_tool') and self.pre_ctrl_tool is not None:
                    self.set_tool(self.pre_ctrl_tool)
                    self.pre_ctrl_tool = None
            event.accept()
            return
        super().keyReleaseEvent(event)
