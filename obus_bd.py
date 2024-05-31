import sqlite3 as sql

def create_obu_db():
    db = sql.connect('obu.db')

    db.execute('''DROP TABLE IF EXISTS obu''')
    db.execute('''CREATE TABLE obu(lat REAL, long REAL, stationID INTEGER PRIMARY KEY);''')
    db.execute('''DROP  TABLE IF EXISTS violations''')
    db.execute('''CREATE TABLE violations(violation_type TEXT, stationID INTEGER PRIMARY KEY);''')
    db.execute('''DROP  TABLE IF EXISTS swerve''')
    db.execute('''CREATE TABLE swerve(swerve_type TEXT, stationID INTEGER PRIMARY KEY);''')

    db.execute('INSERT INTO obu VALUES(NULL, NULL, 1)')
    db.execute('INSERT INTO obu VALUES(NULL, NULL, 2)')
    db.execute('INSERT INTO obu VALUES(NULL, NULL, 3)')
    db.execute('INSERT INTO obu VALUES(NULL, NULL, 4)')

    db.execute('INSERT INTO violations VALUES(NULL, 1)')
    db.execute('INSERT INTO swerve VALUES(NULL, 3)')
    db.execute('INSERT INTO swerve VALUES(NULL, 4)')

    db.commit()
    db.close()

create_obu_db()
