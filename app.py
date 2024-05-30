from flask import Flask, render_template
import sqlite3 as sql
from obus_bd import create_obu_db
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app)

@app.route('/get_coordinates')
def get_coordinates():
    try:
        db = sql.connect('obu.db')
        cursor = db.cursor()
        cursor.execute("SELECT * FROM obu")
        data = cursor.fetchall()
        db.close()
        print(data)
        return data
    except Exception as e:
        print(f"Error fetching coordinates from the database: {e}")
        return []

@app.route('/violations')
def get_violations():
    try:
        db = sql.connect('obu.db')
        cursor = db.cursor()
        cursor.execute("SELECT * FROM violations")
        data = cursor.fetchall()
        db.close()
        print(data)
        return data
    except Exception as e:
        print(f"Error fetching violations from the database: {e}")
        return []

@app.route('/frontCar')
def get_frontCar():
    try:
        db = sql.connect('obu.db')
        cursor = db.cursor()
        cursor.execute("SELECT * FROM swerve")
        data = cursor.fetchall()
        db.close()
        print(data)
        return data
    except Exception as e:
        print(f"Error fetching frontCar from the database: {e}")
        return []

@app.route('/')
def index():
    try:
        coordinates = get_coordinates()
        violations = get_violations()
        frontCar = get_frontCar()
        print("Coordinates fetched from DB:", coordinates)  # Debug print
        return render_template('index.html', coordinates=coordinates, violations=violations, frontCar=frontCar)
    except Exception as e:
        print(f"Error rendering template: {e}")
        return "An error occurred", 500
    

def notify_car_reaction():
    socketio.emit('car_reaction', {'message': 'Car should react'})


if __name__ == '__main__':
    create_obu_db()
    app.run(debug=True)
    socketio.run()
