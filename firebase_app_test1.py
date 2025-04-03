from flask import Flask, jsonify
import firebase_admin
from firebase_admin import credentials, firestore
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Firebase JSON Key
firebase_config = {
    "type": "service_account",
    "project_id": "potholes-tracker-6de66",
    "private_key_id": "7fde427ccd64cea5009609b705e85446197cbcdd",
    "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDA4rTSIVFWy16I\n7NeTzGAekDoah2pvx5SgKAPtyBqVmmcNMFj6A0ZQl3IHI2/PCF7LWS4S3Xn/Sj2f\nYVCYOkkkvyB5j3hpzll7iGPUDX5lAgPZY7I5p/R/UJXXp9jKRE98lhpan/N0xPka\n5UD3qbyfOTwLNhMQZnioQDo8FTlpuGMI30INJ/ig/6p+Cfi3vIiY9dx2H3RujAwJ\ndUyVqRtgeriwHTUAuhXFoH0/Up1GI7AN4alhg/PXCcIipmgkK6yl5o1ZpkytzqyE\n+VYKelLVZog7nNr9R1JSV5qo1GWHhHOCJu8Hu50uh1AzPXmaGiA7umSg2HtbiK4U\nOXSbmyX3AgMBAAECggEAFF5cYJbqyKhFMrRqt3gs66KotXB4tEEhLXXMTxSDKiqE\nmLHy/hkmbbrwbFc4/BCS4hUSy88zji/q00/Ve53RZ4iqB0GNTQRgvVjTzJV4NCEY\nWEvc4EB04z+WneVi+/O8E8NOGSUsR7fH49KIdR7UL67oQPl+3eEppgAnpidKSXg4\n8NPvY5xzEm9VA1q1UARv+f4AYVhbSy8WhKL2oMYxwiXNSkeMIrnQdBhuxaqv7H5r\nLUuHMQnYpEYKX8irusfX0Ows6yR2OHKXcY/NDsBIIS63ipxvnupHI1Y7vS7K3GAX\nn9opBM5gkXj5uImTucsdx1fs+AoYc2t2y/AaL8XSEQKBgQDjPu4Fefu0PmYyMDiN\nZTb4wOeXkRSqSLIqpX151VoNzbY6OQFJ1kdx2TUIg9sBKwrRCYO8uN34BcYoc86O\nljlH680FzSSxi+PgaSxH9NSxZiAGnyMBLwzE/IaZ/ygQyuOkheiL2VbwbHZEX57W\nzHW/SH8M3yJ/ux9Cs1pnrx8LQwKBgQDZSsK+YSrisnWu82YF5Ex/dBuYvVxkXddA\ntpmGNwS07lkYDCaB2wsF2nvGFVmQWTRBpQ2Jv91iAX/SYkIt0JhcXQgTZhVlF61+\n136vlwpDDejLZTzIcag9YCwh5uj4Kux3ff1/jeab8flaSh1IP7Cs6XPaXBIL/pGI\nsnbOY7e9PQKBgQDDqhKt+ntElhnOiwCWlpi/lPGT6qKdgFyQJdAlUBPrIL4P4bd/\nSRZZK8njHA09Mz9r/8JDg/XzsZ0OhbBLy4Nkrt7oaNt4WFgMiOJMzr04RhO7P9iX\nE1juX/TRsgZgdyGNLpOtnqSh/PHUK3ULxB56ZkSm45XD322qM93ausmDGwKBgBqM\nNsTZzEqMMTKhzDo2DV6ZCfIcWJhumqjuZk1ulWWhpUL54Q6Ge49IhUzLOPkY3PiU\nONY2mc6qjjpfBOTiEmtedmkgVMbYILtZisHbO0a8AVAwWz/GGx78jAfMVXRUkjV7\nMCiQZrdw1d1BJti351cI4r2v+Ah9HrzLyRYoOr+lAoGAMTl731FuVp6/qA4YVsz2\nvFxZbHveKFPJRxKI+do4SveiXF8x1GzH0brtwMm1hh7BZIs/kOQkK4azIYZnhCsm\nx7IQm743OqWST803JIorshwn5uftOTuD0nls59YMVnv0FRPOQheYKcsTbnjX4NMo\n/UNp0Du4zcGUaGJofxyGXtk=\n-----END PRIVATE KEY-----\n",
    "client_email": "firebase-adminsdk-fbsvc@potholes-tracker-6de66.iam.gserviceaccount.com",
    "client_id": "114758203481956963523",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40potholes-tracker-6de66.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com"
}

cred = credentials.Certificate(firebase_config)
firebase_admin.initialize_app(cred)
db = firestore.client()

def get_pothole_data():
    try:
        potholes_ref = db.collection("potholes_database").stream()
        data = [{
            "latitude": float(doc.to_dict().get("latitude", 0)),
            "longitude": float(doc.to_dict().get("longitude", 0)),
            "size": str(doc.to_dict().get("size", "")).strip().lower()
        } for doc in potholes_ref if doc.to_dict().get("latitude") and doc.to_dict().get("longitude")]
        return data
    except Exception as e:
        print(f"Firebase Error: {str(e)}")
        return []

@app.route('/api/potholes', methods=['GET'])
def potholes():
    try:
        data = get_pothole_data()
        return jsonify({
            "success": True,
            "count": len(data),
            "data": data if data else []
        })
    except Exception as e:
        return jsonify({"success": False, "error": "Server error", "details": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
