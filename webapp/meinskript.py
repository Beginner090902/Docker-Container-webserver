import os
import docker
from datetime import datetime

client = docker.from_env()
db_container_name = os.getenv("Name_of_your_container")
container = client.containers.get(db_container_name)

def start_m_server():
    container.start()
    write_to_log("M-Server starten ausgeführt")

def stop_m_server():
    container.stop()
    write_to_log("M-Server stoppen ausgeführt")

def check_server_status():
    try:
        container.reload()
        docker_status = container.status
        health_status = None
        
        # HealthCheck Status auslesen falls verfügbar
        try:
            health_info = container.attrs.get('State', {}).get('Health', {})
            health_status = health_info.get('Status', '')
        except:
            pass
        
        # Status-Logik mit HealthCheck
        if docker_status == 'running':
            if health_status == 'starting':
                return 'starting'
            elif health_status == 'healthy':
                return 'running'
            elif health_status == 'unhealthy':
                return 'unhealthy'
            else:
                # Kein HealthCheck konfiguriert oder kein Status
                return 'running'
        else:
            return docker_status
            
    except Exception as e:
        write_to_log(f"FEHLER beim Status abfragen: {e}")
        return "error"

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