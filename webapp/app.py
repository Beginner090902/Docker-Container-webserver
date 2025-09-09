from flask import Flask, render_template, request, jsonify
import sys
import os
sys.path.append("/scripts")
import meinskript as skript

app = Flask(__name__)

# Funktion zum Schreiben in Log-Datei
def write_to_log(message):
    with open("/scripts/output.log", "a") as f:
        f.write(f"{message}\n")
    print(message)  # Auch in Konsole ausgeben

print("Flask-App gestartet")
write_to_log("Flask-App gestartet")

@app.route("/")
def home():
    return render_template("index.html", user="Besucher")

@app.route("/start-m-server", methods=["POST"])
def start_m_server():
    write_to_log("M-Server starten gedrückt")
    skript.start_m_server()
    server_status()
    return "✅ M-Server gestartet!"

@app.route("/stop-m-server", methods=["POST"])
def stop_m_server():
    write_to_log("M-Server stoppen gedrückt")
    skript.stop_m_server()
    server_status()
    return "✅ M-Server gestoppt!"

@app.route('/server-status')
def server_status():
    # Hier prüfst du den Status des Servers
    # Dies ist ein Beispiel - du musst es an deine Bedürfnisse anpassen
    status = skript.check_server_status()  # Diese Funktion musst du implementieren
    return jsonify({"status": status})

@app.route('/get-logs')
def get_logs():
    log_file = "/scripts/output.log"
    logs = []
    
    if os.path.exists(log_file):
        with open(log_file, "r") as f:
            logs = f.read().splitlines()
    
    return jsonify({"logs": logs})

if __name__ == "__main__":
    app.run(debug=True)