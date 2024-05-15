from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.Qsci import *
from PyQt5.QtGui import *
from pathlib import Path

import keyword
import pkgutil

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
        self.linesChanged.connect(self.LineNumber)
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
        self.setEolMode(QsciScintilla.EolUnix)
        self.setEolVisibility(False)
        
        # автозавершение слов
        self.setAutoCompletionSource(QsciScintilla.AcsAll) #подключить бд
        self.setAutoCompletionThreshold(1)
        self.setAutoCompletionCaseSensitivity(False)
        self.setAutoCompletionUseSingle(QsciScintilla.AcusNever)
                            
        # caret
        self.setCaretForegroundColor(QColor("#dedcdc"))
        self.setCaretLineVisible(True)
        self.setCaretWidth(2)
        self.setCaretLineBackgroundColor(QColor("#4d4d4d"))
        
        # Нумерация строк
        self.setMarginType(0, QsciScintilla.NumberMargin)
        self.setMarginWidth(0, f"{self.lines() * 10}" )
        self.setMarginsForegroundColor(QColor("#ff888888"))
        self.setMarginsBackgroundColor(QColor("#282c34"))
        self.setMarginsFont(self.code_font)
            
    def error_list_clicked(self):
        self.setCursorPosition()
        self.setFocus()  
        
    def LineNumber (self):
        self.setMarginWidth(0, f"{self.lines() * 10}" )
    
    # АНАЛИЗ ФАЙЛА
    def start_analysis(self):
        errors = []
        # парные символы
        errors = self.brackets_matching(errors)
                
        # пробелы после <
        errors = self.wspaces(errors)
        
        if "*" in self.main_window.tab_view.tabText(self.main_window.tab_view.currentIndex()):
            name = f"{self.main_window.tab_view.tabText(self.main_window.tab_view.currentIndex()) [1:]}"
        else: 
            name = f"{self.main_window.tab_view.tabText(self.main_window.tab_view.currentIndex())}"
        
        self.main_window.errors.addItem (f"Анализ файла {name}...")
        if errors: 
            for i in errors:
                # вывод ошибок в консоль
                self.main_window.errors.addItem(f"{i}")
        if not errors: self.main_window.errors.addItem("Проверка завершена. Ошибки в разметке не найдены")
        else: self.main_window.errors.itemClicked.connect(self.error_list_clicked)
        
    
    def brackets_matching(self, errors):
        stack = []
        poz = []
        index = 0
        op_list = "({[<'\""
        cl_list = ")}]>'\""
        for i in self.text():
            if i in op_list and not (stack and i == stack[-1]):
                stack.append(i)
                poz.append(index)
            elif i in op_list and stack[-1] != "'" and stack[-1] != '"':
                errors.append(f"Отсутствует парный символ для {stack[-1]}, строка {self.SendScintilla(QsciScintilla.SCI_LINEFROMPOSITION, int(poz[-1])) + 1}, индекс: {self.SendScintilla(QsciScintilla.SCI_GETCOLUMN, int(poz[-1]))}")
                stack.pop()
                poz.pop()
                stack.append(i)
                poz.append(index)
            elif i in cl_list:
                pos = cl_list.index(i)
                if stack:
                    if op_list[pos] != stack[-1]:
                        errors.append(f"Отсутствует парный символ для {i}, строка {self.SendScintilla(QsciScintilla.SCI_LINEFROMPOSITION, int(index)) + 1}, индекс: {self.SendScintilla(QsciScintilla.SCI_GETCOLUMN, int(index))}") 
                        errors.append(f"Отсутствует парный символ для {stack[-1]},строка {self.SendScintilla(QsciScintilla.SCI_LINEFROMPOSITION, int(poz[-1])) + 1},  индекс: {self.SendScintilla(QsciScintilla.SCI_GETCOLUMN, int(poz[-1]))}")  
                        stack.pop()
                        poz.pop()                
                        stack.append(i)
                        poz.append(index)
                    stack.pop()
                    poz.pop() 
                else:
                    errors.append(f"Отсутствует парный символ для {i}, строка {self.SendScintilla(QsciScintilla.SCI_LINEFROMPOSITION, int(index)) + 1}, индекс: {self.SendScintilla(QsciScintilla.SCI_GETCOLUMN, int(index))}") 
            index += 1
        if stack:
            errors.append(f"Отсутствует парный символ для {stack[-1]},строка {self.SendScintilla(QsciScintilla.SCI_LINEFROMPOSITION, int(poz[-1])) + 1}, индекс: {self.SendScintilla(QsciScintilla.SCI_GETCOLUMN, int(poz[-1]))}") 
            stack.pop()
            poz.pop()
        return errors
    
    def wspaces(self, errors):
        stack = []
        index = 0
        poz = -2
        for i in self.text():
            if i == "<":
                stack.append(i)
                poz = index
            elif index == poz+1:
                if stack and (i ==" " or i == "\r" or i == "\n") :
                    errors.append(f"Пробел после символа <, строка {self.SendScintilla(QsciScintilla.SCI_LINEFROMPOSITION, int(poz)) + 1}, индекс: {self.SendScintilla(QsciScintilla.SCI_GETCOLUMN, int(poz))}")
                stack.pop() 
            index += 1    
        return errors
    
    @property
    def current_file_changed(self):
        return self._current_file_changed
    
    @current_file_changed.setter
    def current_file_changed(self, value: bool):
        curr_index = self.main_window.tab_view.currentIndex()
        if value:
            self.main_window.tab_view.setTabText(curr_index, "*"+f"{self.path}")
        else:
            if self.main_window.tab_view.tabText(curr_index).startswith("*"):
                self.main_window.tab_view.setTabText(curr_index, self.main_window.tab_view.tabText(curr_index)[1:])
        
        self._current_file_changed = value
    
    def _textChanged(self):
        if not self.current_file_changed and not self.first_launch:
            self.current_file_changed = True
        if self. first_launch:
            self.first_launch = False