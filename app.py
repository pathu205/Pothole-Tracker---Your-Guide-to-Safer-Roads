from flask import Flask, jsonify
import cx_Oracle
from flask_cors import CORS  # Import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Database connection details
db_username = "PRITAM_SAPKAL"  # Update this
db_password = "pass@123"       # Update this
db_host = "192.168.120.36"          # Update this
db_service = "XE"              # Update this

def get_pothole_data():
    """Fetch pothole data from the database."""
    connection = cx_Oracle.connect(db_username, db_password, f"{db_host}/{db_service}")
    cursor = connection.cursor()
    query = """
    SELECT "LATITUDE", "LONGITUDE", "SIZE" 
    FROM "POTHOLES_DATABASE" 
    WHERE "LATITUDE" IS NOT NULL 
      AND "LONGITUDE" IS NOT NULL
      AND "SIZE" IS NOT NULL
    ORDER BY "DETECTED" DESC
    """



    try:
        cursor.execute(query)
        data = [{
            "latitude": float(str(lat).strip()),
            "longitude": float(str(lon).strip()),
            "size": str(size).strip().lower()
        } for lat, lon, size in cursor]

    except cx_Oracle.DatabaseError as e:
        error, = e.args
        print(f"Oracle Error: {error.code} - {error.message}")
        raise


    connection.close()
    return data

@app.route('/api/potholes', methods=['GET'])
def potholes():
    """API endpoint to fetch pothole data."""
    try:
        data = get_pothole_data()
        if not data:
            return jsonify({
                "success": True,
                "message": "No pothole data found",
                "data": []
            })
        return jsonify({
            "success": True,
            "count": len(data),
            "data": data
        })
    except cx_Oracle.DatabaseError as e:
        return jsonify({
            "success": False,
            "error": "Database error",
            "details": str(e)
        }), 500
    except Exception as e:
        return jsonify({
            "success": False,
            "error": "Server error",
            "details": str(e)
        }), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
