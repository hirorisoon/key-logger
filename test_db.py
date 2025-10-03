import sqlite3
from datetime import datetime

class Database:
    def __init__(self, db_path='test_keylog.db'):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        '''DBとテーブルを初期化'''
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
        print('complete: initialize database')

    def save_key(self, key_name):
        '''キー入力を保存'''
        date = datetime.now().strftime('%Y-%m-%d')
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO key_logs (date, key_name, count)
            VALUES (?, ?, 1)
            ON CONFLICT (date, key_name) DO UPDATE SET count = count + 1
        ''', (date, key_name))
        conn.commit()
        conn.close()

    def get_daily_stats(self):
        '''今日の統計を集計'''
        date = datetime.now().strftime('%Y-%m-%d')
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT key_name, count
            FROM key_logs
            WHERE date = ?
            ORDER BY count DESC
        ''', (date, ))
        results = cursor.fetchall()
        conn.close()
        return results

## テスト実行
print('データベーステスト開始')
print("="*40)

db = Database()

test_keys = ['a','b','c','d','e','f','g']
print(f'テストキーを保存: {test_keys}')
for key in test_keys:
    db.save_key(key)
    print(f'  保存: {key}')

print('\n統計結果:')
stats = db.get_daily_stats()
for key, count in stats:
    print(f'  {key}: {count}回')


