import os
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
        
        file_menu.addSeparator()
        save_file = file_menu.addAction("Save File")
        save_file.setShortcut("Ctrl+S")
        save_file.triggered.connect(self.save_file)
        
        save_as = file_menu.addAction("Save As")
        save_as.setShortcut("Ctrl+Shift+s")
        save_as.triggered.connect(self.save_as)

        #EditMenu
        edit_menu = menu_bar.addMenu("Edit")
    
        copy_action = edit_menu.addAction("Copy")
        copy_action.setShortcut("Ctrl+C")
        copy_action.triggered.connect(self.copy)
    
        paste_action = edit_menu.addAction("Paste")
        paste_action.setShortcut("Ctrl+V")
        paste_action.triggered.connect(self.paste)
    

    def get_editor(self) -> QsciScintilla:
        
        #instance
        editor = QsciScintilla()
        #encoding
        editor.setUtf8(True)
        #Font
        editor.setFont(self.code_font)

        #EOL, Lexer добавить???
        
        return editor
    
    def is_binary (self, path):
        #Checking if file is binary - that cannot be opened in text editor
        with open (path, 'rb') as f:
            return b'\0' in f.read(1024)
    
    def set_new_tab(self, path: Path, is_new_file = False):
        editor = self.get_editor()
        if is_new_file:
            self.tab_view.addTab(editor, "untitled")
            self.setWindowTitle("Untitled")
            self.tab_view.setCurrentIndex(self.tab_view.count() -1)
            self.current_file = None
            return
        
        if not path.is_file():
            return
        if self.is_binary(path):
            self.statusBar().showMessage("Binary file!", 2000)
            return
        
        #проверка, открыт ли файл в одной из вкладок
        for i in range (self.tab_view.count()):
            if self.tab_view.tabText(i) == path.name:
               self.tab_view.setCurrentIndex(i)
               self.current_file = path # удалить эту строку? дублируется чуть ниже?
               return
                
        self.tab_view.addTab(editor,path.name)
        editor.setText(path.read_text(encoding="utf-8"))
        self.setWindowTitle(path.name)
        self.current_file = path 
        self.tab_view.setCurrentIndex(self.tab_view.count()-1)
        self.statusBar().showMessage(f"Opened {path.name}", 2000)
            

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
        
        #Tab Widget
        self.tab_view = QTabWidget()    
        self.tab_view.setContentsMargins(0,0,0,0)
        self.tab_view.setTabsClosable(True)
        self.tab_view.setMovable(True)
        self.tab_view.setDocumentMode(True)
        
        # split view
        self.hsplit = QSplitter(Qt.Horizontal)
        body.addWidget(self.hsplit)
        body_frame.setLayout(body)
        self.setCentralWidget(body_frame)
        self.hsplit.addWidget(self.tab_view)
        
    def new_file(self):
        self.set_new_tab(None, is_new_file=True)
        
    def open_file(self):
        ops = QFileDialog.Options()
        ops = QFileDialog.DontUseNativeDialog
        new_file, _ = QFileDialog.getOpenFileName(self, "Выберите файл", "", "Все файлы (*);;HTML файлы (*.html)", options=ops)
        if new_file == '':
            self.statusBar().showMessage("Отмена", 2000)
            return
        f =  Path(new_file)   
        self.set_new_tab(f)
            
    def save_file(self):
        if self.current_file is None and self.tab_view.count() > 0:
            self.save_as()
        
        editor = self.tab_view.currentWidget()
        self.current_file.write_text(editor.text())
        self.statusBar().showMessage(f"{self.current_file.name}", 2000)
        
    def save_as(self):
        editor = self.tab_view.currentWidget()
        if editor is None:
            return
        file_path = QFileDialog.getSaveFileName(self,"Save As", os.getcwd()) [0]
        if file_path == '':
            self.statusBar().showMessage("Отмена", 2000)
            return
        path = Path(file_path)
        path.write_text(editor.text())
        self.tav_view.setTabText(self.tab_view.currentIndex(),path.name)
        self.statusBar().showMessage(f"Сохранено: {path.name}", 2000)
        self.current_file = path
        
    def copy(self):
        editor = self.tab_view.setCurrentWidget()
        if editor is not None:
            editor.Copy()
        
    def paste(self):
        ...
        
if __name__ == '__main__':
    app = QApplication ([])
    window = MainWindow()
    sys.exit(app.exec())