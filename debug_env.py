import os
import subprocess

print("=== DEBUGGING API KEY LOADING ===")
print(f"Aktuelles Verzeichnis: {os.getcwd()}")

# Funktion zum Abrufen des API-Schlüssels aus pass
def get_api_key_from_pass(key_name="OPENAI_API_KEY"):
    """
    Ruft den API-Schlüssel aus dem Password-Manager 'pass' ab.
    """
    try:
        result = subprocess.run(
            ["pass", "show", key_name],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Fehler beim Abrufen des API-Schlüssels aus pass: {e}")
        return None
    except Exception as e:
        print(f"Unerwarteter Fehler beim Zugriff auf pass: {e}")
        return None

# API-Schlüssel mit pass abrufen
print("\nVersuch mit pass:")
try:
    # Überprüfe, ob der pass-Befehl verfügbar ist
    try:
        subprocess.run(["pass", "--version"], capture_output=True, check=True)
        print("Pass ist korrekt installiert.")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️ WARNUNG: Der 'pass' Befehl scheint nicht verfügbar zu sein!")

    openai_api_key = get_api_key_from_pass()
    print(f"OPENAI_API_KEY gefunden (pass): {bool(openai_api_key)}")
    if openai_api_key:
        # Zeige nur die ersten und letzten 4 Zeichen des Schlüssels
        masked_key = openai_api_key[:4] + "*" * (len(openai_api_key) - 8) + openai_api_key[-4:]
        print(f"API-Schlüssel (maskiert): {masked_key}")
except Exception as e:
    print(f"Fehler beim Abrufen des API-Schlüssels: {e}")

# Zeige alle Umgebungsvariablen
print("\nAlle verfügbaren Umgebungsvariablen:")
for key, value in os.environ.items():
    if "key" in key.lower() or "api" in key.lower():
        print(f"{key}: {'*' * 5}")  # Zensierte Version für Sicherheit
    else:
        print(f"{key}: {value if len(value) < 20 else value[:20] + '...'}")