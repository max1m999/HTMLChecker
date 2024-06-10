import os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.Qsci import *
from PyQt5.QtGui import *
import sys
from pathlib import Path
import csv
from editor import Editor

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.init_ui()
        self.current_file = None 
        self.tags_table = []
        self.loadTags()       
        
    def init_ui(self):
        self.setWindowIcon(self.style().standardIcon(getattr(QStyle,'SP_FileDialogDetailedView')))
        self.app_name = "HTML МАСТЕР"
        self.setWindowTitle(self.app_name)
        self.resize(1300,900)
        self.setStyleSheet(open ("_internal\css\style.qss", "r").read())
        # Шрифт интерфейса
        self.window_font = QFont("FiraCode", 16)
        self.setFont(self.window_font)
        
        self.set_up_menu()
        self.set_up_body() 
        self.set_up_status_bar()
        
        self.show()
        
    
    def set_up_status_bar(self):
        # Строка оповещений
        stat = QStatusBar(self)
        stat.setStyleSheet("color: #1C9BCB; height: 25px; font: 600 15px #1C9BCB;")
        self.setStatusBar(stat)
    
    def get_editor(self, path: Path = None) -> QsciScintilla:
        editor = Editor(self, path = path)
        return editor
        
    def set_up_menu(self):
        menu_bar = self.menuBar()
    
        # Меню Файл
        file_menu = menu_bar.addMenu("Файл")
    
        new_file = file_menu.addAction("Новый")
        new_file.setShortcut("Ctrl+N")
        new_file.triggered.connect(self.new_file)
    
        open_file = file_menu.addAction("Открыть файл")
        open_file.setShortcut("Ctrl+O")
        open_file.triggered.connect(self.open_file)
        
        file_menu.addSeparator()
        save_file = file_menu.addAction("Сохранить файл")
        save_file.setShortcut("Ctrl+S")
        save_file.triggered.connect(self.save_file)
        
        save_as = file_menu.addAction("Сохранить как...")
        save_as.setShortcut("Ctrl+Shift+s")
        save_as.triggered.connect(self.save_as)

        # Меню Редактировать
        edit_menu = menu_bar.addMenu("Редактировать")
    
        copy_action = edit_menu.addAction("Копировать")
        copy_action.setShortcut("Ctrl+C")
        copy_action.triggered.connect(self.copy)
        
        cut_action = edit_menu.addAction("Вырезать")
        cut_action.setShortcut("Ctrl+X")
        cut_action.triggered.connect(self.cut)
    
        paste_action = edit_menu.addAction("Вставить")
        paste_action.setShortcut("Ctrl+V")
        paste_action.triggered.connect(self.paste)
        
        # Меню Сервис
        service_menu = menu_bar.addMenu("Сервис")
        
        analysis_action = service_menu.addAction("Анализ файла")
        analysis_action.setShortcut("F5")
        analysis_action.triggered.connect(self.analysis)
        
        fix_action = service_menu.addAction("Восстановить файл")
        fix_action.setShortcut("F10")
        fix_action.triggered.connect(self.fix)
    
    # Загрузка таблицы с тегами    
    def loadTags(self):
        with open('_internal\HTML5 tags.csv') as File:
            reader = csv.DictReader(File, dialect="excel", delimiter=";")
            for row in reader:
                self.tags_table.append(row)
    
    def analysis(self):
        editor = self.tab_view.currentWidget() 
        if editor: 
            self.errors.clear()
            editor.start_analysis()
            
    def fix(self):
        editor = self.tab_view.currentWidget() 
        if editor: 
            self.errors.clear()
            editor.start_fixing()
            
    
    def is_binary (self, path):
        # Проверка на бинарный файл - не может быть открыт в редакторе
        with open (path, 'rb') as f:
            return b'\0' in f.read(1024)
    
    def set_new_tab(self, path: Path, is_new_file = False, msg = 1):
        if not is_new_file and self.is_binary(path):
            self.statusBar().showMessage("Невозможно открыть файл!", 2000)
            return
        if path.is_dir():
            return
        editor = self.get_editor(path)
        if is_new_file:
            self.tab_view.addTab(editor, f"{path}")
            self.tab_view.setCurrentIndex(self.tab_view.count() -1)
            self.current_file = None
            return  
                 
        # Проверка, открыт ли файл в одной из вкладок
        for i in range (self.tab_view.count()):
            if self.tab_view.tabText(i) == f"{path.absolute()}" or self.tab_view.tabText(i) == "*"+f"{path.absolute()}":
               self.tab_view.setCurrentIndex(i)
               self.current_file = path 
               return
                
        self.tab_view.addTab(editor,f"{path.absolute()}")
        editor.setText(path.read_text(encoding="utf-8"))
        self.current_file = path 
        self.tab_view.setCurrentIndex(self.tab_view.count()-1)
        if msg > 0: self.statusBar().showMessage(f"Открыт {path.name}", 2000)

    def set_up_body(self):
        # Body
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
        
        # Виджет вкладки
        self.tab_view = QTabWidget()    
        self.tab_view.setContentsMargins(0,0,0,0)
        self.tab_view.setTabsClosable(True)
        self.tab_view.setMovable(True)
        self.tab_view.setDocumentMode(True)
        self.tab_view.tabCloseRequested.connect(self.close_tab)
        
        # Окно ошибок
        self.errors = QListWidget() 
        self.errors.setContentsMargins(0,0,0,0) 
        self.errors.setMaximumHeight(200)
        self.errors.setFont(QFont("FiraCode", 14))
        self.errors.setStyleSheet("""
        QListWidget {
            background-color: #21252b;
            border-radius: 1px;            
            padding: 5px;
            color: #D3D3D3;
        }
        """)
        self.errors.addItem("Откройте HTML файл и запустите анализ в меню Сервис")
                     
        self.vsplit = QSplitter(Qt.Vertical)
        self.vsplit.addWidget(self.tab_view)  
        self.vsplit.addWidget(self.errors)  
        body.addWidget(self.vsplit)
        body_frame.setLayout(body)     
                
        self.setCentralWidget(body_frame)   
  
        
    def closeEvent(self, event):
        while self.tab_view.count() > 0:
            self.close_tab(0)
        
    def close_tab(self, index):
        if "*" in self.tab_view.tabText(index):
            dialog = self.show_dialog("Закрыть вкладку", f"Сохранить изменения в {self.tab_view.tabText(index) [1:]}?")
            if dialog == 1:
                self.tab_view.setCurrentIndex(index)
                self.current_file = Path(self.tab_view.tabText(index)[1:])
                self.save_file()
        self.tab_view.removeTab(index)
    
    def show_dialog(self, title, msg) -> int:
        dialog = QMessageBox(self)
        dialog.setFont(self.font())
        dialog.font().setPointSize(14)
        dialog.setWindowTitle(title)
        dialog.setWindowIcon(self.style().standardIcon(getattr(QStyle,'SP_MessageBoxCritical')))
        dialog.setText(msg)
        dialog.addButton("Нет", QMessageBox.NoRole)
        dialog.addButton("Да", QMessageBox.YesRole)
        dialog.setDefaultButton(QMessageBox.No)
        dialog.setIcon(QMessageBox.Warning)
        return dialog.exec_()
        
    def new_file(self):
        count = 0
        for i in range (self.tab_view.count()):
            if "Без названия" in self.tab_view.tabText(i):
                count+=1
        if count > 0:
            self.set_new_tab(Path(f"Без названия_{count}"), is_new_file=True)
        else:
            self.set_new_tab(Path("Без названия"), is_new_file=True)
        
    def open_file(self):
        new_file, _ = QFileDialog.getOpenFileName(self, "Выберите файл", "", "HTML файлы (*.html);;Все файлы (*)")
        if new_file == '':
            self.statusBar().showMessage("Отмена", 2000)
            return
        f =  Path(new_file)
        self.set_new_tab(f)
            
    def save_file(self):
        if self.tab_view.count() == 0:
            return
        if (self.current_file is None or "Без названия" in f"{self.current_file}") and self.tab_view.count() > 0:
            self.save_as()
            return
        
        editor = self.tab_view.currentWidget()
        self.current_file.write_text(editor.text(), encoding="utf-8")
        self.statusBar().showMessage(f"{self.current_file}", 2000)
        editor.current_file_changed = False
        
    def save_as(self):
        if self.tab_view.count() == 0:
            return
        file_path = QFileDialog.getSaveFileName(self,"Сохранить как", os.getcwd(), "HTML файлы (*.html);;Все файлы (*)") [0]
        if file_path == '':
            self.statusBar().showMessage("Отмена", 2000)
            return
        path = Path(file_path)
        editor = self.tab_view.currentWidget()
        path.write_text(editor.text(), encoding="utf-8")
        self.tab_view.setTabText(self.tab_view.currentIndex(),f"{path}")
        self.statusBar().showMessage(f"Сохранено: {path}", 2000)
        self.current_file = path
        editor.current_file_changed = False
        self.tab_view.removeTab(self.tab_view.currentIndex())
        self.set_new_tab(path, msg = 0)

    def copy(self):
        editor = self.tab_view.currentWidget()
        if editor is not None:
            editor.copy()
        
    def paste(self):
        editor = self.tab_view.currentWidget()
        if editor is not None:
            editor.paste()
    def cut(self):
        editor = self.tab_view.currentWidget()
        if editor is not None:
            editor.cut()
        
if __name__ == '__main__':
    app = QApplication ([])
    window = MainWindow()
    sys.exit(app.exec())