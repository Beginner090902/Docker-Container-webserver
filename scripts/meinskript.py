import app as appfunctions

def start_m_server():
    appfunctions.write_to_log("M-Server starten ausgeführt")

def stop_m_server():
    appfunctions.write_to_log("M-Server stoppen ausgeführt")

def check_server_status():
    return "running"  # Beispielstatus, passe dies an deine Logik an