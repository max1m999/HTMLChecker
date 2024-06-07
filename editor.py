from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.Qsci import *
from PyQt5.QtGui import *
from pathlib import Path
from fuzzywuzzy import fuzz

import re

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
        
        self.errors = []
        
        self.line = []
        self.index = []
        self.tagLength = []
        self.possiblePlaces = []
        
        self.tagList = []
        self.tagStart = []
        self.tagEnd = []
        self.tagIgnore = []
        
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
        
    def LineNumber (self):
        self.setMarginWidth(0, f"{self.lines() * 10}" )
    
    # АНАЛИЗ ФАЙЛА
    def start_analysis(self):
        self.errors = []
        self.line = []
        self.index = []
        self.tagLength = []
        self.tagList = []
        self.tagStart = []
        self.tagEnd = []
        self.tagIgnore = []
        self.possiblePlaces = []
        
        # опечатки в тегах
        self.tags_spell()
        print(self.tagList) # delete
        print(self.tagStart) # delete
        print(self.tagEnd) # delete
        
        # непроверяемый текст
        self.skip_Text()
        
        # парные символы
        self.brackets_matching()
        
        # пробелы после <
        self.wspaces()
        if not self.errors:
            # наличие необходимых тегов
            self.tags_presence()
            
            # порядок тегов
            self.tags_order()
            
            # наличие пар тегов
            self.tags_pair()
                       
        if "*" in self.main_window.tab_view.tabText(self.main_window.tab_view.currentIndex()):
            name = f"{self.main_window.tab_view.tabText(self.main_window.tab_view.currentIndex()) [1:]}"
        else: 
            name = f"{self.main_window.tab_view.tabText(self.main_window.tab_view.currentIndex())}"
        
        self.main_window.errors.addItem (f"Анализ файла {name}...")
        if self.errors: 
            self.main_window.errors.addItem("Нажмите на сообщение в консоли, чтобы перейти к месту ошибки:")
            for i in self.errors:
                if not (f"{i}".__contains__("Отсутствует тег") or f"{i}".__contains__("Отсутствует обязательный тег") or f"{i}".__contains__("Некорректное") or f"{i}".__contains__("Debug") or f"{i}".__contains__("Вставьте")):
                    self.line.append(int((f"{i}".split(":")[-2]).split(",")[-2]))
                    self.index.append(int(f"{i}".split(":")[-1])) 
                    print("errors lines: " + f"{self.line}") # delete
                else:
                    self.line.append(-1)
                    self.index.append(-1)
                # вывод ошибок в консоль
                self.main_window.errors.addItem(f"{i}")
            try: self.main_window.errors.itemClicked.disconnect()
            except Exception: pass
            self.main_window.errors.itemClicked.connect(self.set_error_pos)
        if not self.errors: self.main_window.errors.addItem("Проверка завершена. Ошибки в разметке не найдены")
        
    def set_error_pos(self,item):
        ind = self.main_window.errors.row(item) - 2
        if ind >= 0: 
            if self.line[ind] > -1:
                self.setCursorPosition(self.line[ind]-1,self.index[ind])
                self.setFocus()  
        
    # ВОССТАНОВЛЕНИЕ ФАЙЛА
    def start_fixing(self):
        if self.errors.__len__() > 0:
            str = f"{self.errors[0]}"
            match True:
                case _ if "Ошибка в имени тега" in f"{str}": # spell
                    tagFixInd = int(self.tagStart.index((self.line[0],self.index[0])))
                    length = int(self.tagLength[tagFixInd])
                    name = self.tagList[tagFixInd]
                    self.fix_name (self.line[0], self.index[0], length, name)
                case _ if "Отсутствует тег" in f"{str}":  # pair
                    pass
                case _ if "Некорректное расположение тега" in f"{str}": # structure
                    pass
                case _ if "Отсутствует обязательный тег" in f"{str}": # <html> missing
                    pass
                case _ if "Отсутствует парный символ" in f"{str}": # <>
                    symbol =  str.split()[4].split(",")[0]
                    fix_line = self.line[0]
                    fix_index = self.index[0]
                    self.line = []
                    self.index = []
                    self.errors = []
                    self.errors.append(f"Отсутствует парный символ для {symbol}")
                    self.errors.append(f"Вставьте парный символ для {symbol} в одну из предложенных позиций:")
                    self.main_window.errors.addItem(f"Отсутствует парный символ для {symbol}")
                    self.main_window.errors.addItem(f"Вставьте парный символ для {symbol} в одну из предложенных позиций:")
                    self.fix_symbol_pair(fix_line, fix_index, symbol)
                case _ if "Пробел после символа" in f"{str}": # <_abc...
                    self.fix_whitespace(self.line[0], self.index[0])    
            #self.start_analysis()
            
    def fix_symbol_pair (self, line, index, symbol):
        op_list = "({[<'\""
        cl_list = ")}]>'\""
        pair = ""
        str = self.text()
        lin = 1
        ind = 0
        num_symbol = 0
        twin_num = -1
        
        if symbol in op_list:
            pair = cl_list[op_list.index(f"{symbol}")]
        elif symbol in cl_list:
            pair = op_list[cl_list.index(f"{symbol}")]
        for s in str:
            if lin != line or ind != index:
                if s == "\n":
                    lin += 1
                    ind = -1
                num_symbol += 1
                ind += 1
            else: 
                break
        tmp_symbol = num_symbol
        lin = line
        ind = index + 1
        if symbol in op_list: #OPEN SYMBOL
            for s in str[num_symbol+1:]:
                if s == "\n":
                    lin += 1
                    ind = -1
                elif s == f"{symbol}":
                    twin_num = tmp_symbol
                    break
                tmp_symbol += 1
                ind += 1
            tmp_symbol = num_symbol
            lin = line
            ind = index + 1
            if twin_num == -1:
                twin_num = len(str) - 1
            for s in str[num_symbol+1:twin_num+1]:
                if s == "\n":
                    self.errors.append(f"Возможное место для символа {pair} : строка: {lin}, индекс: {ind}")
                    self.line.append(lin)
                    self.index.append(ind) 
                    self.main_window.errors.addItem(f"Возможное место для символа {pair} : строка: {lin}, индекс: {ind}")
                    lin += 1
                    ind = -1
                elif s == ' ' or s == "\t" or s == f"{symbol}":
                    self.errors.append(f"Возможное место для символа {pair} : строка: {lin}, индекс: {ind}")
                    self.line.append(lin)
                    self.index.append(ind) 
                    self.main_window.errors.addItem(f"Возможное место для символа {pair} : строка: {lin}, индекс: {ind}")
                elif tmp_symbol == twin_num - 1:
                    self.errors.append(f"Возможное место для символа {pair} : строка: {lin}, индекс: {ind + 1}")
                    self.line.append(lin)
                    self.index.append(ind + 1) 
                    self.main_window.errors.addItem(f"Возможное место для символа {pair} : строка: {lin}, индекс: {ind + 1}")
                tmp_symbol += 1
                ind += 1
        elif symbol in cl_list: #CLOSE SYMBOL
            ind -=1
            for s in reversed(str[:num_symbol]):
                if s == "\n":
                    lin -= 1
                    ind = -1 #???
                elif s == f"{symbol}":
                    twin_num = tmp_symbol
                    break
                tmp_symbol -= 1
                ind -= 1
            tmp_symbol = num_symbol
            lin = line
            ind = index - 1
            if twin_num == -1:
                twin_num = 1
            for s in str[twin_num-1:num_symbol+1]:
                if s == "\n":
                    self.errors.append(f"Возможное место для символа {pair} : строка: {lin}, индекс: {ind}")
                    self.line.append(lin)
                    self.index.append(ind) 
                    self.main_window.errors.addItem(f"Возможное место для символа {pair} : строка: {lin}, индекс: {ind}")
                    lin += 1
                    ind = -1 
                elif s == ' ' or s == "\t" or s == f"{symbol}":
                    self.errors.append(f"Возможное место для символа {pair} : строка: {lin}, индекс: {ind}")
                    self.line.append(lin)
                    self.index.append(ind) 
                    self.main_window.errors.addItem(f"Возможное место для символа {pair} : строка: {lin}, индекс: {ind}")
                elif tmp_symbol == twin_num - 1:
                    self.errors.append(f"Возможное место для символа {pair} : строка: {lin}, индекс: {ind}")
                    self.line.append(lin)
                    self.index.append(ind - 1) 
                    self.main_window.errors.addItem(f"Возможное место для символа {pair} : строка: {lin}, индекс: {ind}")
                tmp_symbol += 1
                ind += 1                
            
    def fix_name (self, line, index, length, name):
        str = self.text()
        lin = 1
        ind = 0
        symbol = 0
        for s in str:
            if lin != line or ind != index:
                if s == "\n":
                    lin += 1
                    ind = -1
                symbol += 1
                ind += 1
            else: 
                break
        fixed_str = str[:symbol+1] + name + str[symbol+length+1:]
        self.setText(fixed_str)
    
    def fix_whitespace (self, line, index):
        str = self.text()
        lin = 1
        ind = 0
        symbol = 0
        for s in str:
            if lin != line or ind != index:
                if s == "\n":
                    lin += 1
                    ind = -1
                symbol += 1
                ind += 1
            else: break
        fixed_str = str[:symbol+1] + str[symbol+2:]
        self.setText(fixed_str)
    
    def skip_Text (self):
        symbol = 0
        ind = 0
        line = 1
        str = self.text()
        for i in self.tagList:
            if f"{i}".__contains__("/"):
                if next(item for item in self.main_window.tags_table if f"{item['tag']}".lower() == f"{i}"[1:].lower())['ignore'] == '1':
                    self.tagIgnore.append(self.tagEnd[ind])
                    print("I: /") # delete
                    print(i) # delete
            elif next(item for item in self.main_window.tags_table if f"{item['tag']}".lower() == f"{i}".lower())['ignore'] == '1':
               self.tagIgnore.append(self.tagStart[ind])
               print("I: ") # delete
               print(i) # delete
            ind += 1
        print("ORIGINAL: ") # delete
        print(self.tagIgnore) # delete
        print("-----") # delete
        ind = 0
        index = 0
        for i in self.tagIgnore:
            for s in str:
                if line != int(self.tagIgnore[index][0]) or ind != int(self.tagIgnore[index][1]):
                    if s == "\n":
                        line += 1
                        ind = -1
                    symbol += 1
                    ind += 1
                else: break
            self.tagIgnore[index] = symbol
            str = self.text()[symbol:]
            index += 1
        print("ignore count: " + f"{self.tagIgnore.__len__()}") # delete
        print("ignore : " + f"{self.tagIgnore}") # delete
        
    def tags_spell(self):
        str = ""
        ind = 0
        index = 0
        line = 1
        max_percent = -1
        current_tag = ""
        tok_str = self.text().split(">")
        while tok_str.__len__() > index:
            match = re.search(r'<\s*(\w+)', tok_str[index],re.IGNORECASE)
            match_end = re.search(r'</(\w+)', tok_str[index],re.IGNORECASE)
            match_complex = re.search(r'<(!+-{1,2})(\s*[()]*/*\w*\s*)*(-{1,2})|<(!+[A-Za-z]+)\s*([A-Za-z]+)', tok_str[index],re.IGNORECASE)
            for x in tok_str[index]:
                if x == "\n":                 
                    ind = 0
                    line += 1
                elif x == "<":
                    break
                else: ind +=1
            if match_end:
                str = match_end.group(1)
                for x in self.main_window.tags_table:
                    if fuzz.ratio(str.lower(), f"{x['tag']}".lower()) > max_percent:
                        max_percent = fuzz.ratio(str.lower(), f"{x['tag']}".lower())
                        current_tag = f"{x['tag']}".lower()
                    if max_percent == 100:
                        print("</" + f"{current_tag}" +">") # delete
                        break
                current_tag = "/" + f"{current_tag}"
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
                        print("<" + f"{current_tag}" +">") # delete
                        break  
            elif match:
                str = match.group(1)
                for x in self.main_window.tags_table:
                    if fuzz.ratio(str.lower(), f"{x['tag']}".lower()) > max_percent:
                        max_percent = fuzz.ratio(str.lower(), f"{x['tag']}".lower())
                        current_tag = f"{x['tag']}".lower()
                    if max_percent == 100:
                        print("<" + f"{current_tag}" +">") # delete
                        break  
            self.tagLength.append(len(str))
            if max_percent > 60:
                self.tagList.append(current_tag)
                self.tagStart.append((line,ind))
              #  self.errors.append(f"Debug {current_tag}, строка: {line}, индекс: {ind}") # delete
                if max_percent < 100: 
                    self.errors.append(f"Ошибка в имени тега {current_tag}, строка: {line}, индекс: {ind}")
                    self.errors.append(f"Debug {tok_str[index]}, строка: {line}, индекс: {ind}") # delete
            for x in tok_str[index][tok_str[index].find("<"):]:
                if x == "\n":                 
                    ind = 0
                    line += 1
                else: ind +=1
            ind += 1
            if max_percent > 60: self.tagEnd.append((line,ind))
            index += 1
            max_percent = -1
            current_tag = ""
    
    def tags_presence(self):
        for x in self.main_window.tags_table:
            if x['necessary'] == '1':
                if self.tagList.__contains__(f"{x['tag']}".lower()) == False:
                    self.errors.append(f"Отсутствует обязательный тег {x['tag']}")                
    
    def tags_order(self):
        if self.tagList.__contains__('!doctype html') and self.tagList[0] != '!doctype html':
            self.errors.append("Некорректное расположение тега <!doctype html>")
        if self.tagList.__contains__('html') and self.tagList[1] != 'html':
            self.errors.append("Некорректное расположение тега <html>")
        if self.tagList.__contains__('head'):
            if self.tagList[2] != 'head':
                self.errors.append("Некорректное расположение тега <head>")
            if self.tagList.__contains__('/head'):
                if self.tagList.__contains__('meta') and not (self.tagList.index('head') < self.tagList.index('meta') and self.tagList.index('meta') < self.tagList.index('/head')):
                    self.errors.append("Некорректное расположение тега <meta>")
                if self.tagList.__contains__('title') and not (self.tagList.index('head') < self.tagList.index('title') and self.tagList.index('title') < self.tagList.index('/head')):
                    self.errors.append("Некорректное расположение тега <title>")    
                if self.tagList.__contains__('body') and not (self.tagList.index('/head') < self.tagList.index('body')):
                    self.errors.append("Некорректное расположение тега <body>")            
    
    def tags_pair(self):
        stack = []
        cl_stack = []
        ind = 0
        for i in self.tagList:
            if f"{i}".__contains__("/"):
                cl_stack.append(i)
                print("cl: " + f"{cl_stack}") # delete
            elif next(item for item in self.main_window.tags_table if f"{item['tag']}".lower() == f"{i}".lower())['paired'] == '1':
                stack.append(i)
            print(stack) # delete
        while ind < len(stack):
            if cl_stack.__contains__("/"+f"{stack[ind]}"):
                cl_stack.pop(cl_stack.index("/"+f"{stack[ind]}"))
                stack.pop(ind)
            else: ind +=1  
        print (stack)  # delete 
        print (cl_stack)  # delete 
        while stack:
            self.errors.append(f"Отсутствует тег </{stack[-1]}>")
            stack.pop()
        while cl_stack:
            self.errors.append(f"Отсутствует тег <{cl_stack[-1][1:]}>")
            cl_stack.pop()
    
    def brackets_matching(self):
        stack = []
        poz = []
        lineP = []
        index = 0
        symbol = 0
        line = 1
        op_list = "({[<'\""
        cl_list = ")}]>'\""
        for i in self.text():
            if self.tagIgnore.__len__() < 2 or self.tagIgnore.__len__() > 1 and not (self.tagIgnore[0] <= symbol <= self.tagIgnore[1]):
                if i in op_list and not (stack and i == stack[-1] and stack[-1] in ["'",'"',"<"]):
                    stack.append(i)
                    poz.append(index)
                    lineP.append(line)
                elif stack and i == stack[-1] and stack[-1] == "<":
                    self.errors.append(f"Отсутствует парный символ для {stack[-1]}, строка: {lineP[-1]}, индекс: {int(poz[-1])}")
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
                            self.errors.append(f"Отсутствует парный символ для {i}, строка: {line}, индекс: {index}") 
                            self.errors.append(f"Отсутствует парный символ для {stack[-1]}, строка: {lineP[-1]},  индекс: {poz[-1]}")  
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
                        self.errors.append(f"Отсутствует парный символ для {i}, строка: {line}, индекс: {index}") 
            if i == "\n": 
                line +=1
                index = -1
            index +=1
            if self.tagIgnore.__len__() > 1 and symbol == self.tagIgnore[1]:
                self.tagIgnore.pop(0)
                if self.tagIgnore:
                    self.tagIgnore.pop(0)
            symbol += 1
        print("symbol: " + f"{symbol}") # delete
        while stack:
            self.errors.append(f"Отсутствует парный символ для {stack[-1]}, строка: {lineP[-1]}, индекс: {int(poz[-1])}") 
            stack.pop()
            poz.pop()
            lineP.pop()
    
    def wspaces(self):
        stack = []
        index = 0
        poz = -20
        line = 1
        for i in self.text():
            if i == "<":
                stack.append(i)
                poz = index
            elif index == poz+1:
                if i == "\n":
                    self.errors.append(f"Пробел после символа <, строка: {line}, индекс: {int(poz)}")
                    line += 1
                    index = -1
                elif stack and (i ==" " or i == "\r") :
                    self.errors.append(f"Пробел после символа <, строка: {line}, индекс: {int(poz)}")
                stack.pop()
                poz = -20 
            elif i == "\n":
                    line += 1
                    index = -1
            index += 1   
    
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