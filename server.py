from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os

app = Flask(__name__)
CORS(app)  # מאפשר בקשות מכל דומיין

def write_to_json(name_j, data):
    """פונקציה לשמירת נתונים בקובץ JSON"""
    try:
        file_path = f"{name_j}.json"

        # בדיקה האם הקובץ קיים - אם כן, טוענים את הנתונים הקיימים; אחרת, מאותחלים במילון ריק
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    data_json = json.load(file)
            except json.JSONDecodeError:
                data_json = {}  # במקרה של שגיאה בקריאת הקובץ, מאותחלים במילון ריק
        else:
            data_json = {}

        # עדכון הנתונים עם המידע החדש
        data_json.update(data)

        # שמירה מחדש של הנתונים עם עיצוב ברור (indent=4)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data_json, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print("❌ שגיאה בכתיבת קובץ JSON:", e)  # הודעת שגיאה בעת כתיבת הקובץ

@app.route('/api/status/update', methods=['POST'])
def status_update():
    print("📡 התחלת טיפול בבקשת עדכון סטטוס מהקיי לוגר")  # הודעה המצביעה על התחלת טיפול בבקשה מהקיי לוגר
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON"}), 400

        status = {"mac_address": data}
        write_to_json("device_status", status)
        print("✅ נתוני סטטוס מהקיי לוגר התקבלו:", data)  # הדפסת הנתונים שהתקבלו מהקיי לוגר
        return jsonify({"message": "Success"}), 200
    except Exception as e:
        print("❌ שגיאה בעדכון סטטוס מהקיי לוגר:", e)
        return jsonify({"error": str(e)}), 500

@app.route('/api/data/upload', methods=['POST'])
def upload_data():
    # טיפול בבקשת העלאת נתוני מחשב מהאתר (מזהה MAC חובה)
    print("📡 התחלת טיפול בבקשת העלאת נתוני מחשב מהאתר")
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON"}), 400

        mac_address = data.get("Mac-Address")
        if not mac_address:
            return jsonify({"error": "Missing macAddress"}), 400

        data = {"mac_address": data}
        write_to_json("device_status", data)
        print("✅ נתוני מחשב מהאתר התקבלו:", data)  # הדפסת הנתונים שהתקבלו מהאתר
        return jsonify({"message": "Success"}), 200
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON file"}), 500
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
    """שליפת קובץ הסטטוסים של כל המכשירים המחוברים עבור הדף האינטרנט"""
    print("📡 התחלת טיפול בבקשת שליפת סטטוסים לכל המכשירים מהאתר")
    try:
        with open("device_status.json", "r", encoding="utf-8") as file:
            data_json = json.load(file)
            print("✅ סטטוסים שנשלחו אל הדף מהשרת:", data_json)  # הדפסת סטטוסים שנשלחו אל הדף מהשרת
        return jsonify(data_json)
    except FileNotFoundError:
        return jsonify({"error": "No data found"}), 404
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

            print("✅ סטטוס אחרון מהקיי לוגר עבור MAC", mac_address, ":", device_status)  # הדפסת סטטוס אחרון שהתקבל מהקיי לוגר
            return jsonify(device_status)
    except FileNotFoundError:
        return jsonify({"error": "Status file not found"}), 500
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON file"}), 500

@app.route('/api/status/change', methods=['POST'])
def change_status():
    """מקבל נתוני סטטוס מהאתר ושומר בקובץ לפי כתובת MAC"""
    print("📡 התחלת טיפול בבקשת שינוי סטטוס מהאתר")
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON"}), 400

        mac_address = data.get("Mac-Address")
        if not mac_address:
            return jsonify({"error": "Missing macAddress"}), 400

        status = {"mac_address": data}
        write_to_json("change_device_status", status)
        print("✅ נתוני סטטוס מהאתר התקבלו:", data)  # הדפסת הנתונים שהתקבלו מהאתר
        return jsonify({"message": "Success"}), 200
    except FileNotFoundError:
        return jsonify({"error": "Status file not found"}), 500
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON file"}), 500
    except Exception as e:
        print("❌ שגיאה בעדכון סטטוס מהאתר:", e)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
