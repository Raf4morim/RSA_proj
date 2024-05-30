import sqlite3 as sql

def create_obu_db():
    db = sql.connect('obu.db')

    db.execute('''DROP TABLE IF EXISTS obu''')
    db.execute('''CREATE TABLE obu(lat REAL, long REAL, ip TEXT PRIMARY KEY);''')

    db.execute('INSERT INTO obu VALUES(NULL, NULL, "192.168.98.10")')
    db.execute('INSERT INTO obu VALUES(NULL, NULL, "192.168.98.20")')
    db.execute('INSERT INTO obu VALUES(NULL, NULL, "192.168.98.30")')
    # db.execute('INSERT INTO obu VALUES(NULL, NULL, "192.168.98.40")')

    db.commit()
    db.close()

create_obu_db()