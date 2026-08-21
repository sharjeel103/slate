import fitz  # PyMuPDF
from PyQt6.QtGui import QImage
import os

class PDFDocument:
    def __init__(self, filepath):
        self.filepath = filepath
        self.doc = fitz.open(filepath)
        # Cache page sizes to avoid C-binding lookup overhead on every zoom layout update
        self.page_sizes = []
        for page in self.doc:
            self.page_sizes.append((page.rect.width, page.rect.height))
        
    @property
    def page_count(self):
        return len(self.doc)
        
    def get_page_size(self, page_num):
        """Returns (width, height) of the page in PDF points."""
        return self.page_sizes[page_num]
        
    def render_page(self, page_num, zoom=2.0, dpr=1.0):
        """Renders the page to a PyQt QImage with device pixel ratio scaling."""
        page = self.doc[page_num]
        total_scale = zoom * dpr
        mat = fitz.Matrix(total_scale, total_scale)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        
        # Create QImage from raw RGB data
        # We call .copy() to duplicate the buffer, making it safe from garbage collection issues with pix
        qimg = QImage(
            pix.samples, 
            pix.width, 
            pix.height, 
            pix.stride, 
            QImage.Format.Format_RGB888
        ).copy()
        
        if dpr != 1.0:
            qimg.setDevicePixelRatio(dpr)
            
        return qimg

    def get_words(self, page_num):
        """Returns list of word info tuples from the page: (x0, y0, x1, y1, "word", block, line, word_no)"""
        page = self.doc[page_num]
        return page.get_text("words")

    def add_pen_annotation(self, page_num, point_list, color_rgb, width=2):
        """
        Adds a freehand ink annotation to the page.
        point_list: list of (x, y) coordinates in PDF points.
        color_rgb: tuple of (r, g, b) floats (0.0 to 1.0).
        width: line thickness.
        """
        if len(point_list) < 2:
            return
        
        page = self.doc[page_num]
        # PyMuPDF add_ink_annot expects a list of lists of float pairs, e.g. [[(x1, y1), (x2, y2), ...]]
        raw_points = [[(float(p[0]), float(p[1])) for p in point_list]]
        annot = page.add_ink_annot(raw_points)
        annot.set_colors(stroke=color_rgb)
        annot.set_border(width=width)
        annot.update()

    def add_highlight_annotation(self, page_num, rect_list, color_rgb):
        """
        Adds highlight annotation.
        rect_list: list of fitz.Rect objects in PDF points.
        color_rgb: tuple of (r, g, b) floats (0.0 to 1.0).
        """
        if not rect_list:
            return
            
        page = self.doc[page_num]
        # Highlighting works best by converting Rects to Quads
        quads = [r.quad for r in rect_list]
        annot = page.add_highlight_annot(quads)
        annot.set_colors(stroke=color_rgb)
        annot.update()

    def add_text_annotation(self, page_num, rect, text, color_rgb, fontsize=12):
        """
        Adds a free text (written on PDF) annotation.
        rect: fitz.Rect in PDF points.
        text: string text.
        color_rgb: tuple of (r, g, b) floats (0.0 to 1.0).
        fontsize: int font size.
        """
        page = self.doc[page_num]
        # Add FreeText annotation. PyMuPDF handles rect fitting.
        annot = page.add_freetext_annot(
            rect, 
            text, 
            fontsize=fontsize, 
            fontname="helv", 
            text_color=color_rgb
        )
        annot.update()

    def add_square_annotation(self, page_num, rect, color_rgb, width=2):
        """
        Adds a rectangle/square outline annotation.
        rect: fitz.Rect in PDF points.
        color_rgb: tuple of (r, g, b) floats (0.0 to 1.0).
        width: line thickness.
        """
        page = self.doc[page_num]
        annot = page.add_rect_annot(rect)
        annot.set_colors(stroke=color_rgb)
        annot.set_border(width=width)
        annot.update()
        return annot.rect

    def add_line_annotation(self, page_num, p1, p2, color_rgb, width=2):
        """
        Adds a straight line annotation.
        p1, p2: fitz.Point or (x, y) tuple in PDF points.
        color_rgb: tuple of (r, g, b) floats (0.0 to 1.0).
        width: line thickness.
        """
        page = self.doc[page_num]
        annot = page.add_line_annot(p1, p2)
        annot.set_colors(stroke=color_rgb)
        annot.set_border(width=width)
        annot.update()
        return annot.rect

    def add_arrow_annotation(self, page_num, p1, p2, color_rgb, width=2):
        """
        Adds a line with a custom-proportioned arrowhead as a single Ink annotation.
        p1, p2: fitz.Point or (x, y) tuple in PDF points.
        color_rgb: tuple of (r, g, b) floats (0.0 to 1.0).
        width: line thickness.
        """
        page = self.doc[page_num]
        
        x1, y1 = float(p1[0]), float(p1[1])
        x2, y2 = float(p2[0]), float(p2[1])
        
        dx = x2 - x1
        dy = y2 - y1
        length = (dx**2 + dy**2)**0.5
        
        if length == 0:
            return
            
        # Normalize direction vector
        ux = dx / length
        uy = dy / length
        
        # Calculate balanced arrowhead wing size
        base_size = 6.0 + 1.5 * width
        base_size = min(base_size, 18.0)
        arrow_size = min(base_size, length * 0.3)
        if length > 10:
            arrow_size = max(arrow_size, 5.0)
        
        # Rotate vector to get arrowhead wings (30-degree angle from shaft pointing backward)
        # cos(150 deg) = -0.866, sin(150 deg) = 0.5
        cos_val = -0.866
        sin_val = 0.5
        
        rx1 = ux * cos_val - uy * sin_val
        ry1 = ux * sin_val + uy * cos_val
        
        rx2 = ux * cos_val - uy * (-sin_val)
        ry2 = ux * (-sin_val) + uy * cos_val
        
        w1_x = x2 + arrow_size * rx1
        w1_y = y2 + arrow_size * ry1
        
        w2_x = x2 + arrow_size * rx2
        w2_y = y2 + arrow_size * ry2
        
        # Define paths for the shaft and two wings
        shaft = [(x1, y1), (x2, y2)]
        wing1 = [(x2, y2), (w1_x, w1_y)]
        wing2 = [(x2, y2), (w2_x, w2_y)]
        
        annot = page.add_ink_annot([shaft, wing1, wing2])
        annot.set_colors(stroke=color_rgb)
        annot.set_border(width=width)
        annot.update()
        return annot.rect


    def get_freetext_fontsize(self, annot):
        """
        Retrieves the font size of a FreeText annotation.
        Uses low-level PDF xref parsing. Falls back to 12 if not found.
        """
        try:
            if not annot or not hasattr(annot, "xref"):
                return 12
            key_type, da_val = self.doc.xref_get_key(annot.xref, "DA")
            if da_val and da_val != "null":
                if isinstance(da_val, bytes):
                    da_val = da_val.decode('utf-8', errors='ignore')
                elif not isinstance(da_val, str):
                    da_val = str(da_val)
                import re
                match = re.search(r'([\d\.]+)\s+Tf', da_val)
                if match:
                    return float(match.group(1))
        except Exception:
            pass
        return 12

    def get_freetext_color(self, annot):
        """
        Retrieves the text color (r, g, b) of a FreeText annotation.
        Uses low-level PDF xref parsing. Falls back to (0.0, 0.0, 0.0) if not found.
        """
        try:
            if not annot or not hasattr(annot, "xref"):
                return (0.0, 0.0, 0.0)
            key_type, da_val = self.doc.xref_get_key(annot.xref, "DA")
            if da_val and da_val != "null":
                if isinstance(da_val, bytes):
                    da_val = da_val.decode('utf-8', errors='ignore')
                elif not isinstance(da_val, str):
                    da_val = str(da_val)
                import re
                # Try RGB search: e.g. "0.46 0.90 0.58 rg" or "0 0 0 rg"
                rgb_match = re.search(r'([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s*rg', da_val, re.IGNORECASE)
                if rgb_match:
                    r = float(rgb_match.group(1))
                    g = float(rgb_match.group(2))
                    b = float(rgb_match.group(3))
                    return (r, g, b)
                # Try CMYK search: e.g. "0 0 0 1 k"
                cmyk_match = re.search(r'([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s*k', da_val, re.IGNORECASE)
                if cmyk_match:
                    c = float(cmyk_match.group(1))
                    m = float(cmyk_match.group(2))
                    y = float(cmyk_match.group(3))
                    k = float(cmyk_match.group(4))
                    r = (1.0 - c) * (1.0 - k)
                    g = (1.0 - m) * (1.0 - k)
                    b = (1.0 - y) * (1.0 - k)
                    return (r, g, b)
                # Try grayscale search: e.g. "0 g" or "0.5 g"
                gray_match = re.search(r'\b([\d\.]+)\s*g\b', da_val, re.IGNORECASE)
                if gray_match:
                    gray = float(gray_match.group(1))
                    return (gray, gray, gray)
        except Exception:
            pass
        return (0.0, 0.0, 0.0)

    def delete_annotation_at(self, page_num, pdf_point):
        """
        Deletes the first annotation that contains the pdf_point.
        pdf_point: fitz.Point.
        Returns True if an annotation was deleted, False otherwise.
        """
        page = self.doc[page_num]
        # Iterate through annotations
        for annot in page.annots():
            rect = annot.rect
            # Expand rect slightly to make it easier to hit lines/points
            click_tolerance = 4
            tolerance_rect = fitz.Rect(
                rect.x0 - click_tolerance,
                rect.y0 - click_tolerance,
                rect.x1 + click_tolerance,
                rect.y1 + click_tolerance
            )
            
            if tolerance_rect.contains(pdf_point):
                # If it's an ink annotation, we can check if click is close to any point in the path,
                # but for simplicity and responsiveness, deleting via rect collision is highly effective.
                page.delete_annot(annot)
                return True
        return False

    def delete_annotation_by_rect(self, page_num, target_rect):
        """Deletes the annotation on page_num that matches target_rect."""
        page = self.doc[page_num]
        for annot in page.annots():
            if annot.rect and target_rect:
                if abs(annot.rect.x0 - target_rect.x0) < 0.2 and abs(annot.rect.y0 - target_rect.y0) < 0.2:
                    page.delete_annot(annot)
                    return True
        return False

    def save(self, output_path=None):
        """Saves the document. Uses incremental save if output_path is None or matches filepath."""
        target = output_path if output_path else self.filepath
        
        # If saving to the same file, do a super fast incremental save
        if target == self.filepath:
            try:
                self.doc.save(self.doc.name, incremental=True, encryption=fitz.PDF_ENCRYPT_KEEP)
                return True
            except Exception as e:
                print(f"Incremental save failed: {e}. Falling back to full save...")
                
        # Otherwise, save to a different path or fall back to full save
        temp_path = target + ".tmp"
        try:
            # Save using garbage=1 (fast cleaning) instead of garbage=3 to avoid freezing
            self.doc.save(temp_path, garbage=1, deflate=True)
            
            if target == self.filepath:
                # If we are overwriting the active file (fallback case), we must close and reopen
                self.doc.close()
                if os.path.exists(target):
                    os.remove(target)
                os.rename(temp_path, target)
                self.doc = fitz.open(target)
            else:
                # Saving to a new copy
                if os.path.exists(target):
                    os.remove(target)
                os.rename(temp_path, target)
            return True
        except Exception as e:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
            raise e
