import fitz

def create_pdf():
    doc = fitz.open()
    
    # Page 1 - Welcome and Shortcuts
    page1 = doc.new_page(width=595, height=842) # A4 size in points
    
    # Header
    page1.insert_text((50, 80), "Lightweight PDF Annotator", fontsize=24, color=(0.15, 0.2, 0.4))
    page1.insert_text((50, 110), "Test and Tutorial Document", fontsize=14, color=(0.4, 0.4, 0.4))
    
    # Body
    y = 170
    page1.insert_text((50, y), "Welcome! This is a simple test document to try out your new PDF annotator.", fontsize=12)
    y += 30
    page1.insert_text((50, y), "Use the following keyboard shortcuts to switch tools and colors:", fontsize=12)
    
    y += 30
    shortcuts = [
        ("V", "Selection Tool (Select text to copy to clipboard)"),
        ("H", "Highlighter (Select areas to highlight text in active color)"),
        ("P", "Pen Tool (Draw freehand ink strokes in active color)"),
        ("T", "Text Tool (Click on PDF to type text in active color)"),
        ("E", "Eraser Tool (Click/drag over any annotation to delete it)")
    ]
    for key, desc in shortcuts:
        page1.insert_text((70, y), f"•  {key}", fontsize=11, color=(0.1, 0.5, 0.8))
        page1.insert_text((110, y), desc, fontsize=11)
        y += 22
        
    y += 15
    page1.insert_text((50, y), "Use keys 1 to 5 to switch annotation colors:", fontsize=12)
    
    y += 25
    colors = [
        ("1", "Yellow", (0.8, 0.7, 0.1)),
        ("2", "Red", (0.8, 0.1, 0.1)),
        ("3", "Green", (0.1, 0.6, 0.1)),
        ("4", "Blue", (0.1, 0.1, 0.8)),
        ("5", "Black", (0.0, 0.0, 0.0))
    ]
    for key, name, rgb in colors:
        page1.insert_text((70, y), f"•  {key}", fontsize=11, color=rgb)
        page1.insert_text((110, y), name, fontsize=11)
        y += 22
        
    y += 20
    page1.insert_text((50, y), "Controls:", fontsize=12)
    page1.insert_text((70, y+25), "•  Left / Right Arrow  -  Go to Previous / Next page", fontsize=11)
    page1.insert_text((70, y+45), "•  Ctrl + = / Ctrl + -  -  Zoom In / Zoom Out", fontsize=11)
    page1.insert_text((70, y+65), "•  Ctrl + S             -  Save your changes to the PDF", fontsize=11)
    
    # Page 2 - Sandbox
    page2 = doc.new_page(width=595, height=842)
    page2.insert_text((50, 80), "Sandbox Page", fontsize=24, color=(0.15, 0.2, 0.4))
    page2.insert_text((50, 110), "Use this space to draw, highlight, and write text freely.", fontsize=12)
    
    # Draw some guidelines/grids
    shape = page2.new_shape()
    shape.draw_rect(fitz.Rect(50, 150, 545, 750))
    shape.finish(color=(0.8, 0.8, 0.8), width=1, dashes="[3 3] 0")
    shape.commit()
    
    page2.insert_text((60, 170), "Draw inside the box below:", fontsize=10, color=(0.6, 0.6, 0.6))
    
    # Set Table of Contents (Outline)
    toc = [
        [1, "1. Welcome & Keyboard Shortcuts", 1],
        [2, "1.1 Tools Overview", 1],
        [2, "1.2 Colors Overview", 1],
        [1, "2. Drawing Sandbox", 2]
    ]
    doc.set_toc(toc)
    
    doc.save("test.pdf")
    doc.close()
    print("Created test.pdf with outline successfully!")

if __name__ == "__main__":
    create_pdf()
