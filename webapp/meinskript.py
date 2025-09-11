import os
import docker
from datetime import datetime

client = docker.from_env()

def get_container(container_name):
    """Holt einen spezifischen Container basierend auf dem Namen"""
    try:
        return client.containers.get(container_name)
    except docker.errors.NotFound:
        print(f"Container '{container_name}' nicht gefunden")
        return None
    except Exception as e:
        print(f"Fehler beim Zugriff auf Container: {e}")
        return None

def start_m_server(container_name):
    container = get_container(container_name)
    if container:
        container.start()
        write_to_log(f"{container_name} starten ausgeführt", container_name)
        return True
    return False

def stop_m_server(container_name):
    container = get_container(container_name)
    if container:
        container.stop()
        write_to_log(f"{container_name} stoppen ausgeführt", container_name)
        return True
    return False

def check_server_status(container_name):
    try:
        container = get_container(container_name)
        if not container:
            write_to_log(f"Container {container_name} nicht gefunden", container_name)
            return "error"
            
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
            return 'paused' if docker_status == 'paused' else 'stopped'
            
    except Exception as e:
        write_to_log(f"Container {container_name} nicht gefunden", container_name)
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
def write_to_log(message, container_name=None):
    # Erstelle container-spezifischen Log-Dateinamen
    if container_name:
        # Ersetze Sonderzeichen für Dateinamen
        safe_name = "".join(c for c in container_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        log_file = f"/scripts/logs/{safe_name}.log"
    else:
        log_file = "/scripts/output.log"
    
    # Stelle sicher, dass das Log-Verzeichnis existiert
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    zeitstempel = datetime.now().strftime("%H:%M:%S %d.%m.%Y")
    with open(log_file, "a") as f:
        f.write(f"{zeitstempel} - {message}\n")
    cleanup_logs(log_file, max_size_kb=100, keep_lines=20)
    print(message)  # Auch in Konsole ausgeben

def auto_container_stop():
    for container_name in get_container_names():
        if os.getenv("Auto_Stop") == "True":
            if check_server_status(container_name) == "running":
                current_time = datetime.now().strftime("%H:%M")
                if current_time == os.getenv("Auto_Stop_Time"):
                    stop_m_server(container_name)
                    write_to_log(f"Automatischer Stopp des Containers {container_name} um {current_time}", container_name)
        else:
            pass

def get_container_names():
    """Holt alle Container-Namen aus einer Liste in der .env"""
    containers_raw = os.getenv("CONTAINERS", "")
    if not containers_raw:
        return []
    
    # Liste erstellen, Leerzeichen entfernen
    container_names = [c.strip() for c in containers_raw.split(",") if c.strip()]
    return container_names

# Nur ausführen, wenn das Skript direkt aufgerufen wird
if __name__ == "__main__":
    # Teste die Funktionen
    names = get_container_names()
    print("Verfügbare Container:", names)
    
    if names:
        status = check_server_status(names[0])
        print(f"Status von {names[0]}: {status}")