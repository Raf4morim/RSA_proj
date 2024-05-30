from flask import Flask, render_template
import sqlite3 as sql
from obus_bd import create_obu_db

app = Flask(__name__)

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

@app.route('/')
def index():
    try:
        coordinates = get_coordinates()
        print("Coordinates fetched from DB:", coordinates)  # Debug print
        return render_template('index.html', coordinates=coordinates)
    except Exception as e:
        print(f"Error rendering template: {e}")
        return "An error occurred", 500

if __name__ == '__main__':
    create_obu_db()
    app.run(debug=True)
