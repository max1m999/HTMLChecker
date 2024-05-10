from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.Qsci import *
from PyQt5.QtGui import *

from pathlib import Path

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from main import MainWindow

class Editor(QsciScintilla):
    def __init__(self, main_window,path: Path = None, parent = None):
        super(Editor, self).__init__(parent)
        
        self.main_window: MainWindow = main_window
        self._current_file_changed = False
        self.first_launch = True
        self.textChanged.connect(self._textChanged)
        self.path = path
        
        # Кодировка
        self.setUtf8(True)
        # Шрифт
        self.code_font = QFont("Consolas")
        self.code_font.setPointSize(16)
        
        self.setFont(self.code_font)
        
        self.setWrapMode(3)
        
        #Стиль
        
        self.setPaper(QColor("#282c34"))
        self.setColor(QColor("#bbc1ca"))

        #EOL
        self.setEolMode(QsciScintilla.EolWindows)
        self.setEolVisibility(False)
        
        # caret
        self.setCaretForegroundColor(QColor("#dedcdc"))
        self.setCaretLineVisible(True)
        self.setCaretWidth(2)
        self.setCaretLineBackgroundColor(QColor("#4d4d4d"))
        
        # Нумерация строк
        self.setMarginType(50, QsciScintilla.NumberMargin)
        self.setMarginWidth(0, f"{self.lines()*10}" ) # sum(1 for line in fp)
        self.setMarginsForegroundColor(QColor("#ff888888"))
        self.setMarginsBackgroundColor(QColor("#282c34"))
        self.setMarginsFont(self.code_font)
    
    @property #????
    def current_file_changed(self):
        return self._current_file_changed
    
    @current_file_changed.setter
    def current_file_changed(self, value: bool):
        curr_index = self.main_window.tab_view.currentIndex()
        if value:
            self.main_window.tab_view.setTabText(curr_index, "*"+self.path.name)
            self.main_window.setWindowTitle(f"*{self.path.name}")
        else:
            if self.main_window.tab_view.tabText(curr_index).startswith("*"):
                self.main_window.tab_view.setTabText(curr_index, self.main_window.tab_view.tabText(curr_index)[1:])
                self.main_window.setWindowTitle(self.main_window.windowTitle()[1:])
        
        self._current_file_changed = value
    
    def _textChanged(self):
        if not self.current_file_changed and not self.first_launch:
            self.current_file_changed = True
        if self. first_launch:
            self.first_launch = False