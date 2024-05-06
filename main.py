from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.Qsci import *
from PyQt5.QtGui import *
import sys
from pathlib import Path

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.init_ui()
        self.current_file = None
        
    def init_ui(self):
        self.app_name = "HTML CHECKER"
        self.setWindowTitle(self.app_name)
        self.resize(1300,900)
        self.setStyleSheet(open ("./css/style.qss", "r").read())
        
        #Fonts
        self.window_font = QFont("Fire code")
        self.window_font.setPointSize(16)
        self.setFont(self.window_font)
        
        self.code_font = QFont("Consolas")
        self.code_font.setPointSize(16)
        self.setFont(self.code_font)
        
        self.set_up_menu()
        self.set_up_body()
        
        self.show()
        
    def set_up_menu(self):
        menu_bar = self.menuBar()
    
        #FileMenu
        file_menu = menu_bar.addMenu("File")
    
        new_file = file_menu.addAction("New")
        new_file.setShortcut("Ctrl+N")
        new_file.triggered.connect(self.new_file)
    
        open_file = file_menu.addAction("Open File")
        open_file.setShortcut("Ctrl+O")
        open_file.triggered.connect(self.open_file)

        #EditMenu
        edit_menu = menu_bar.addMenu("Edit")
    
        copy_action = edit_menu.addAction("Copy")
        copy_action.setShortcut("Ctrl+C")
        copy_action.triggered.connect(self.copy)
    
        paste_action = edit_menu.addAction("Paste")
        paste_action.setShortcut("Ctrl+V")
        paste_action.triggered.connect(self.paste)
    
    def new_file(self):
        ...
        
    def open_file(self):
        ...
        
    def copy(self):
        ...
        
    def paste(self):
        ...

    def get_editor(self) -> QsciScintilla:
        
        #instance
        editor = QsciScintilla()
        #encoding
        editor.setUtf8(True)
        #Font
        editor.setFont(self.code_font)

        #EOL, Lexer добавить???
        
        return editor

    def set_up_body(self):
        #Body
        body_frame = QFrame()
        body_frame.setFrameShape(QFrame.NoFrame)
        body_frame.setFrameShadow(QFrame.Plain)
        body_frame.setLineWidth(0)
        body_frame.setMidLineWidth(0)
        body_frame.setContentsMargins(0,0,0,0)
        body_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        body = QHBoxLayout()
        body.setContentsMargins(0,0,0,0)
        body.setSpacing(0)
        body_frame.setLayout(body)
        
        

if __name__ == '__main__':
    app = QApplication ([])
    window = MainWindow()
    sys.exit(app.exec())