def start_m_server():
    with open("/scripts/output.log", "a") as f:
        f.write("✅ M-Server gestartet!\n")
        print("M-Server starten ausgeführt")

def stop_m_server():
    with open("/scripts/output.log", "a") as f:
        f.write("✅ M-Server gestoppt!\n")
        print("M-Server stoppen ausgeführt")

def check_server_status():
    return "running"  # Beispielstatus, passe dies an deine Logik an