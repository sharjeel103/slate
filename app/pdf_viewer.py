from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QTextEdit, QGraphicsRectItem, QGraphicsPathItem, QGraphicsLineItem, QFrame, QHBoxLayout, QWidget, QGraphicsTextItem
from PyQt6.QtGui import QPixmap, QImage, QPainter, QPen, QColor, QPainterPath, QBrush, QFont, QDesktopServices
from PyQt6.QtCore import Qt, pyqtSignal, QRect, QPoint, QRectF, QPointF, QLineF, QUrl, QThread, QTimer
import fitz
import time
from app.state import Tool

class PDFSearchWorker(QThread):
    progress = pyqtSignal(int, list)  # page_num, list of fitz.Rect matches
    finished = pyqtSignal(dict)       # final dictionary of {page_num: [fitz.Rect, ...]}

    def __init__(self, doc_path, query, parent=None):
        super().__init__(parent)
        self.doc_path = doc_path
        self.query = query
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        results = {}
        if not self.query or not self.doc_path:
            self.finished.emit(results)
            return

        try:
            doc = fitz.open(self.doc_path)
            for page_num in range(len(doc)):
                if self._is_cancelled:
                    break
                page = doc[page_num]
                rects = page.search_for(self.query)
                if rects:
                    results[page_num] = rects
                    self.progress.emit(page_num, rects)
            doc.close()
        except Exception as e:
            print(f"Error during search: {e}")
        
        if not self._is_cancelled:
            self.finished.emit(results)

class TextResizeHandle(QWidget):
    def __init__(self, parent_container, is_left):
        super().__init__(parent_container)
        self.parent_container = parent_container
        self.is_left = is_left
        self.setFixedWidth(8)
        self.setCursor(Qt.CursorShape.SizeHorCursor)
        self.setStyleSheet("background-color: #3b82f6; border-radius: 4px;")
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.drag_start_x = 0
        self.start_geometry = None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_x = event.globalPosition().x()
            self.start_geometry = self.parent_container.geometry()
            self.parent_container.auto_width = False
            self.parent_container.text_edit.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            dx = event.globalPosition().x() - self.drag_start_x
            geo = self.start_geometry
            
            if self.is_left:
                new_width = max(self.parent_container.min_width, geo.width() - dx)
                new_x = geo.x() + (geo.width() - new_width)
                self.parent_container.setGeometry(int(new_x), geo.y(), int(new_width), geo.height())
            else:
                new_width = max(self.parent_container.min_width, geo.width() + dx)
                self.parent_container.setGeometry(geo.x(), geo.y(), int(new_width), geo.height())
                
            self.parent_container.text_edit.adjust_height_from_layout(self.parent_container.text_edit.document().documentLayout().documentSize())
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.parent_container.text_edit.setFocus()
            event.accept()

class InnerTextInputWidget(QTextEdit):
    def __init__(self, parent_container):
        super().__init__(parent_container)
        self.parent_container = parent_container
        self.setFrameStyle(0)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.document().setDocumentMargin(0)
        
        self.document().documentLayout().documentSizeChanged.connect(self.adjust_height_from_layout)

    def adjust_height_from_layout(self, size):
        new_height = max(30, int(size.height()) + 10)
        self.setFixedHeight(new_height)
        self.parent_container.adjust_size()

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        if self.parent_container.left_handle.underMouse() or self.parent_container.right_handle.underMouse():
            return
        self.parent_container.commit()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.parent_container.commit()
        else:
            super().keyPressEvent(event)

class TextInputWidget(QFrame):
    editing_done = pyqtSignal(object, object)  # text, widget (self)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Shape.NoFrame)
        self.setStyleSheet("TextInputWidget { background: transparent; border: none; }")
        
        # State variables
        self._committed = False
        self.scene_pos = None
        self.page_num = -1
        self.editing_annot_rect = None
        self.editing_annot_page = -1
        self.color_pdf = (0.0, 0.0, 0.0)
        self.font_size = 12
        self.min_width = 50
        self.auto_width = True
        self.max_allowed_width = 1000
        
        # Layout
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # Left Handle
        self.left_handle = TextResizeHandle(self, is_left=True)
        self.layout.addWidget(self.left_handle)

        # Text Edit
        self.text_edit = InnerTextInputWidget(self)
        self.layout.addWidget(self.text_edit)
        
        # Right Handle
        self.right_handle = TextResizeHandle(self, is_left=False)
        self.layout.addWidget(self.right_handle)
        
    def adjust_size(self):
        if self.auto_width:
            # Measure natural unwrapped width using a dummy document
            doc = self.text_edit.document().clone()
            doc.setTextWidth(-1)
            natural_width = doc.idealWidth()
            
            if natural_width + 16 > self.max_allowed_width:
                if self.text_edit.lineWrapMode() != QTextEdit.LineWrapMode.WidgetWidth:
                    self.text_edit.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
                self.setFixedWidth(self.max_allowed_width)
            else:
                if self.text_edit.lineWrapMode() != QTextEdit.LineWrapMode.NoWrap:
                    self.text_edit.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
                self.setFixedWidth(max(self.min_width, int(natural_width) + 16))
        
        # Let height automatically expand based on the text document height
        doc_height = self.text_edit.document().size().height()
        self.setFixedHeight(int(doc_height) + 10)

    def commit(self):
        if not self._committed:
            self._committed = True
            self.editing_done.emit(self.text_edit.toPlainText(), self)
            
    def setFont(self, font):
        self.text_edit.setFont(font)
        
    def setPlainText(self, text):
        self.text_edit.setPlainText(text)
        
    def setFocus(self):
        self.text_edit.setFocus()
        
    def clearFocus(self):
        self.text_edit.clearFocus()

class PDFPageItem(QGraphicsRectItem):
    """A visual representation of a single PDF page inside the QGraphicsScene."""
    def __init__(self, page_num, pdf_doc, parent_viewer, y_offset, zoom):
        width, height = pdf_doc.get_page_size(page_num)
        scaled_w = width * zoom
        scaled_h = height * zoom
        
        # Define the page rectangle bounds
        super().__init__(0, 0, scaled_w, scaled_h)
        
        self.page_num = page_num
        self.pdf_doc = pdf_doc
        self.viewer = parent_viewer
        self.zoom = zoom
        self.pixmap_item = None
        
        # Position page vertically with a 15px gap between pages
        self.setPos(0, y_offset)
        
        # Styled border and dark placeholder background to match premium theme
        self.setPen(QPen(QColor("#374151"), 1))
        self.setBrush(QColor("#1f2937")) # Gray placeholder background

    def load_page(self):
        """Loads and renders the page image dynamically if it is not already loaded."""
        if self.pixmap_item is not None:
            return
            
        qimg = self.pdf_doc.render_page(self.page_num, zoom=self.zoom)
        pixmap = QPixmap.fromImage(qimg)
        
        self.pixmap_item = QGraphicsPixmapItem(pixmap, self)
        self.pixmap_item.setPos(0, 0)
        
        # Remove placeholder background brush
        self.setBrush(QBrush(Qt.BrushStyle.NoBrush))

    def unload_page(self):
        """Unloads the page image to free memory when scrolled out of viewport."""
        if self.pixmap_item is not None:
            self.pixmap_item.setParentItem(None)
            self.viewer.scene().removeItem(self.pixmap_item)
            self.pixmap_item = None
            
            # Restore dark gray background placeholder
            self.setBrush(QColor("#1f2937"))

    def reload_page(self):
        """Forces page re-rendering (used after adding/deleting annotations)."""
        self.unload_page()
        self.load_page()

    def get_link_at(self, local_pos):
        """Returns the PyMuPDF link dictionary if local_pos (scene page-local) is over a link."""
        if not self.pdf_doc or not self.pdf_doc.doc:
            return None
        # Convert local pos to PDF points
        zoom = self.zoom
        pdf_x = local_pos.x() / zoom
        pdf_y = local_pos.y() / zoom
        pdf_point = fitz.Point(pdf_x, pdf_y)
        
        # Get links on this page
        try:
            links = self.pdf_doc.doc[self.page_num].get_links()
            for link in links:
                if link.get("from") and link["from"].contains(pdf_point):
                    return link
        except Exception:
            pass
        return None

