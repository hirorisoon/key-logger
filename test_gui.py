import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QPushButton, QSystemTrayIcon)
from PyQt6.QtCore import QTimer

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.counter = 0
        self.init_ui()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_counter)
        self.timer.start(1000)

    def init_ui(self):
        self.setWindowTitle('GUIテスト')
        self.setGeometry(100, 100, 100, 100)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.label = QLabel('カウンター: 0')
        layout.addWidget(self.label)

        table = QTableWidget()
        table.setRowCount(3)
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(['key','count'])

        test_data = [('a',10), ('b',10), ('c',10)]
        for i, (key, count) in enumerate(test_data):
            tableItem = QTableWidgetItem(key)
            tableItem.on_press
            table.setItem(i, 0, QTableWidgetItem(key))
            table.setItem(i, 1, QTableWidgetItem(str(count)))

        layout.addWidget(table)

        btn = QPushButton('テストボタン')
        btn.clicked.connect(self.on_button_click)
        layout.addWidget(btn)

    def update_counter(self):
        '''1秒ごとにカウンターを更新'''
        self.counter += 1
        self.label.setText(f'カウンター: {self.counter}')

    def on_button_click(self):
        print('ボタンがクリックされました')
        self.label.setText(f'カウンター: {self.counter} （ボタンクリック）')

def main():
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()

    sys.exit(app.exec())

if __name__  == '__main__':
    main()
