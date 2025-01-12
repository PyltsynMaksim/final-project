import sqlite3

def create_favourites_table():
    conn = sqlite3.connect('favourite.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS favourites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

create_favourites_table()