class PDFViewer(QGraphicsView):
    page_changed = pyqtSignal(int, int)  # current, total
    zoom_changed = pyqtSignal(float)     # zoom percentage factor
    status_message = pyqtSignal(str)
    document_modified = pyqtSignal()

    def __init__(self, state, parent=None):
        super().__init__(parent)
        self.state = state
        self.pdf_doc = None
        
        self.zoom = 1.5  # Current viewer zoom factor
        self.page_items = []
        
        # QGraphicsScene setup
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        
        # Viewer UI configuration
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setStyleSheet("background-color: #111827; border: none;") # Gray 900 background
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # Tool state variables
        self.drawing = False
        self.active_page_num = -1  # Page where drawing started
        self.temp_path_item = None
        self.active_path = None    # QPainterPath for standard drawing sequence
        self.current_stroke_points = []
        
        # Annotation drag variables
        self.drag_initiated = False
        self.drag_has_moved = False
        self.dragged_annot_page = -1
        self.dragged_annot_rect = None  # fitz.Rect
        self.dragged_annot_text = ""
        self.dragged_annot_color = None
        self.dragged_annot_fontsize = 12
        self.drag_start_scene_pos = None
        self.drag_visual_item = None
        
        # Highlighting & Text selection index state
        self.selection_start_word_idx = -1
        self.selection_end_word_idx = -1
        self.selected_word_items = []
        self.selected_text_content = ""
        
        # Click sequence tracking for double/triple click detection
        self.last_click_time = 0.0
        self.click_sequence_count = 0
        
        # In-place Text widget
        self.active_text_widget = None

        # Search state variables
        self.search_bar = None
        self.search_worker = None
        self.search_highlights = {}  # page_num: [QGraphicsRectItem, ...]
        self.flat_highlight_items = []
        self.search_matches = []  # list of tuples: (page_num, fitz.Rect)
        self.current_match_idx = -1
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.trigger_search)
        self.pending_search_query = ""
        self.running_workers = set()

        # Enable mouse tracking for hover cursor updates
        self.setMouseTracking(True)
        self.viewport().setMouseTracking(True)

    def set_document(self, pdf_doc):
        if hasattr(self, 'search_bar') and self.search_bar:
            self.search_bar.hide()
            self.clear_search()

        self.pdf_doc = pdf_doc
        self.page_items.clear()
        self._scene.clear()
        
        if not self.pdf_doc:
            return
            
        # Build pages vertically
        y_offset = 0
        page_gap = 15  # Pixels spacing between pages
        
        for p in range(self.pdf_doc.page_count):
            item = PDFPageItem(p, self.pdf_doc, self, y_offset, self.zoom)
            self._scene.addItem(item)
            self.page_items.append(item)
            y_offset += item.rect().height() + page_gap
            
        # Set scene bounding rect to wrap all stacked pages
        max_width = max([item.rect().width() for item in self.page_items]) if self.page_items else 800
        self._scene.setSceneRect(0, 0, max_width, y_offset)
        
        # Render visible pages initially
        self.update_visible_pages()

    def scrollContentsBy(self, dx, dy):
        super().scrollContentsBy(dx, dy)
        self.update_visible_pages()

    def update_visible_pages(self):
        """Dynamic virtual page loading loop. Loads visible pages and unloads far away ones."""
        if not self.pdf_doc or not self.page_items:
            return
            
        # Get current visible viewport region in scene coordinates
        viewport_rect = self.mapToScene(self.viewport().rect()).boundingRect()
        
        # Add a viewport-height buffer above and below to prevent loading flickers
        buffer_height = viewport_rect.height()
        load_rect = QRectF(
            viewport_rect.left(),
            viewport_rect.top() - buffer_height,
            viewport_rect.width(),
            viewport_rect.height() + 2 * buffer_height
        )
        
        current_page_idx = 0
        max_overlap_height = 0
        
        for idx, item in enumerate(self.page_items):
            item_rect = item.sceneBoundingRect()
            
            # Check intersection
            if load_rect.intersects(item_rect):
                item.load_page()
            else:
                item.unload_page()
                
            # Detect which page occupies the most height in the active viewport
            overlap = viewport_rect.intersected(item_rect).height()
            if overlap > max_overlap_height:
                max_overlap_height = overlap
                current_page_idx = idx
                
        # Emit active page progress
        self.page_changed.emit(current_page_idx + 1, self.pdf_doc.page_count)

    def get_current_visible_page(self):
        """Returns the page index currently occupying the most space in the viewport."""
        if not self.page_items:
            return 0
        viewport_rect = self.mapToScene(self.viewport().rect()).boundingRect()
        max_overlap = 0
        current = 0
        for idx, item in enumerate(self.page_items):
            overlap = viewport_rect.intersected(item.sceneBoundingRect()).height()
            if overlap > max_overlap:
                max_overlap = overlap
                current = idx
        return current

    def scroll_to_page(self, page_num):
        """Scrolls the viewport to align with the top of a specific page number."""
        if 0 <= page_num < len(self.page_items):
            item = self.page_items[page_num]
            # Calculate viewport height in scene coordinates
            scene_viewport_rect = self.mapToScene(self.viewport().rect()).boundingRect()
            scene_viewport_height = scene_viewport_rect.height()
            
            # Center on the point that aligns the page top with the viewport top
            center_x = item.pos().x() + item.rect().width() / 2
            center_y = item.pos().y() + scene_viewport_height / 2
            
            self.centerOn(center_x, center_y)
            self.update_visible_pages()

    def next_page(self):
        curr = self.get_current_visible_page()
        if curr < len(self.page_items) - 1:
            self.scroll_to_page(curr + 1)

    def prev_page(self):
        curr = self.get_current_visible_page()
        if curr > 0:
            self.scroll_to_page(curr - 1)

    def zoom_in(self):
        if self.zoom < 5.0:
            self.zoom += 0.2
            self.rebuild_layout_with_zoom()

    def zoom_out(self):
        if self.zoom > 0.4:
            self.zoom -= 0.2
            self.rebuild_layout_with_zoom()

    def rebuild_layout_with_zoom(self):
        """Re-scales and re-positions all page items vertically when zoom factors change."""
        if not self.pdf_doc:
            return
            
        # Store current active page before zoom to scroll back to it
        active_page = self.get_current_visible_page()
        
        y_offset = 0
        page_gap = 15
        
        # Update each page item's size and pos, then force unload so they reload at high res
        for item in self.page_items:
            width, height = self.pdf_doc.get_page_size(item.page_num)
            scaled_w = width * self.zoom
            scaled_h = height * self.zoom
            
            # Set the new bounds and pos
            item.setRect(0, 0, scaled_w, scaled_h)
            item.zoom = self.zoom
            item.setPos(0, y_offset)
            
            # Unload the old pixmap representation
            item.unload_page()
            
            y_offset += scaled_h + page_gap
            
        # Adjust scene bounds
        max_width = max([item.rect().width() for item in self.page_items]) if self.page_items else 800
        self._scene.setSceneRect(0, 0, max_width, y_offset)
        
        # Restore scroll position
        self.scroll_to_page(active_page)
        self.update_visible_pages()
        self.zoom_changed.emit(self.zoom)
        self.update_search_highlights_zoom()

    def get_page_under_pos(self, scene_pos):
        """Finds the PDFPageItem containing the scene position, returning (item, page_local_pos)."""
        for item in self.page_items:
            if item.sceneBoundingRect().contains(scene_pos):
                local_pos = scene_pos - item.pos()
                return item, local_pos
        return None, None

    def get_pdf_point(self, local_pos):
        """Converts page-local scene coordinates to PDF Points."""
        return fitz.Point(local_pos.x() / self.zoom, local_pos.y() / self.zoom)

    def mousePressEvent(self, event):
        if not self.pdf_doc or not self.page_items:
            super().mousePressEvent(event)
            return

        scene_pos = self.mapToScene(event.pos())
        page_item, local_pos = self.get_page_under_pos(scene_pos)
        
        # Don't draw if click is outside any page bounds
        if not page_item:
            super().mousePressEvent(event)
            return

        self.active_page_num = page_item.page_num
        tool = self.state.active_tool
        # For SELECT tool, check if we clicked on a hyperlink/document link
        if tool == Tool.SELECT:
            link = page_item.get_link_at(local_pos)
            if link:
                if "page" in link and link["page"] is not None and link["page"] >= 0:
                    self.scroll_to_page(link["page"])
                elif link.get("kind") == fitz.LINK_URI:
                    QDesktopServices.openUrl(QUrl(link["uri"]))
                event.accept()
                return

        # For SELECT and TEXT tools, check first if we clicked on an existing FreeText annotation for editing/dragging
        if tool in (Tool.SELECT, Tool.TEXT):
            pdf_point = self.get_pdf_point(local_pos)
            page = self.pdf_doc.doc[page_item.page_num]
            clicked_annot = None
            for annot in page.annots():
                if annot.type[1] == "FreeText" and annot.rect.contains(pdf_point):
                    clicked_annot = annot
                    break
            
            if clicked_annot:
                self.drag_initiated = True
                self.drag_has_moved = False
                self.dragged_annot_page = page_item.page_num
                self.dragged_annot_rect = clicked_annot.rect
                self.dragged_annot_text = clicked_annot.info.get("content", "")
                self.dragged_annot_color = self.pdf_doc.get_freetext_color(clicked_annot)
                self.dragged_annot_fontsize = self.pdf_doc.get_freetext_fontsize(clicked_annot)
                
                self.drag_start_scene_pos = scene_pos
                event.accept()
                return
        
        if tool == Tool.PEN:
            self.drawing = True
            pdf_point = self.get_pdf_point(local_pos)
            self.current_stroke_points = [pdf_point]
            
            # Start temporary drawing path in scene coordinates
            self.active_path = QPainterPath()
            self.active_path.moveTo(scene_pos)
            
            pen = QPen(QColor(*self.state.active_color_rgb), self.state.active_line_width * self.zoom, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
            self.temp_path_item = self._scene.addPath(self.active_path, pen)
            
        elif tool in (Tool.HIGHLIGHT, Tool.SELECT):
            self.drawing = True
            self.clear_selection_graphics()
            
            # Manual double/triple click detection using time differences
            now = time.time()
            if now - self.last_click_time < 0.35:
                self.click_sequence_count += 1
            else:
                self.click_sequence_count = 1
            self.last_click_time = now
            
            target_idx = self.find_closest_word_index(page_item.page_num, local_pos)
            
            if self.click_sequence_count == 2 and target_idx != -1:
                # Double click: select the clicked word
                self.drawing = False  # Disable drag expansion
                self.selection_start_word_idx = target_idx
                self.selection_end_word_idx = target_idx
                self.update_selection_overlays()
                
                if tool == Tool.SELECT:
                    self.copy_selection_to_clipboard()
                elif tool == Tool.HIGHLIGHT:
                    self.apply_highlight_to_selection()
                    
            elif self.click_sequence_count >= 3 and target_idx != -1:
                # Triple click: select the whole paragraph (block)
                self.drawing = False  # Disable drag expansion
                words = self.pdf_doc.get_words(page_item.page_num)
                block_no = words[target_idx][5]
                
                # Find all word indices belonging to the same block
                block_indices = [i for i, w in enumerate(words) if w[5] == block_no]
                if block_indices:
                    self.selection_start_word_idx = min(block_indices)
                    self.selection_end_word_idx = max(block_indices)
                    self.update_selection_overlays()
                    
                    if tool == Tool.SELECT:
                        self.copy_selection_to_clipboard()
                    elif tool == Tool.HIGHLIGHT:
                        self.apply_highlight_to_selection()
            else:
                # Single click: normal selection start
                self.selection_start_word_idx = target_idx
                self.selection_end_word_idx = self.selection_start_word_idx
                self.selection_start_local_pos = local_pos
                if target_idx != -1:
                    self.selected_word_indices = [target_idx]
                else:
                    self.selected_word_indices = []
                self.update_selection_overlays()
            
        elif tool == Tool.TEXT:
            if self.active_text_widget:
                self.active_text_widget.clearFocus()
                
            viewport_pos = event.pos()
            
            # Calculate coordinates and page boundaries in PDF points
            pdf_point = self.get_pdf_point(local_pos)
            page_width, page_height = self.pdf_doc.get_page_size(page_item.page_num)
            margin = 10.0
            
            # Start exactly at the click point
            start_x = pdf_point.x
            max_width_pdf = max(50.0, page_width - start_x - margin)
            max_width_px = int(max_width_pdf * self.zoom)
            
            # Convert adjusted coordinates back to scene and viewport coordinates
            adjusted_local_x = start_x * self.zoom
            adjusted_local_y = local_pos.y() - 8.0
            adjusted_scene_pos = QPointF(
                page_item.pos().x() + adjusted_local_x,
                page_item.pos().y() + adjusted_local_y
            )
            adjusted_viewport_pos = self.mapFromScene(adjusted_scene_pos)
            
            self.active_text_widget = TextInputWidget(self.viewport())
            self.active_text_widget.max_allowed_width = max_width_px
            self.active_text_widget.scene_pos = adjusted_scene_pos
            self.active_text_widget.page_num = page_item.page_num
            self.active_text_widget.color_pdf = self.state.active_color_pdf
            self.active_text_widget.font_size = self.state.active_font_size
            
            self.active_text_widget.editing_done.connect(self.finish_text_input)
            
            # Scale screen font size to match current zoom level
            screen_font_size = self.state.active_font_size * self.zoom
            font = QFont("helvetica")
            font.setPixelSize(int(screen_font_size))
            self.active_text_widget.setFont(font)
            
            r, g, b = self.state.active_color_rgb
            self.active_text_widget.text_edit.setStyleSheet(
                f"background: rgba(255, 255, 255, 0.4);"
                f"color: rgb({r},{g},{b});"
                f"border: 1px dashed #3b82f6;"
                f"padding: 0px;"
                f"margin: 0px;"
                f"outline: none;"
            )
            
            # Use initial height based on font size and set geometry
            initial_height = int(screen_font_size * 1.5)
            self.active_text_widget.setGeometry(
                int(adjusted_viewport_pos.x()) - 8, 
                int(adjusted_viewport_pos.y()), 
                100, 
                initial_height
            )
            self.active_text_widget.text_edit.adjust_height_from_layout(self.active_text_widget.text_edit.document().documentLayout().documentSize())
            self.active_text_widget.show()
            self.active_text_widget.setFocus()
            
        elif tool == Tool.ERASER:
            self.drawing = True
            self.erase_at(page_item.page_num, local_pos)
            
        elif tool in (Tool.SQUARE, Tool.ARROW):
            self.drawing = True
            self.drag_start_local_pos = local_pos
            self.drag_start_scene_pos = scene_pos

    def mouseMoveEvent(self, event):
        if not self.pdf_doc or not self.page_items:
            super().mouseMoveEvent(event)
            return

        scene_pos = self.mapToScene(event.pos())
        
        # Handle annotation drag moving
        if hasattr(self, 'drag_initiated') and self.drag_initiated:
            delta = scene_pos - self.drag_start_scene_pos
            distance = (delta.x()**2 + delta.y()**2)**0.5
            
            if not self.drag_has_moved and distance > 5:
                self.drag_has_moved = True
                page_item = self.page_items[self.dragged_annot_page]
                x0 = page_item.pos().x() + self.dragged_annot_rect.x0 * self.zoom
                y0 = page_item.pos().y() + self.dragged_annot_rect.y0 * self.zoom
                w = self.dragged_annot_rect.width * self.zoom
                h = self.dragged_annot_rect.height * self.zoom
                
                self.drag_visual_item = QGraphicsRectItem(0, 0, w, h)
                self.drag_visual_item.setPos(x0, y0)
                pen = QPen(QColor(59, 130, 246), 2, Qt.PenStyle.DashLine)
                self.drag_visual_item.setPen(pen)
                
                # If dragging a text annotation, display the actual text instead of just a box
                if hasattr(self, 'dragged_annot_text') and self.dragged_annot_text:
                    self.drag_visual_item.setBrush(QBrush(Qt.BrushStyle.NoBrush))
                    self.drag_visual_item.setPen(QPen(Qt.PenStyle.NoPen))
                    
                    text_item = QGraphicsTextItem(self.dragged_annot_text, self.drag_visual_item)
                    font = QFont("helvetica")
                    font.setPixelSize(int(self.dragged_annot_fontsize * self.zoom))
                    text_item.setFont(font)
                    text_item.setTextWidth(w)
                    text_item.setDefaultTextColor(QColor(*[int(c*255) for c in self.dragged_annot_color]))
                    text_item.setPos(0, -4.0)
                else:
                    self.drag_visual_item.setBrush(QColor(59, 130, 246, 40))

                self.drag_visual_item.setZValue(1000.0)
                self._scene.addItem(self.drag_visual_item)
                
            if self.drag_has_moved and self.drag_visual_item:
                page_item = self.page_items[self.dragged_annot_page]
                x0 = page_item.pos().x() + self.dragged_annot_rect.x0 * self.zoom + delta.x()
                y0 = page_item.pos().y() + self.dragged_annot_rect.y0 * self.zoom + delta.y()
                self.drag_visual_item.setPos(x0, y0)
                
            event.accept()
            return

        if not self.drawing or self.active_page_num == -1:
            self.update_cursor_for_position(scene_pos)
            super().mouseMoveEvent(event)
            return

        # Keep operations local to the active page item
        active_item = self.page_items[self.active_page_num]
        local_pos = scene_pos - active_item.pos()
        
        tool = self.state.active_tool
        
        if tool == Tool.PEN and self.temp_path_item and self.active_path:
            pdf_point = self.get_pdf_point(local_pos)
            self.current_stroke_points.append(pdf_point)
            self.active_path.lineTo(scene_pos)
            self.temp_path_item.setPath(self.active_path)
            
        elif tool in (Tool.HIGHLIGHT, Tool.SELECT):
            # Update temporary drag selection box graphic
            if self.state.rect_select_mode and hasattr(self, 'selection_start_local_pos'):
                active_item = self.page_items[self.active_page_num]
                x0 = min(self.selection_start_local_pos.x(), local_pos.x())
                y0 = min(self.selection_start_local_pos.y(), local_pos.y())
                w_px = abs(self.selection_start_local_pos.x() - local_pos.x())
                h_px = abs(self.selection_start_local_pos.y() - local_pos.y())
                
                scene_rect = QRectF(
                    active_item.pos().x() + x0,
                    active_item.pos().y() + y0,
                    w_px,
                    h_px
                )
                
                if not hasattr(self, 'temp_rect_item') or self.temp_rect_item is None:
                    self.temp_rect_item = QGraphicsRectItem(scene_rect)
                    pen = QPen(QColor(59, 130, 246), 1.5, Qt.PenStyle.DashLine)
                    self.temp_rect_item.setPen(pen)
                    self.temp_rect_item.setBrush(QBrush(QColor(59, 130, 246, 30)))
                    self.temp_rect_item.setZValue(1000.0)
                    self._scene.addItem(self.temp_rect_item)
                else:
                    self.temp_rect_item.setRect(scene_rect)
                    
            if self.state.rect_select_mode and hasattr(self, 'selection_start_local_pos'):
                # Rectangle selection mode: select words intersecting the drag bounding box
                x0_pdf = min(self.selection_start_local_pos.x(), local_pos.x()) / self.zoom
                y0_pdf = min(self.selection_start_local_pos.y(), local_pos.y()) / self.zoom
                x1_pdf = max(self.selection_start_local_pos.x(), local_pos.x()) / self.zoom
                y1_pdf = max(self.selection_start_local_pos.y(), local_pos.y()) / self.zoom
                drag_rect = fitz.Rect(x0_pdf, y0_pdf, x1_pdf, y1_pdf)
                
                words = self.pdf_doc.get_words(self.active_page_num)
                self.selected_word_indices = []
                for idx, w in enumerate(words):
                    word_rect = fitz.Rect(w[0], w[1], w[2], w[3])
                    if word_rect.intersects(drag_rect):
                        self.selected_word_indices.append(idx)
                self.update_selection_overlays()
            else:
                # Reading-order selection
                idx = self.find_closest_word_index(self.active_page_num, local_pos)
                if idx != -1 and idx != self.selection_end_word_idx:
                    self.selection_end_word_idx = idx
                    start = min(self.selection_start_word_idx, self.selection_end_word_idx)
                    end = max(self.selection_start_word_idx, self.selection_end_word_idx)
                    self.selected_word_indices = list(range(start, end + 1))
                    self.update_selection_overlays()
                    
        elif tool == Tool.ERASER:
            self.erase_at(self.active_page_num, local_pos)
            
        elif tool == Tool.SQUARE:
            # Draw a temporary rectangle outline in scene coordinates
            x0 = min(self.drag_start_scene_pos.x(), scene_pos.x())
            y0 = min(self.drag_start_scene_pos.y(), scene_pos.y())
            w = abs(self.drag_start_scene_pos.x() - scene_pos.x())
            h = abs(self.drag_start_scene_pos.y() - scene_pos.y())
            scene_rect = QRectF(x0, y0, w, h)
            
            if (not hasattr(self, 'temp_shape_item') or 
                self.temp_shape_item is None or 
                not isinstance(self.temp_shape_item, QGraphicsRectItem)):
                if hasattr(self, 'temp_shape_item') and self.temp_shape_item is not None:
                    try:
                        self._scene.removeItem(self.temp_shape_item)
                    except Exception:
                        pass
                self.temp_shape_item = QGraphicsRectItem(scene_rect)
                pen = QPen(QColor(*self.state.active_color_rgb), self.state.active_line_width * self.zoom, Qt.PenStyle.SolidLine)
                pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
                self.temp_shape_item.setPen(pen)
                self.temp_shape_item.setZValue(1000.0)
                self._scene.addItem(self.temp_shape_item)
            else:
                self.temp_shape_item.setRect(scene_rect)
                
        elif tool == Tool.ARROW:
            # Draw a temporary arrow in scene coordinates using QPainterPath
            p1 = self.drag_start_scene_pos
            p2 = scene_pos
            
            dx = p2.x() - p1.x()
            dy = p2.y() - p1.y()
            length = (dx**2 + dy**2)**0.5
            
            path = QPainterPath()
            if length > 0:
                ux = dx / length
                uy = dy / length
                
                # Proportional arrowhead size math scaled by zoom
                width = self.state.active_line_width * self.zoom
                base_size = 6.0 * self.zoom + 1.5 * width
                base_size = min(base_size, 18.0 * self.zoom)
                arrow_size = min(base_size, length * 0.3)
                if length > 10 * self.zoom:
                    arrow_size = max(arrow_size, 5.0 * self.zoom)
                
                # Rotate vectors by 150 degrees (30 degrees from back shaft)
                cos_val = -0.866
                sin_val = 0.5
                
                rx1 = ux * cos_val - uy * sin_val
                ry1 = ux * sin_val + uy * cos_val
                
                rx2 = ux * cos_val - uy * (-sin_val)
                ry2 = ux * (-sin_val) + uy * cos_val
                
                w1_x = p2.x() + arrow_size * rx1
                w1_y = p2.y() + arrow_size * ry1
                
                w2_x = p2.x() + arrow_size * rx2
                w2_y = p2.y() + arrow_size * ry2
                
                # Construct path: shaft + wing1 + wing2
                path.moveTo(p1)
                path.lineTo(p2)
                path.moveTo(p2)
                path.lineTo(QPointF(w1_x, w1_y))
                path.moveTo(p2)
                path.lineTo(QPointF(w2_x, w2_y))
            else:
                path.moveTo(p1)
                path.lineTo(p2)
                
            if (not hasattr(self, 'temp_shape_item') or 
                self.temp_shape_item is None or 
                not isinstance(self.temp_shape_item, QGraphicsPathItem)):
                if hasattr(self, 'temp_shape_item') and self.temp_shape_item is not None:
                    try:
                        self._scene.removeItem(self.temp_shape_item)
                    except Exception:
                        pass
                self.temp_shape_item = QGraphicsPathItem(path)
                pen = QPen(QColor(*self.state.active_color_rgb), self.state.active_line_width * self.zoom, Qt.PenStyle.SolidLine)
                pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
                self.temp_shape_item.setPen(pen)
                self.temp_shape_item.setZValue(1000.0)
                self._scene.addItem(self.temp_shape_item)
            else:
                self.temp_shape_item.setPath(path)

    def cleanup_temp_rect(self):
        if hasattr(self, 'temp_rect_item') and self.temp_rect_item is not None:
            try:
                self._scene.removeItem(self.temp_rect_item)
            except Exception:
                pass
            self.temp_rect_item = None
            
        if hasattr(self, 'temp_shape_item') and self.temp_shape_item is not None:
            try:
                self._scene.removeItem(self.temp_shape_item)
            except Exception:
                pass
            self.temp_shape_item = None

    def mouseReleaseEvent(self, event):
        if not self.pdf_doc or not self.page_items:
            super().mouseReleaseEvent(event)
            self.cleanup_temp_rect()
            return

        scene_pos = self.mapToScene(event.pos())
        
        # Handle annotation drag release
        if hasattr(self, 'drag_initiated') and self.drag_initiated:
            self.drag_initiated = False
            
            if self.drag_visual_item:
                self._scene.removeItem(self.drag_visual_item)
                self.drag_visual_item = None
                
            self.cleanup_temp_rect()
            
            if self.drag_has_moved:
                delta = scene_pos - self.drag_start_scene_pos
                dx_pdf = delta.x() / self.zoom
                dy_pdf = delta.y() / self.zoom
                
                # Clamp coordinates to stay completely inside page boundaries (allowing a 10-point margin)
                page_width, page_height = self.pdf_doc.get_page_size(self.dragged_annot_page)
                w_pdf = self.dragged_annot_rect.width
                h_pdf = self.dragged_annot_rect.height
                
                new_x0 = max(10.0, min(self.dragged_annot_rect.x0 + dx_pdf, page_width - w_pdf - 10.0))
                new_y0 = max(10.0, min(self.dragged_annot_rect.y0 + dy_pdf, page_height - h_pdf - 10.0))
                
                new_rect = fitz.Rect(
                    new_x0,
                    new_y0,
                    new_x0 + w_pdf,
                    new_y0 + h_pdf
                )
                
                # Delete the old annotation from the page
                self.pdf_doc.delete_annotation_by_rect(self.dragged_annot_page, self.dragged_annot_rect)
                
                # Add the new annotation at the new position
                self.pdf_doc.add_text_annotation(
                    self.dragged_annot_page,
                    new_rect,
                    self.dragged_annot_text,
                    self.dragged_annot_color,
                    fontsize=self.dragged_annot_fontsize
                )
                
                self.page_items[self.dragged_annot_page].reload_page()
                self.document_modified.emit()
                self.status_message.emit("Repositioned text annotation.")
            else:
                # It was a simple click (no movement) on an existing annotation!
                if self.state.active_tool == Tool.TEXT:
                    if self.active_text_widget:
                        self.active_text_widget.clearFocus()
                        
                    # Delete the annotation immediately so it doesn't show under the transparent edit widget
                    page_item = self.page_items[self.dragged_annot_page]
                    self.pdf_doc.delete_annotation_by_rect(self.dragged_annot_page, self.dragged_annot_rect)
                    page_item.reload_page()
                    self.document_modified.emit()
                    
                    annot_scene_topleft = QPointF(
                        page_item.pos().x() + self.dragged_annot_rect.x0 * self.zoom,
                        page_item.pos().y() + self.dragged_annot_rect.y0 * self.zoom
                    )
                    viewport_pos = self.mapFromScene(annot_scene_topleft)
                    
                    self.active_text_widget = TextInputWidget(self.viewport())
                    self.active_text_widget.scene_pos = annot_scene_topleft
                    self.active_text_widget.page_num = self.dragged_annot_page
                    self.active_text_widget.editing_annot_rect = self.dragged_annot_rect
                    self.active_text_widget.editing_annot_page = self.dragged_annot_page
                    self.active_text_widget.color_pdf = self.dragged_annot_color
                    self.active_text_widget.font_size = self.dragged_annot_fontsize
                    
                    self.active_text_widget.editing_done.connect(self.finish_text_input)
                    
                    screen_font_size = self.dragged_annot_fontsize * self.zoom
                    font = QFont("helvetica")
                    font.setPixelSize(int(screen_font_size))
                    self.active_text_widget.setFont(font)
                    self.active_text_widget.setPlainText(self.dragged_annot_text)
                    
                    r = int(self.dragged_annot_color[0] * 255)
                    g = int(self.dragged_annot_color[1] * 255)
                    b = int(self.dragged_annot_color[2] * 255)
                    self.active_text_widget.text_edit.setStyleSheet(
                        f"background: rgba(255, 255, 255, 0.4);"
                        f"color: rgb({r},{g},{b});"
                        f"border: 1px dashed #3b82f6;"
                        f"padding: 0px;"
                        f"margin: 0px;"
                        f"outline: none;"
                    )
                    
                    # Keep original annotation width exactly, with a minimum of 50 points
                    max_width = max(50.0, self.dragged_annot_rect.width)
                    self.active_text_widget.auto_width = False
                    self.active_text_widget.text_edit.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
                    # The QFrame must be 18px wider than the text width to fit the handles (8px each) and border (2px)!
                    widget_width = int(max_width * self.zoom) + 18
                    
                    # Set geometry and auto-adjust height
                    self.active_text_widget.setGeometry(
                        int(viewport_pos.x()) - 8, # Shift left by 8px so the inner text aligns perfectly with where the PDF text was!
                        int(viewport_pos.y()), 
                        widget_width, 
                        30
                    )
                    self.active_text_widget.text_edit.adjust_height_from_layout(self.active_text_widget.text_edit.document().documentLayout().documentSize())
                    self.active_text_widget.show()
                    self.active_text_widget.setFocus()
                    
            event.accept()
            return

        if not self.drawing:
            super().mouseReleaseEvent(event)
            self.cleanup_temp_rect()
            return

        self.drawing = False
        tool = self.state.active_tool
        
        if tool == Tool.PEN:
            if self.temp_path_item:
                self._scene.removeItem(self.temp_path_item)
                self.temp_path_item = None
            self.active_path = None
                
            if len(self.current_stroke_points) >= 2 and self.active_page_num != -1:
                self.pdf_doc.add_pen_annotation(
                    self.active_page_num, 
                    self.current_stroke_points, 
                    self.state.active_color_pdf,
                    width=self.state.active_line_width
                )
                self.page_items[self.active_page_num].reload_page()
                self.document_modified.emit()
                
        elif tool in (Tool.SQUARE, Tool.ARROW):
            if hasattr(self, 'temp_shape_item') and self.temp_shape_item is not None:
                try:
                    self._scene.removeItem(self.temp_shape_item)
                except Exception:
                    pass
                self.temp_shape_item = None
                
            if self.active_page_num != -1:
                active_item = self.page_items[self.active_page_num]
                local_pos = scene_pos - active_item.pos()
                
                p1_pdf = self.get_pdf_point(self.drag_start_local_pos)
                p2_pdf = self.get_pdf_point(local_pos)
                
                if tool == Tool.SQUARE:
                    x0 = min(p1_pdf.x, p2_pdf.x)
                    y0 = min(p1_pdf.y, p2_pdf.y)
                    x1 = max(p1_pdf.x, p2_pdf.x)
                    y1 = max(p1_pdf.y, p2_pdf.y)
                    pdf_rect = fitz.Rect(x0, y0, x1, y1)
                    if pdf_rect.width > 2 and pdf_rect.height > 2:
                        self.pdf_doc.add_square_annotation(
                            self.active_page_num,
                            pdf_rect,
                            self.state.active_color_pdf,
                            width=self.state.active_line_width
                        )
                        self.page_items[self.active_page_num].reload_page()
                        self.document_modified.emit()
                        
                elif tool == Tool.ARROW:
                    dist = ((p1_pdf.x - p2_pdf.x)**2 + (p1_pdf.y - p2_pdf.y)**2)**0.5
                    if dist > 2:
                        self.pdf_doc.add_arrow_annotation(
                            self.active_page_num,
                            p1_pdf,
                            p2_pdf,
                            self.state.active_color_pdf,
                            width=self.state.active_line_width
                        )
                        self.page_items[self.active_page_num].reload_page()
                        self.document_modified.emit()
                
        elif tool == Tool.HIGHLIGHT:
            self.apply_highlight_to_selection()
                
        elif tool == Tool.SELECT:
            self.copy_selection_to_clipboard()
            
        self.active_page_num = -1
        self.cleanup_temp_rect()

    def erase_at(self, page_num, local_pos):
        pdf_point = self.get_pdf_point(local_pos)
        if self.pdf_doc.delete_annotation_at(page_num, pdf_point):
            self.page_items[page_num].reload_page()
            self.document_modified.emit()

    def find_closest_word_index(self, page_num, local_pos):
        """Finds closest word index on a specific page using local page coordinates."""
        pdf_point = self.get_pdf_point(local_pos)
        words = self.pdf_doc.get_words(page_num)
        if not words:
            return -1
            
        # Contain check
        for idx, w in enumerate(words):
            rect = fitz.Rect(w[0], w[1], w[2], w[3])
            if rect.contains(pdf_point):
                return idx
                
        # Proximity distance check
        min_dist = float('inf')
        closest_idx = -1
        for idx, w in enumerate(words):
            cx = (w[0] + w[2]) / 2.0
            cy = (w[1] + w[3]) / 2.0
            dist = (pdf_point.x - cx)**2 + (pdf_point.y - cy)**2
            if dist < min_dist:
                min_dist = dist
                closest_idx = idx
        return closest_idx

    def update_selection_overlays(self):
        self.clear_selected_word_graphics()
        if self.active_page_num == -1 or self.selection_start_word_idx == -1 or self.selection_end_word_idx == -1:
            return
            
        words = self.pdf_doc.get_words(self.active_page_num)
        start = min(self.selection_start_word_idx, self.selection_end_word_idx)
        end = max(self.selection_start_word_idx, self.selection_end_word_idx)
        
        tool = self.state.active_tool
        if tool == Tool.HIGHLIGHT:
            color = QColor(*self.state.active_color_rgb)
            color.setAlpha(90)
        else:
            color = QColor(59, 130, 246, 90)
            
        active_item = self.page_items[self.active_page_num]
        
        for idx in self.selected_word_indices:
            if idx < 0 or idx >= len(words):
                continue
            w = words[idx]
            word_rect = fitz.Rect(w[0], w[1], w[2], w[3])
            
            # Map page local coords to scene coordinates
            scene_rect = QRectF(
                active_item.pos().x() + word_rect.x0 * self.zoom,
                active_item.pos().y() + word_rect.y0 * self.zoom,
                word_rect.width * self.zoom,
                word_rect.height * self.zoom
            )
            item = QGraphicsRectItem(scene_rect)
            item.setBrush(color)
            item.setPen(QPen(Qt.PenStyle.NoPen))
            item.setZValue(999.0)
            self._scene.addItem(item)
            self.selected_word_items.append(item)

    def apply_highlight_to_selection(self):
        if self.active_page_num == -1 or not hasattr(self, 'selected_word_indices') or not self.selected_word_indices:
            self.clear_selection_graphics()
            return
            
        words = self.pdf_doc.get_words(self.active_page_num)
        # Process the selected word indices sorted in order of appearance
        sorted_indices = sorted(self.selected_word_indices)
        
        lines_rects = []
        current_rect = None
        
        for idx in sorted_indices:
            if idx < 0 or idx >= len(words):
                continue
            w = words[idx]
            word_rect = fitz.Rect(w[0], w[1], w[2], w[3])
            
            if current_rect is None:
                current_rect = word_rect
            else:
                same_line = abs(w[1] - current_rect.y0) < 5 and abs(w[3] - current_rect.y1) < 5
                adjacent = (w[0] - current_rect.x1) < 20
                if same_line and adjacent:
                    current_rect = fitz.Rect(
                        min(current_rect.x0, w[0]),
                        min(current_rect.y0, w[1]),
                        max(current_rect.x1, w[2]),
                        max(current_rect.y1, w[3])
                    )
                else:
                    lines_rects.append(current_rect)
                    current_rect = word_rect
                    
        if current_rect is not None:
            lines_rects.append(current_rect)
            
        if lines_rects:
            self.pdf_doc.add_highlight_annotation(
                self.active_page_num,
                lines_rects,
                self.state.active_color_pdf
            )
            self.page_items[self.active_page_num].reload_page()
            self.document_modified.emit()
            
        self.clear_selection_graphics()

    def copy_selection_to_clipboard(self):
        """Processes the selected text range, saving it in memory but NOT auto-copying to clipboard."""
        if self.active_page_num == -1 or not hasattr(self, 'selected_word_indices') or not self.selected_word_indices:
            self.clear_selection_graphics()
            return
            
        words = self.pdf_doc.get_words(self.active_page_num)
        sorted_indices = sorted(self.selected_word_indices)
        
        selected_words = [words[idx] for idx in sorted_indices if 0 <= idx < len(words)]
        self.selected_text_content = " ".join([w[4] for w in selected_words])
        
        if self.selected_text_content:
            self.status_message.emit(f"Selected text (Press Ctrl+C to copy): \"{self.selected_text_content[:40]}...\"")

    def get_selected_text(self):
        """Returns the currently selected text contents."""
        return self.selected_text_content

    def finish_text_input(self, text, widget):
        if self.active_text_widget == widget:
            self.active_text_widget = None
            
        widget.deleteLater()
        
        if not self.pdf_doc:
            return
            
        if text is None:
            # User cancelled, restore original annotation if we were editing one
            if widget.editing_annot_rect and widget.editing_annot_page >= 0:
                self.pdf_doc.add_text_annotation(
                    widget.editing_annot_page,
                    widget.editing_annot_rect,
                    self.dragged_annot_text,
                    widget.color_pdf,
                    fontsize=widget.font_size
                )
                page_item = self.page_items[widget.editing_annot_page]
                page_item.reload_page()
            return
            
        if text == "":
            # User cleared text, since we deleted the annotation when editing started, it is already deleted.
            return
            
        # Removed short-circuit that restored the original rect if text was unchanged,
        # so that manual width adjustments via handles are properly applied even if text didn't change!
            
        if widget.scene_pos:
            page_item, local_pos = self.get_page_under_pos(widget.scene_pos)
            if page_item:
                pdf_point = self.get_pdf_point(local_pos)
                
                # Convert widget dimensions (pixels) back to PDF points
                # If auto_width is False, use the text_edit width (excluding handles) to perfectly match the allocated text space.
                doc_width = widget.text_edit.document().idealWidth() + 16.0 if getattr(widget, 'auto_width', True) else widget.text_edit.width()
                rect_width = doc_width / self.zoom
                
                # Height is the true text document height plus a minimal vertical buffer (2 PDF points)
                # to prevent the invisible bounding box from extending far below the text
                rect_height = (widget.text_edit.document().size().height() / self.zoom) + 2.0
                
                # Clamp coordinates to stay completely inside page boundaries (allowing a 10-point margin)
                page_width, page_height = self.pdf_doc.get_page_size(page_item.page_num)
                
                start_x = pdf_point.x
                start_y = pdf_point.y # Removed artificial offset, letting the Qt creation offset dictate the position
                
                if start_x + rect_width > page_width - 10.0:
                    start_x = max(10.0, page_width - rect_width - 10.0)
                if start_x < 10.0:
                    start_x = 10.0
                    
                if start_y + rect_height > page_height - 10.0:
                    start_y = max(10.0, page_height - rect_height - 10.0)
                if start_y < 10.0:
                    start_y = 10.0
                    
                rect = fitz.Rect(start_x, start_y, start_x + rect_width, start_y + rect_height)
                
                self.pdf_doc.add_text_annotation(
                    page_item.page_num,
                    rect,
                    text,
                    widget.color_pdf,
                    fontsize=widget.font_size
                )
                page_item.reload_page()
                self.document_modified.emit()

    def clear_selected_word_graphics(self):
        for item in self.selected_word_items:
            try:
                self._scene.removeItem(item)
            except Exception:
                pass
        self.selected_word_items.clear()
        
    def clear_selection_graphics(self):
        self.selection_start_word_idx = -1
        self.selection_end_word_idx = -1
        self.selected_word_indices = []
        self.clear_selected_word_graphics()
        self.selected_text_content = ""
        self.cleanup_temp_rect()

    def is_pos_over_any_word(self, page_num, local_pos):
        if not self.pdf_doc:
            return False
        pdf_point = self.get_pdf_point(local_pos)
        words = self.pdf_doc.get_words(page_num)
        if not words:
            return False
        for w in words:
            rect = fitz.Rect(w[0], w[1], w[2], w[3])
            if rect.contains(pdf_point):
                return True
        return False

    def is_pos_over_any_freetext(self, page_num, local_pos):
        if not self.pdf_doc:
            return False
        pdf_point = self.get_pdf_point(local_pos)
        page = self.pdf_doc.doc[page_num]
        for annot in page.annots():
            if annot.type[1] == "FreeText" and annot.rect.contains(pdf_point):
                return True
        return False

    def update_cursor_for_position(self, scene_pos):
        if not self.pdf_doc or not self.page_items:
            self.viewport().setCursor(Qt.CursorShape.ArrowCursor)
            return

        page_item, local_pos = self.get_page_under_pos(scene_pos)
        tool = self.state.active_tool

        if tool in (Tool.SELECT, Tool.HIGHLIGHT):
            if page_item:
                if tool == Tool.SELECT and page_item.get_link_at(local_pos) is not None:
                    self.viewport().setCursor(Qt.CursorShape.PointingHandCursor)
                    return
                over_text = self.is_pos_over_any_word(page_item.page_num, local_pos) or self.is_pos_over_any_freetext(page_item.page_num, local_pos)
                if over_text:
                    self.viewport().setCursor(Qt.CursorShape.IBeamCursor)
                else:
                    self.viewport().setCursor(Qt.CursorShape.ArrowCursor)
            else:
                self.viewport().setCursor(Qt.CursorShape.ArrowCursor)
        elif tool == Tool.TEXT:
            self.viewport().setCursor(Qt.CursorShape.IBeamCursor)
        elif tool == Tool.PEN:
            self.viewport().setCursor(Qt.CursorShape.CrossCursor)
        elif tool == Tool.ERASER:
            self.viewport().setCursor(Qt.CursorShape.PointingHandCursor)
        else:
            self.viewport().setCursor(Qt.CursorShape.ArrowCursor)

    def update_cursor(self):
        from PyQt6.QtGui import QCursor
        local_pos = self.viewport().mapFromGlobal(QCursor.pos())
        self.update_cursor_for_position(self.mapToScene(local_pos))

    def keyPressEvent(self, event):
        super().keyPressEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.position_search_bar()

    def show_search_bar(self):
        if not self.pdf_doc:
            return
        
        if not self.search_bar:
            from app.main_window import PDFSearchBar
            self.search_bar = PDFSearchBar(self)
            self.search_bar.search_requested.connect(self.start_search)
            self.search_bar.next_match.connect(lambda: self.navigate_search_match("next"))
            self.search_bar.prev_match.connect(lambda: self.navigate_search_match("prev"))
            self.search_bar.closed.connect(self.clear_search)
            
        self.search_bar.show()
        self.position_search_bar()
        self.search_bar.input_field.setFocus()
        self.search_bar.input_field.selectAll()

    def position_search_bar(self):
        if hasattr(self, 'search_bar') and self.search_bar and self.search_bar.isVisible():
            sb_w = 380
            sb_h = self.search_bar.sizeHint().height() or 40
            v_width = self.viewport().width()
            x = v_width - sb_w - 15
            y = 15
            x = max(10, x)
            self.search_bar.setGeometry(x, y, sb_w, sb_h)

    def start_search(self, query):
        self.pending_search_query = query
        self.search_timer.start(800)  # Wait for 800ms of inactivity before triggering

    def trigger_search(self):
        query = self.pending_search_query
        # Cancel current search asynchronously
        if hasattr(self, 'search_worker') and self.search_worker:
            old_worker = self.search_worker
            old_worker.cancel()
            try:
                old_worker.progress.disconnect()
                old_worker.finished.disconnect()
            except TypeError:
                pass
            # Make sure it discards itself from tracking set when it finishes in the background
            old_worker.finished.connect(lambda w=old_worker: self.running_workers.discard(w))
            self.search_worker = None

        # Clear search highlights
        for items in self.search_highlights.values():
            for item in items:
                if item.scene():
                    self.scene().removeItem(item)
        self.search_highlights.clear()
        self.flat_highlight_items = []
        self.search_matches = []
        self.current_match_idx = -1

        if not query or not self.pdf_doc:
            if self.search_bar:
                self.search_bar.update_status(0, 0)
            return

        # Start background search thread
        worker = PDFSearchWorker(self.pdf_doc.filepath, query, self)
        worker.progress.connect(self.on_search_progress)
        worker.finished.connect(self.on_search_finished)
        worker.finished.connect(lambda: self.running_workers.discard(worker))
        self.running_workers.add(worker)
        self.search_worker = worker
        worker.start()

    def on_search_progress(self, page_num, rects):
        if not self.pdf_doc or page_num >= len(self.page_items):
            return
            
        page_item = self.page_items[page_num]
        zoom = self.zoom
        
        for r in rects:
            self.search_matches.append((page_num, r))
            
            local_rect = QRectF(r.x0 * zoom, r.y0 * zoom, r.width * zoom, r.height * zoom)
            highlight_item = QGraphicsRectItem(local_rect, page_item)
            highlight_item.setBrush(QBrush(QColor(255, 255, 0, 76)))
            highlight_item.setPen(QPen(Qt.PenStyle.NoPen))
            highlight_item.setZValue(2.0)
            
            if page_num not in self.search_highlights:
                self.search_highlights[page_num] = []
            self.search_highlights[page_num].append(highlight_item)
            self.flat_highlight_items.append(highlight_item)

        # If this is the first progress callback, highlight the first match
        if self.current_match_idx == -1 and len(self.search_matches) > 0:
            self.current_match_idx = 0
            self.highlight_active_match()
            
        if self.search_bar:
            self.search_bar.update_status(self.current_match_idx + 1 if self.current_match_idx >= 0 else 0, len(self.search_matches))

    def on_search_finished(self, results):
        total = len(self.search_matches)
        if total == 0:
            self.status_message.emit("No matches found")
            if self.search_bar:
                self.search_bar.update_status(0, 0)
        else:
            self.status_message.emit(f"Search finished: {total} matches found")

    def navigate_search_match(self, direction):
        if not self.search_matches:
            return
        
        if direction == "next":
            self.current_match_idx = (self.current_match_idx + 1) % len(self.search_matches)
        else:
            self.current_match_idx = (self.current_match_idx - 1) % len(self.search_matches)
            
        self.highlight_active_match()
        if self.search_bar:
            self.search_bar.update_status(self.current_match_idx + 1, len(self.search_matches))

    def highlight_active_match(self):
        if not self.search_matches or self.current_match_idx < 0 or self.current_match_idx >= len(self.search_matches):
            return

        # Reset colors of all highlight items to standard yellow
        for item in self.flat_highlight_items:
            item.setBrush(QBrush(QColor(255, 255, 0, 76)))
            item.setPen(QPen(Qt.PenStyle.NoPen))
            item.setZValue(2.0)
            
        # Highlight the current active match in orange
        if self.current_match_idx < len(self.flat_highlight_items):
            active_item = self.flat_highlight_items[self.current_match_idx]
            active_item.setBrush(QBrush(QColor(249, 115, 22, 128))) # Orange 50% opacity
            active_item.setPen(QPen(QColor("#f97316"), 1))
            active_item.setZValue(3.0) # Bring to front
        
        # Center view on active match
        page_num, rect = self.search_matches[self.current_match_idx]
        page_item = self.page_items[page_num]
        zoom = self.zoom
        scene_rect = QRectF(
            page_item.pos().x() + rect.x0 * zoom,
            page_item.pos().y() + rect.y0 * zoom,
            rect.width * zoom,
            rect.height * zoom
        )
        self.centerOn(scene_rect.center())

    def clear_search(self):
        self.search_timer.stop()
        if hasattr(self, 'search_worker') and self.search_worker:
            old_worker = self.search_worker
            old_worker.cancel()
            try:
                old_worker.progress.disconnect()
                old_worker.finished.disconnect()
            except TypeError:
                pass
            old_worker.finished.connect(lambda w=old_worker: self.running_workers.discard(w))
            self.search_worker = None

        # Remove all highlights from the scene/pages
        for page_num, items in self.search_highlights.items():
            for item in items:
                if item.scene():
                    self.scene().removeItem(item)
        self.search_highlights.clear()
        self.flat_highlight_items = []
        self.search_matches = []
        self.current_match_idx = -1
        self.status_message.emit("Search cleared")

    def update_search_highlights_zoom(self):
        # Remove old highlights
        for page_num, items in self.search_highlights.items():
            for item in items:
                if item.scene():
                    self.scene().removeItem(item)
        self.search_highlights.clear()
        self.flat_highlight_items = []
        
        if not self.search_matches:
            return
            
        # Recreate highlights with the new zoom factor
        for page_num, r in self.search_matches:
            page_item = self.page_items[page_num]
            zoom = self.zoom
            local_rect = QRectF(r.x0 * zoom, r.y0 * zoom, r.width * zoom, r.height * zoom)
            
            highlight_item = QGraphicsRectItem(local_rect, page_item)
            highlight_item.setBrush(QBrush(QColor(255, 255, 0, 76)))
            highlight_item.setPen(QPen(Qt.PenStyle.NoPen))
            highlight_item.setZValue(2.0)
            
            if page_num not in self.search_highlights:
                self.search_highlights[page_num] = []
            self.search_highlights[page_num].append(highlight_item)
            self.flat_highlight_items.append(highlight_item)
            
        # Re-apply active match highlight
        if self.current_match_idx >= 0 and self.current_match_idx < len(self.flat_highlight_items):
            active_item = self.flat_highlight_items[self.current_match_idx]
            active_item.setBrush(QBrush(QColor(249, 115, 22, 128)))
            active_item.setPen(QPen(QColor("#f97316"), 1))
            active_item.setZValue(3.0)
