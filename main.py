import os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.Qsci import *
from PyQt5.QtGui import *
import sys
from pathlib import Path
from editor import Editor

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
    
    
    def is_binary (self, path):
        # Проверка на бинарный файл - не может быть открыт в редакторе
        with open (path, 'rb') as f:
            return b'\0' in f.read(1024)
    
    def set_new_tab(self, path: Path, is_new_file = False):
        if not is_new_file and self.is_binary(path):
            self.statusBar().showMessage("Невозможно открыть файл!", 2000)
            return
        if path.is_dir():
            return
        editor = self.get_editor(path)
        if is_new_file:
            self.tab_view.addTab(editor, "Без названия")
            self.setWindowTitle("Без названия")
            self.tab_view.setCurrentIndex(self.tab_view.count() -1)
            self.current_file = None
            return       
        
        # Проверка, открыт ли файл в одной из вкладок
        for i in range (self.tab_view.count()):
            if self.tab_view.tabText(i) == path.name or self.tab_view.tabText(i) == "*"+path.name:
               self.tab_view.setCurrentIndex(i)
               self.current_file = path 
               return
                
        self.tab_view.addTab(editor,path.name)
        editor.setText(path.read_text(encoding="utf-8"))
        self.setWindowTitle(f"{path.name}")
        self.current_file = path 
        self.tab_view.setCurrentIndex(self.tab_view.count()-1)
        self.statusBar().showMessage(f"Открыт {path.name}", 2000)

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
                
        self.hsplit = QSplitter(Qt.Horizontal)
        self.hsplit.addWidget(self.tab_view)  
        body.addWidget(self.hsplit)
        body_frame.setLayout(body)     
                
        self.setCentralWidget(body_frame)
        
    def close_tab(self, index):
        editor: Editor = self.tab_view.currentWidget()
        if editor.current_file_changed:
            dialog = self.show_dialog("Close", f"Сохранить изменения в {self.current_file.path.name}?")
            if dialog == QMessageBox.Yes:
                self.save_file()
        self.tab_view.removeTab(index)
    
    def show_dialog(self, title, msg) -> int:
        dialog = QMessageBox(self)
        dialog.setFont(self.font())
        dialog.font().setPointSize(14)
        dialog.setWindowTitle(title)
        dialog.setWindowIcon(QIcon(":/icons/close-icon.svg"))
        dialog.setText(msg)
        dialog.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        dialog.setDefaultButton(QMessageBox.No)
        dialog.setIcon(QMessageBox.Warning)
        return dialog.exec_()
        
    def new_file(self):
        self.set_new_tab(Path("untitled"), is_new_file=True)
        
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
        if self.current_file is None and self.tab_view.count() > 0:
            self.save_as()
        
        editor = self.tab_view.currentWidget()
        self.current_file.write_text(editor.text())
        self.statusBar().showMessage(f"{self.current_file.name}", 2000)
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
        self.tab_view.setTabText(self.tab_view.currentIndex(),path.name)
        self.statusBar().showMessage(f"Сохранено: {path.name}", 2000)
        self.current_file = path
        editor.current_file_changed = False

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