import sys
import os
from PyQt6.QtWidgets import QApplication
from app.main_window import MainWindow

def main():
    # Allow high DPI scaling for crisp rendering on high DPI monitors (like Ubuntu 4K displays)
    app = QApplication(sys.argv)
    app.setApplicationName("Slate")
    app.setDesktopFileName("slate")
    
    window = MainWindow()
    window.show()
    
    # Check if a file argument was passed on command line
    if len(sys.argv) > 1:
        file_arg = sys.argv[1]
        if os.path.exists(file_arg) and file_arg.lower().endswith('.pdf'):
            # Convert to absolute path to avoid issues
            abs_path = os.path.abspath(file_arg)
            window.open_file_path(abs_path)
        else:
            print(f"Warning: File not found or not a PDF: {file_arg}")
            
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
