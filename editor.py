from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.Qsci import *
from PyQt5.QtGui import *
from pathlib import Path
from fuzzywuzzy import fuzz

import re

import keyword
import pkgutil

from typing import TYPE_CHECKING #??????????

if TYPE_CHECKING: #?????????????????
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
        
        self.line = []
        self.index = []
        
        self.tagList = []
        self.tagPoz = []
        
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
        
        # автозавершение слов
        self.setAutoCompletionSource(QsciScintilla.AcsAll) 
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
            
    def set_error_pos(self,item):
        ind = self.main_window.errors.row(item) - 2
        if ind >= 0: 
            self.setCursorPosition(self.line[ind]-1,self.index[ind])
            self.setFocus()  
        
    def LineNumber (self):
        self.setMarginWidth(0, f"{self.lines() * 10}" )
    
    # АНАЛИЗ ФАЙЛА
    def start_analysis(self):
        errors = []
        self.line = []
        self.index = []
        
        # опечатки в тегах
        errors = self.tags_spell(errors)
        
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
            self.main_window.errors.addItem("Нажмите на сообщение в консоли, чтобы перейти к месту ошибки:")
            for i in errors:
                # вывод ошибок в консоль
                self.main_window.errors.addItem(f"{i}")
                self.line.append(int((f"{i}".split(":")[-2]).split(",")[-2]))
                self.index.append(int(f"{i}".split(":")[-1]))
            self.main_window.errors.itemClicked.connect(self.set_error_pos)
        if not errors: self.main_window.errors.addItem("Проверка завершена. Ошибки в разметке не найдены")
        
    #   ВОССТАНОВЛЕНИЕ ФАЙЛА
    def start_fixing(self):
        str = ""
        list = "<[{()}]>'\""
        for i in self.text():
            if i in list:
                str += i
        self.setText(str)
        
    def tags_spell(self, errors):
        ind = 0
        index = 0
        line = 1
        max_percent = -1
        current_tag = ""
        tok_str = self.text().split(">")
        while tok_str.__len__() > index:
            match = re.search(r'<\s*(\w+)', tok_str[index],re.IGNORECASE)
            match_end = re.search(r'</(\w+)', tok_str[index],re.IGNORECASE)
            match_complex = re.search(r'<(!+-{1,2})(\s*\w*\s*)*(-{1,2})|<(!+[A-Za-z]+)\s*([A-Za-z]+)', tok_str[index],re.IGNORECASE)
            for x in tok_str[index]:
                if x == "\n":                 
                    ind = 0
                    line += 1
            ind += len(tok_str[index]) -1 
            if match_end:
                str = match_end.group(1)
                for x in self.main_window.tags_table:
                    if fuzz.ratio(str.lower(), f"{x['tag']}".lower()) > max_percent:
                        max_percent = fuzz.ratio(str.lower(), f"{x['tag']}".lower())
                        current_tag = f"{x['tag']}".lower()
                    if max_percent == 100:
                        print("</" + f"{current_tag}" +">")
                        break
            elif match_complex:
                if match_complex.group(1):  # если найдено совпадение <!-- -->
                    str = match_complex.group(1) + " " + match_complex.group(3)
                elif match_complex.group(4):  # если найдено совпадение <!doctype html>
                    str = match_complex.group(4) + " " + match_complex.group(5)
                for x in self.main_window.tags_table:
                    if fuzz.ratio(str.lower(), f"{x['tag']}".lower()) > max_percent:
                        max_percent = fuzz.ratio(str.lower(), f"{x['tag']}".lower())
                        current_tag = f"{x['tag']}".lower()
                    if max_percent == 100:
                        print("<" + f"{current_tag}" +">")
                        break  
            elif match:
                str = match.group(1)
                for x in self.main_window.tags_table:
                    if fuzz.ratio(str.lower(), f"{x['tag']}".lower()) > max_percent:
                        max_percent = fuzz.ratio(str.lower(), f"{x['tag']}".lower())
                        current_tag = f"{x['tag']}".lower()
                    if max_percent == 100:
                        print("<" + f"{current_tag}" +">")
                        break      
            if max_percent != -1 and max_percent < 100: 
                errors.append(f"Ошибка в имени тега {current_tag}, строка: {line}, индекс: {ind}")
                print (f"debug : line {tok_str[index]} ; str  {str}")
            self.tagList.append(current_tag)
            self.tagPoz.append((line,ind))
            index += 1
            max_percent = -1
            current_tag = ""
        return errors    
    
    def brackets_matching(self, errors):
        stack = []
        poz = []
        lineP = []
        index = 0
        symbol = 0
        line = 1
        op_list = "({[<'\""
        cl_list = ")}]>'\""
        for i in self.text():
            if i in op_list and not (stack and i == stack[-1] and stack[-1] in ["'",'"',"<"]):
                stack.append(i)
                poz.append(index)
                lineP.append(line)
            elif stack and i == stack[-1] and stack[-1] == "<":
                errors.append(f"Отсутствует парный символ для {stack[-1]}, строка: {lineP[-1]}, индекс: {int(poz[-1])}")
                stack.pop()
                poz.pop()
                lineP.pop()
                stack.append(i)
                poz.append(index)
                lineP.append(line)
            elif i in cl_list:
                pos = cl_list.index(i)
                if stack:
                    if op_list[pos] != stack[-1]:
                        errors.append(f"Отсутствует парный символ для {i}, строка: {line}, индекс: {index}") 
                        errors.append(f"Отсутствует парный символ для {stack[-1]}, строка: {lineP[-1]},  индекс: {poz[-1]}")  
                        stack.pop()
                        poz.pop()
                        lineP.pop()                
                        stack.append(i)
                        poz.append(index)
                        lineP.append(line)
                    stack.pop()
                    poz.pop()
                    lineP.pop() 
                else:
                    errors.append(f"Отсутствует парный символ для {i}, строка: {line}, индекс: {index}") 
            elif i == "\n": 
                line +=1
                index = -1
            index +=1
            symbol += 1
        if stack:
            errors.append(f"Отсутствует парный символ для {stack[-1]}, строка: {lineP[-1]}, индекс: {int(poz[-1])}") 
            stack.pop()
            poz.pop()
            lineP.pop()
        return errors
    
    def wspaces(self, errors):
        stack = []
        index = 0
        poz = -2
        line = 1
        for i in self.text():
            if i == "<":
                stack.append(i)
                poz = index
            elif index == poz+1:
                if i == "\n":
                    errors.append(f"Пробел после символа <, строка: {line}, индекс: {int(poz)}")
                    line += 1
                    index = -1
                elif stack and (i ==" " or i == "\r") :
                    errors.append(f"Пробел после символа <, строка: {line}, индекс: {int(poz)}")
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