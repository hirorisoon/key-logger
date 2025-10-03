import sys
import sqlite3
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
                             QPushButton, QTabWidget, QSystemTrayIcon, QMenu)
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QTimer
from PyQt6.QtGui import QIcon, QAction
from pynput import keyboard
from collections import defaultdict

class KeyLogger(QThread):
    '''バックグラウンドでキー入力を監視するスレッド'''
    key_pressed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.listener = None
        self.running = False

    def run(self):
        '''キー監視を開始'''
        self.running = True
        with keyboard.Listener(on_press=self.on_press) as self.listener:
            self.listener.join()

    def on_press(self, key):
        '''キーが押された時の処理'''
        if not self.running:
            return False

        try:
            # 通常のキー
            key_name = key.char if hasattr(key, 'char') else str(key).replace('Key.', '')
        except:
            key_name = str(key).replace('Key.', '')

        self.key_pressed.emit(key_name)

    def stop(self):
        '''監視を停止'''
        self.running = False
        if self.listener:
            self.listener.stop()

class Database:
    '''SQLiteデータベース管理クラス'''

    def __init__(self, db_path='keylog.db'):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        '''データベースとテーブルを初期化'''
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS key_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                key_name TEXT NOT NULL,
                count INTEGER DEFAULT 1,
                UNIQUE(date, key_name)
            )
        ''')
        conn.commit()
        conn.close()

    def save_key(self, key_name):
        '''キー入力を保存（同じ日付、キーなら加算）'''
        date = datetime.now().strftime('%Y-%m-%d')
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO key_logs (date, key_name, count)
                        VALUES (?, ?, 1)
                        ON CONFLICT(date, key_name) DO UPDATE SET count = count + 1
        ''', (date, key_name))
        conn.commit()
        conn.close()

    def get_total_stats(self):
        '''累計統計を取得'''
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT key_name, SUM(count) as total
                       FROM key_logs
                       GROUP by key_name
                       ORDER BY total DESC
        ''')
        ressults = cursor.fetchall()
        conn.close()
        return ressults
    def get_daily_stats(self, date=None):
        '''日付ごとの統計を取得'''
        if date is None:
            date = datetime.now().strftime('%Y-%m-d')
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT key_name, count
                        FROM key_logs
                       WHERE date = ?
                       ORDER BY count DESC
        ''', (date,))
        results = cursor.fetchall()
        conn.close()
        return results
    def get_all_dates(self):
        '''記録されているすべての日付を取得'''
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT DISTINCT date
                       FROM key_logs
                       ORDER BY date DESC
        ''')
        results = [row[0] for row in cursor.fetchall()]
        conn.close()
        return results

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.key_logger = KeyLogger()
        self.current_session_keys = defaultdict(int)

        self.init_ui()
        self.init_tray()
        self.start_logging()

        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(500)

    def init_ui(self):
        '''UIを初期化'''
        self.setWindowTitle('キー入力監視アプリ')
        self.setGeometry(100, 100, 800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Tab
        tabs = QTabWidget()
        layout.addWidget(tabs)

        # today
        self.today_tab = self.create_stats_tab()
        tabs.addTab(self.today_tab, '今日の統計')

        # total
        self.total_tab = self.create_stats_tab()
        tabs.addTab(self.total_tab, '累計')

        # stats
        self.status_label = QLabel('監視中')
        layout.addWidget(self.status_label)

        self.update_display()

    def create_stats_tab(self):
        '''統計表示タブを作成'''
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 統計情報
        info_layout = QHBoxLayout()
        total_label = QLabel('総キー入力数: 0')
        total_label.setObjectName('total_label')
        info_layout.addWidget(total_label)
        info_layout.addStretch()
        layout.addLayout(info_layout)

        # table
        table = QTableWidget()
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(['key', 'count'])
        table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(table)

        return widget

    def init_tray(self):
        '''システムトレイアイコンを初期化'''
        self.tray_icon = QSystemTrayIcon(self)

        self.tray_icon.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_ComputerIcon))

        # tray menu
        tray_menu = QMenu()

        show_action = QAction('表示', self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)

        hide_action = QAction('非表示', self)
        hide_action.triggered.connect(self.hide)
        tray_menu.addAction(hide_action)

        tray_menu.addSeparator()

        quit_action = QAction('終了', self)
        quit_action.triggered.connect(self.quit_application)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_icon_activated)
        self.tray_icon.show()

    def tray_icon_activated(self, reason):
        '''トレイアイコンクリック時の処理'''
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.activateWindow()
    def start_logging(self):
        '''キーロギングを開始'''
        self.key_logger.key_pressed.connect(self.on_key_pressed)
        self.key_logger.start()

    def on_key_pressed(self, key_name):
        self.current_session_keys[key_name] += 1
        self.db.save_key(key_name)

    def update_display(self):
        '''表示を更新'''
        # today
        today_stats = self.db.get_daily_stats()
        self.update_table(self.today_tab, today_stats)

        # total
        total_stats = self.db.get_total_stats()
        self.update_table(self.total_tab, total_stats)

        session_total = sum(self.current_session_keys.values())
        self.status_label.setText(f'監視中...(今回のセッション: {session_total}キー)')

    def update_table(self, tab_widget, data):
        '''テーブルを更新'''
        table = tab_widget.findChild(QTableWidget)
        total_label = tab_widget.findChild(QLabel, 'total_label')

        table.setRowCount(len(data))
        total = 0

        for i, (key, count) in enumerate(data):
            table.setItem(i, 0, QTableWidgetItem(str(key)))
            table.setItem(i, 1, QTableWidgetItem(str(count)))
            total += count

        total_label.setText(f'総キー入力数: {total:,}')

    def closeEvent(self, event):
        '''ウィンドウを閉じるとき、最小化してトレイに収納'''
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            'キー入力監視アプリ',
            'バックグラウンドで作動中です',
            QSystemTrayIcon.MessageIcon.Information,
            1000
        )

    def quit_application(self):
        '''アプリケーションを終了'''
        self.key_logger.stop()
        self.key_logger.wait()
        QApplication.quit()

def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False) # ウィンドウを閉じてもアプリは終了しないようにする

    window = MainWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == '__main__':
    main()
