from flask import Flask, render_template, request, jsonify, session
import sys
import os
sys.path.append("/scripts")
import meinskript as skript
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler


app = Flask(__name__)
app.secret_key = 'dein_geheimer_schluessel'

def auto_container_stop():
    if os.getenv("Auto_Stop") == "True":
        current_time = datetime.now().strftime("%H:%M")
        if current_time == os.getenv("Auto_Stop_Time"):
            skript.stop_m_server()
            skript.write_to_log(f"Automatischer Stopp des Containers um {current_time}")
    else:
        pass
    

scheduler = BackgroundScheduler()
scheduler.add_job(auto_container_stop, "interval", seconds=50)
scheduler.start()

# Verifizierungs-Funktion
def verify_password(password):
    # Hier kannst du deine eigene Verifizierungslogik einbauen
    # Einfaches Beispiel: Passwort = "admin123"
    richtiges_password = os.getenv("PASSWORD")
    if richtiges_password is None:
        print("Umgebungsvariable PASSWORD ist nicht gesetzt.")
        return False
    elif password == richtiges_password:
        return True
    return False





skript.write_to_log("Flask-App gestartet")

@app.route("/")
def home():
    # Prüfen ob der Benutzer verifiziert ist
    if session.get('verified'):
        container_name = os.getenv("Name_of_your_container")
        return render_template("index.html", container_name=container_name, user="Verifizierter Benutzer", verified=True)
    else:
        return render_template("login.html")
    
@app.route("/login", methods=["POST"])
def login():
    password = request.form.get("password")
    
    if verify_password(password):
        session['verified'] = True
        return jsonify({"success": True, "message": "Erfolgreich verifiziert!"})
    else:
        return jsonify({"success": False, "message": "Falsches Passwort!"})
    
@app.route("/logout")
def logout():
    session.pop('verified', None)
    return jsonify({"success": True, "message": "Erfolgreich abgemeldet!"})

@app.route("/start-m-server", methods=["POST"])
def start_m_server():
    skript.write_to_log("M-Server starten gedrückt")
    skript.start_m_server()
    server_status()
    return "✅ In Arbeit(Start) Warte!"

@app.route("/stop-m-server", methods=["POST"])
def stop_m_server():
    skript.write_to_log("M-Server stoppen gedrückt")
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

    
@app.route('/docker-info')
def docker_info():
    """Gibt Roh-Docker-Informationen zurück"""
    try:
        import docker
        client = docker.from_env()
        container_name = os.getenv("Name_of_your_container")
        
        if not container_name:
            return jsonify({"error": "Container Name nicht gesetzt"})
        
        try:
            container = client.containers.get(container_name)
            container.reload()
            
            return jsonify({
                "container_name": container_name,
                "status": container.status,  # Der echte Docker-Status
                "state": container.attrs.get('State', {}),
                "id": container.id,
                "image": container.image.tags if container.image else "unknown"
            })
        except docker.errors.NotFound:
            return jsonify({"error": f"Container {container_name} nicht gefunden"})
        except docker.errors.APIError as e:
            return jsonify({"error": f"Docker API Error: {str(e)}"})
            
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"})

if __name__ == "__main__":
    app.run(debug=True)
