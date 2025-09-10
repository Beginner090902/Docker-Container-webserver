from flask import Flask, render_template, request, jsonify
import sys
import os
sys.path.append("/scripts")
import meinskript as skript
from datetime import datetime

app = Flask(__name__)



def cleanup_logs(log_file, max_size_kb=10, keep_lines=20):

    if not os.path.exists(log_file):
        return
    
    # Dateigröße in KB berechnen
    file_size_kb = os.path.getsize(log_file) / 1024
    
    if file_size_kb < max_size_kb:
        return
    
    # Log-Einträge lesen
    with open(log_file, 'r') as file:
        lines = file.readlines()
    
    # Wenn nicht genug Zeilen vorhanden sind, nichts tun
    if len(lines) <= keep_lines:
        return
    
    # Die letzten 'keep_lines' Zeilen behalten
    lines_to_keep = lines[-keep_lines:]
    
    # Log-Datei mit den behaltenen Zeilen überschreiben
    with open(log_file, 'w') as file:
        file.writelines(lines_to_keep)
    
    print(f"Log bereinigt: {len(lines) - keep_lines} Einträge gelöscht, {keep_lines} behalten")


# Funktion zum Schreiben in Log-Datei
def write_to_log(message):
    zeitstempel = datetime.now().strftime("%H:%M:%S %d.%m.%Y")
    with open("/scripts/output.log", "a") as f:
        f.write(f"{zeitstempel} - {message}\n")
    cleanup_logs("/scripts/output.log", max_size_kb=100, keep_lines=20)
    print(message)  # Auch in Konsole ausgeben


write_to_log("Flask-App gestartet")

@app.route("/")
def home():
    return render_template("index.html", user="Besucher")

@app.route("/start-m-server", methods=["POST"])
def start_m_server():
    write_to_log("M-Server starten gedrückt")
    skript.start_m_server()
    server_status()
    return "✅ In Arbeit(Start) Warte!"

@app.route("/stop-m-server", methods=["POST"])
def stop_m_server():
    write_to_log("M-Server stoppen gedrückt")
    skript.stop_m_server()
    server_status()
    return "✅ In Arbeit(Stop) Warte!"

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