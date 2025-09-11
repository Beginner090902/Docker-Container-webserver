from flask import Flask, redirect, render_template, request, jsonify, session, url_for
import sys
import os
sys.path.append("/scripts")
import meinskript as skript
from datetime import time
from apscheduler.schedulers.background import BackgroundScheduler
import docker


app = Flask(__name__)
app.secret_key = 'dein_geheimer_schluessel'


scheduler = BackgroundScheduler()
scheduler.add_job(skript.auto_container_stop, "interval", seconds=50)
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



skript.write_to_log("Web-Server gestartet")


@app.route("/")
def home():
    # Prüfen ob der Benutzer verifiziert ist
    if session.get('verified'):
        container_names = skript.get_container_names()
        return render_template("home.html", 
                               container_names=container_names, 
                               user="Verifizierter Benutzer", 
                               verified=True)
    else:
        return render_template("login.html")
    
@app.route("/server-übersicht/<container_name>")
def server_übersicht(container_name):
    if not session.get('verified'):
        return render_template("login.html")
    
    # Container-Status abfragen
    status = "unknown"

    status = skript.check_server_status(container_name)

    return render_template("server-übersicht.html", 
                           container_name=container_name,
                           container_status=status)
    
@app.route("/login", methods=["POST"])
def login():
    password = request.form.get("password")
    
    if verify_password(password):
        session['verified'] = True
        return jsonify({"success": True, "message": "Erfolgreich verifiziert!"})
    else:
        return jsonify({"success": False, "message": "Falsches Passwort!"})
    

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

@app.route('/server-status/<container_name>')
def server_status(container_name):
    # Hier prüfst du den Status des Servers
    if skript:
        status = skript.check_server_status(container_name)
    else:
        status = "error"
    
    return jsonify({"status": status, "container": container_name})

@app.route('/clear-logs/<container_name>', methods=['POST'])
def clear_logs(container_name):
    if not session.get('verified'):
        return jsonify({"error": "Nicht autorisiert"}), 401
    
    try:
        # Erstelle container-spezifischen Log-Dateinamen
        safe_name = "".join(c for c in container_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        log_file = f"/scripts/logs/{safe_name}.log"
        
        if os.path.exists(log_file):
            # Lösche die Log-Datei
            os.remove(log_file)
            return jsonify({"success": True, "message": f"Logs für {container_name} gelöscht"})
        else:
            return jsonify({"success": False, "message": f"Keine Log-Datei für {container_name} gefunden"})
    except Exception as e:
        return jsonify({"error": f"Fehler beim Löschen der Log-Datei: {str(e)}"}), 500

@app.route('/get-logs/<container_name>')
def get_logs(container_name):
    if not session.get('verified'):
        return jsonify({"error": "Nicht autorisiert"}), 401
    
    try:
        # Erstelle container-spezifischen Log-Dateinamen
        safe_name = "".join(c for c in container_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        log_file = f"/scripts/logs/{safe_name}.log"
        
        logs = []
        
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                logs = f.readlines()
        else:
            # Fallback zur allgemeinen Log-Datei für alte Einträge
            general_log_file = "/scripts/output.log"
            if os.path.exists(general_log_file):
                with open(general_log_file, 'r') as f:
                    # Filtere nur Einträge für diesen Container
                    all_logs = f.readlines()
                    logs = [log for log in all_logs if container_name in log]
    except Exception as e:
        return jsonify({"error": f"Fehler beim Lesen der Log-Datei: {str(e)}"}), 500

    return jsonify({"logs": logs, "container": container_name})

@app.route('/docker-info')
def docker_info():
    """Gibt Roh-Docker-Informationen zurück"""
    try:
        
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
    
@app.route("/start-container/<container_name>", methods=["POST"])
def start_container(container_name):
    if not session.get('verified'):
        return redirect(url_for('login'))
    
    if skript:
        skript.start_m_server(container_name)
    
    return redirect(url_for('server_übersicht', container_name=container_name))

@app.route("/stop-container/<container_name>", methods=["POST"])
def stop_container(container_name):
    if not session.get('verified'):
        return redirect(url_for('login'))
    
    if skript:
        skript.stop_m_server(container_name)
    
    return redirect(url_for('server_übersicht', container_name=container_name))

@app.route("/restart-container/<container_name>", methods=["POST"])
def restart_container(container_name):
    if not session.get('verified'):
        return redirect(url_for('login'))

    if skript:
        skript.stop_m_server(container_name)
        # Kurze Pause bevor der Container neu gestartet wird
        time.sleep(2)
        skript.start_m_server(container_name)
    
    return redirect(url_for('server_übersicht', container_name=container_name))

@app.route('/logout', methods=['POST'])
def logout():
    # Session löschen
    session.clear()
    # Zur Login-Seite weiterleiten
    return render_template("login.html")

if __name__ == "__main__":
    app.run(debug=True)
