import fitz

def create_pdf():
    doc = fitz.open()
    
    # Pre-allocate the pages first
    doc.new_page(width=595, height=842) # Page 1
    doc.new_page(width=595, height=842) # Page 2
    doc.new_page(width=595, height=842) # Page 3
    
    # Retrieve bound page references
    page1 = doc[0]
    page2 = doc[1]
    page3 = doc[2]
    
    # ----------------------------------------------------
    # Page 1: Welcome & Interactive Navigation Test
    # ----------------------------------------------------
    # Header
    page1.insert_text((50, 70), "Slate PDF Reader & Annotator", fontsize=22, color=(0.11, 0.2, 0.45))
    page1.insert_text((50, 95), "User Manual & Interactive Test Document", fontsize=12, color=(0.4, 0.4, 0.4))
    
    # Intro
    y = 150
    page1.insert_text((50, y), "Welcome to Slate! This document acts as both a user manual and an interactive", fontsize=11)
    y += 18
    page1.insert_text((50, y), "sandbox to test Slate's custom tools, keyboard navigation, search, and link systems.", fontsize=11)
    
    # Section 1: Link Interception Test
    y += 40
    page1.insert_text((50, y), "1. Clickable Link Tests (Select Mode 'V' only)", fontsize=13, color=(0.11, 0.2, 0.45))
    
    y += 25
    page1.insert_text((50, y), "Below are two hyperlinks. Switch to Select Mode (press 'V') to click and test them:", fontsize=11)
    
    # Internal GOTO Link
    y += 25
    rect_goto = fitz.Rect(70, y - 10, 320, y + 5)
    page1.insert_text((70, y), "→  Click here to jump to Page 3 (Sandbox)", fontsize=11, color=(0.1, 0.5, 0.8))
    page1.insert_link({'kind': fitz.LINK_GOTO, 'from': rect_goto, 'page': 2}) # page index 2 is Page 3
    
    # External URI Link
    y += 22
    rect_uri = fitz.Rect(70, y - 10, 320, y + 5)
    page1.insert_text((70, y), "→  Click here to open the Slate Project Directory", fontsize=11, color=(0.1, 0.5, 0.8))
    page1.insert_link({'kind': fitz.LINK_URI, 'from': rect_uri, 'uri': 'https://github.com/sharjeel103/slate'})
    
    # Section 2: Vim-Style Document Search Test
    y += 45
    page1.insert_text((50, y), "2. Vim-Style Document Search Test", fontsize=13, color=(0.11, 0.2, 0.45))
    
    y += 25
    page1.insert_text((50, y), "Press Ctrl + F or '/' to open the floating, debounced search bar. Type 'sandbox' or", fontsize=11)
    y += 18
    page1.insert_text((50, y), "'banana' to see matches highlighted. Use Enter/Shift+Enter to jump between them.", fontsize=11)
    
    # Section 3: Sidebar Outline Navigation
    y += 40
    page1.insert_text((50, y), "3. Outline Sidebar navigation", fontsize=13, color=(0.11, 0.2, 0.45))
    
    y += 25
    page1.insert_text((50, y), "Press F9, O, or '0' to toggle the Table of Contents sidebar. You can use standard", fontsize=11)
    y += 18
    page1.insert_text((50, y), "Vim keys (j/k) to scroll the PDF canvas, and press Escape to close the sidebar.", fontsize=11)
    
    # Footer info
    page1.insert_text((50, 780), "Page 1 of 3", fontsize=9, color=(0.5, 0.5, 0.5))
    
    # ----------------------------------------------------
    # Page 2: Keyboard Reference & Shortcuts Manual
    # ----------------------------------------------------
    page2.insert_text((50, 70), "Keyboard Shortcuts & Tools Reference", fontsize=18, color=(0.11, 0.2, 0.45))
    
    y = 120
    # Annotation Tools
    page2.insert_text((50, y), "Annotation Tool Modes", fontsize=12, color=(0.11, 0.2, 0.45))
    y += 20
    tools = [
        ("V", "Select Mode (Text Selection & Link Interception)"),
        ("H", "Highlight Mode (Translucent highlighting overlay)"),
        ("P", "Pen Mode (Freehand vector ink strokes)"),
        ("T", "Text Mode (FreeText annotations - click anywhere to type)"),
        ("S", "Square Mode (Vector rectangles)"),
        ("A", "Arrow Mode (Vector directional arrows)"),
        ("C", "Callout Mode (Box -> Arrow -> Text workflow)"),
        ("E", "Eraser Mode (Click/drag to delete annotations)"),
        ("Hold Ctrl + Shift", "Temporary Eraser toggle (reverts back to active tool on release)")
    ]
    for key, desc in tools:
        page2.insert_text((70, y), f"•  {key}", fontsize=10, color=(0.1, 0.5, 0.8))
        page2.insert_text((160, y), desc, fontsize=10)
        y += 18
        
    y += 15
    # Color Palettes
    page2.insert_text((50, y), "Active Colors (Applies to Pen, Highlight, Shape, and Text Tools)", fontsize=12, color=(0.11, 0.2, 0.45))
    y += 20
    colors = [
        ("1", "Yellow"),
        ("2", "Blue"),
        ("3", "Green"),
        ("4", "Red"),
        ("5", "Black")
    ]
    for key, name in colors:
        page2.insert_text((70, y), f"•  {key}", fontsize=10, color=(0.1, 0.5, 0.8))
        page2.insert_text((110, y), name, fontsize=10)
        y += 16
        
    y += 15
    # View Navigation
    page2.insert_text((50, y), "Navigation & Zoom Shortcuts", fontsize=12, color=(0.11, 0.2, 0.45))
    y += 20
    navs = [
        ("j  /  k", "Scroll Down / Scroll Up by small offsets"),
        ("Shift + J", "Jump directly to the next page"),
        ("Shift + K", "Jump directly to the previous page"),
        ("→ / PageDown", "Next Page"),
        ("← / PageUp", "Previous Page"),
        ("Ctrl + =", "Zoom In"),
        ("Ctrl + -", "Zoom Out"),
        ("Ctrl + S", "Save PDF Document (Garbage collected fallback save on dirty checks)")
    ]
    for key, desc in navs:
        page2.insert_text((70, y), f"•  {key}", fontsize=10, color=(0.1, 0.5, 0.8))
        page2.insert_text((180, y), desc, fontsize=10)
        y += 18
        
    page2.insert_text((50, 780), "Page 2 of 3", fontsize=9, color=(0.5, 0.5, 0.5))
    
    # ----------------------------------------------------
    # Page 3: Sandbox Page
    # ----------------------------------------------------
    page3.insert_text((50, 70), "Drawing & Annotation Sandbox", fontsize=20, color=(0.11, 0.2, 0.45))
    page3.insert_text((50, 95), "Use this area to test drawing boxes, highlighters, pens, and text annotations.", fontsize=11, color=(0.4, 0.4, 0.4))
    
    # Draw guidelines
    shape = page3.new_shape()
    shape.draw_rect(fitz.Rect(50, 130, 545, 740))
    shape.finish(color=(0.75, 0.75, 0.75), width=1.5, dashes="[3 3] 0")
    shape.commit()
    
    page3.insert_text((60, 150), "Test Box - Draw or Type freely inside this boundary:", fontsize=10, color=(0.6, 0.6, 0.6))
    page3.insert_text((100, 300), "Search keyword banana: banana monkey banana tree banana.", fontsize=10, color=(0.4, 0.4, 0.4))
    
    page3.insert_text((50, 780), "Page 3 of 3", fontsize=9, color=(0.5, 0.5, 0.5))
    
    # Set Outline / Table of Contents
    toc = [
        [1, "1. Welcome & Link Tests", 1],
        [2, "1.1 Clickable Links", 1],
        [2, "1.2 Search & Sidebar", 1],
        [1, "2. Keyboard Reference & Shortcuts", 2],
        [1, "3. Drawing Sandbox Page", 3]
    ]
    doc.set_toc(toc)
    
    doc.save("test.pdf")
    doc.close()
    print("Successfully generated test.pdf with outline, internal links, and reference manual.")

if __name__ == "__main__":
    create_pdf()
