from flask import Flask, render_template, request, redirect, jsonify
from flask_paginate import Pagination, get_page_parameter
from uuid import uuid4
import mysql.connector
from model import License
from util import get_current_datetime_str

# Connect to MySQL
# db = mysql.connector.connect(
#     host="localhost",
#     user="root",
#     password="12345678",
#     database="zanoby_bot"
# )

db = mysql.connector.connect(
    host="46.250.226.149",
    port=3307,
    user="root",
    password="12345678",
    database="zanoby_bot"
)

app = Flask(__name__)

PER_PAGE = 4

def get_total_licenses():
    # Create a cursor to execute SQL queries
    cursor = db.cursor()

    error = None
    try:
        # Execute SQL query
        query = "SELECT COUNT(*) FROM licenses"
        cursor.execute(query)
        
        # Fetch row
        row = cursor.fetchone()

        count = row[0]
    
    except Exception as e:
        error = e
        return [], error
    finally:
        # Close cursor and database connection
        cursor.close()

    return count, error

def get_license_by_license(license_key: str):
        # Create a cursor to execute SQL queries
    cursor = db.cursor()

    license: License = None

    error = None
    try:
        # Execute SQL query
        query = """
            SELECT 
                id,
                name,
                email,
                license,
                max_device,
                logged_in_device,
                created_date,
                expired_date
            FROM licenses
            WHERE 
                license = %s
        """
        cursor.execute(query, (license_key,))
        
        # Fetch row
        row = cursor.fetchone()

        if row != None:
            license = License(
                id=row[0],
                name=row[1],
                email=row[2],
                license=row[3],
                max_device=row[4],
                logged_in_device=row[5],
                created_date=row[6],
                expired_date=row[7],
            )
    
    except Exception as e:
        error = e
        return [], error
    finally:
        # Close cursor and database connection
        cursor.close()

    return license, error

def get_licenses(offset=0, per_page=PER_PAGE):
    licenses: list[License] = []

    # Create a cursor to execute SQL queries
    cursor = db.cursor()

    error = None
    try:
        # Execute SQL query
        query = """
            SELECT 
                id,
                name,
                email,
                license,
                max_device,
                logged_in_device,
                created_date,
                expired_date
            FROM licenses LIMIT %s OFFSET %s
        """
        cursor.execute(query, (per_page, offset))
        
        # Fetch all rows
        rows = cursor.fetchall()

        for row in rows:
            licenses.append(
                License(
                    id=row[0],
                    name=row[1],
                    email=row[2],
                    license=row[3],
                    max_device=row[4],
                    logged_in_device=row[5],
                    created_date=row[6],
                    expired_date=row[7],
                )
            )
    
    except Exception as e:
        error = e
        return [], error
    finally:
        # Close cursor and database connection
        cursor.close()

    return licenses, error

def insert_license(license: License):
    # Create a cursor to execute SQL queries
    cursor = db.cursor()

    error = None
    try:
        # Execute SQL query
        query = """
            INSERT INTO licenses (name,email,license,max_device,logged_in_device,created_date,expired_date) 
            VALUES (%s,%s,%s,%s,%s,%s,%s)
        """
        cursor.execute(
            query, 
            (
                license.name, 
                license.email,
                license.license,
                str(license.max_device),
                str(license.logged_in_device),
                license.created_date,
                license.expired_date,
            )
        )
        db.commit()
    
    except Exception as e:
        db.rollback()

        error = e
        return error
    finally:
        # Close cursor and database connection
        cursor.close()

    return error

def update_license(license_id: int, updates: dict):
    # Create a cursor to execute SQL queries
    cursor = db.cursor()

    error = None
    try:
        # Generate SQL query dynamically
        columns = ', '.join([f"{column} = %s" for column in updates.keys()])
        query = f"UPDATE licenses SET {columns} WHERE id = %s"
        
        # Execute SQL query
        cursor.execute(query, list(updates.values()) + [license_id])
        db.commit()
    
    except Exception as e:
        db.rollback()
        error = e
        return error
    finally:
        # Close cursor and database connection
        cursor.close()

    return error


@app.route('/licenses/activate', methods=['POST'])
def activate_license():
    license_key = request.form['license']

    license, err = get_license_by_license(license_key)
    
    if err:
        return jsonify({"message": err}), 500

    if license == None:
        return jsonify({"message": "error license is not found"}), 404

    if license.maxDeviceReached():
        return jsonify({"message": "error max device reached"}), 403
    
    err = update_license(license.id, updates={"logged_in_device": license.logged_in_device + 1})

    if err:
        return jsonify({"message": err}), 500

    license, err = get_license_by_license(license_key)
    
    if err:
        return jsonify({"message": err}), 500
    
    return jsonify({
        "license": license.__dict__
    })


@app.route('/licenses/deactivate', methods=['POST'])
def deactivate_license():
    license_key = request.form['license']

    license, err = get_license_by_license(license_key)
    
    if err:
        return jsonify({"message": err}), 500

    if license == None:
        return jsonify({"message": "error license is not found"}), 404
    
    err = update_license(license.id, updates={"logged_in_device": license.logged_in_device - 1})

    if err:
        return jsonify({"message": err}), 500

    license, err = get_license_by_license(license_key)
    
    if err:
        return jsonify({"message": err}), 500
    
    return jsonify({
        "license": license.__dict__
    })

@app.route('/')
def dashboard():
    page = request.args.get(get_page_parameter(), type=int, default=1)
    offset = (page - 1) * PER_PAGE

    total_licenses, err = get_total_licenses()

    pagination_licenses, err = get_licenses(offset=offset, per_page=PER_PAGE)

    pagination = Pagination(page=page, per_page=PER_PAGE, total=total_licenses, css_framework='bootstrap4')

    return render_template('dashboard.html', licenses=pagination_licenses, pagination=pagination)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        max_device = request.form['max_device']
        expiration = request.form['expiration']
        
        new_license = License(
            name=name,
            email=email,
            license=str(uuid4()),
            max_device=max_device,
            created_date=get_current_datetime_str(),
            expired_date=expiration,
        )

        err = insert_license(new_license)

        print(err)

        return redirect('/')
    return render_template('register.html')

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
