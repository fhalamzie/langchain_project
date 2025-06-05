# Implementierungsplan: Umstellung von .env auf Password-Manager "pass"

Dieser Plan beschreibt die Umstellung des Projekts von `.env`-Dateien auf den Password-Manager `pass` für die Verwaltung des OpenAI API-Schlüssels.

## Hintergrund

Derzeit wird der OpenAI API-Schlüssel aus einer `.env`-Datei im Pfad `/home/envs/openai.env` geladen. Die Umstellung erfolgt auf den Password-Manager "pass", in dem der API-Schlüssel unter dem Namen `OPENAI_API_KEY` gespeichert ist.

## Betroffene Dateien

1. `generate_yaml_ui.py`
2. `llm_interface.py`
3. `debug_env.py`

## Detaillierte Änderungen

### 1. Änderungen in `generate_yaml_ui.py`

#### Zu entfernende Zeilen:
```python
from dotenv import load_dotenv
# ...
# ==== SETUP – VERBESSERTE VERZEICHNISERSTELLUNG
# Lade .env-Datei aus dem angegebenen Pfad
env_path = "/home/envs/openai.env"  # Pfad zur .env-Datei
load_dotenv(dotenv_path=env_path)
openai_api_key = os.getenv("OPENAI_API_KEY")

if not openai_api_key:
    raise ValueError(f"OPENAI_API_KEY nicht gefunden. Bitte überprüfe, ob die Datei {env_path} existiert und den API-Schlüssel enthält.")
```

#### Zu ergänzende Zeilen:
```python
import subprocess

# ==== SETUP – VERBESSERTE VERZEICHNISERSTELLUNG
# API-Schlüssel aus dem Password-Manager 'pass' abrufen
def get_api_key_from_pass(key_name="OPENAI_API_KEY"):
    """
    Ruft den API-Schlüssel aus dem Password-Manager 'pass' ab.
    
    Args:
        key_name: Der Name des Eintrags im pass-Store (Standard: "OPENAI_API_KEY")
    
    Returns:
        str: Der abgerufene API-Schlüssel
        
    Raises:
        ValueError: Wenn der API-Schlüssel nicht abgerufen werden kann
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
        raise ValueError(f"Fehler beim Abrufen des API-Schlüssels aus pass: {e}")
    except Exception as e:
        raise ValueError(f"Unerwarteter Fehler beim Zugriff auf pass: {e}")

# API-Schlüssel mit pass abrufen
try:
    openai_api_key = get_api_key_from_pass()
except ValueError as e:
    raise ValueError(f"OPENAI_API_KEY konnte nicht aus dem Password-Manager 'pass' abgerufen werden: {e}")
```

### 2. Änderungen in `llm_interface.py`

#### Zu entfernende Zeilen:
```python
from dotenv import load_dotenv
# ...
def __init__(self):
    # Lade Umgebungsvariablen aus der spezifischen .env-Datei
    env_path = "/home/envs/openai.env"
    load_dotenv(dotenv_path=env_path)
    
    # Hole den OpenAI API-Schlüssel aus den Umgebungsvariablen
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError(f"OPENAI_API_KEY nicht gefunden. Bitte überprüfe, ob die Datei {env_path} existiert und den API-Schlüssel enthält.")
```

#### Zu ergänzende Zeilen:
```python
import subprocess
# ...
def __init__(self):
    # API-Schlüssel aus dem Password-Manager 'pass' abrufen
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
            raise ValueError(f"Fehler beim Abrufen des API-Schlüssels aus pass: {e}")
        except Exception as e:
            raise ValueError(f"Unerwarteter Fehler beim Zugriff auf pass: {e}")
    
    # API-Schlüssel mit pass abrufen
    try:
        openai_api_key = get_api_key_from_pass()
    except ValueError as e:
        raise ValueError(f"OPENAI_API_KEY konnte nicht aus dem Password-Manager 'pass' abgerufen werden: {e}")
```

### 3. Änderungen in `debug_env.py`

#### Zu entfernende Zeilen:
```python
from dotenv import load_dotenv
# ...
# Versuch 1: Standard .env im aktuellen Verzeichnis
print("\nVersuch 1: Standardpfad")
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
print(f"OPENAI_API_KEY gefunden (Standard): {bool(openai_api_key)}")

# Versuch 2: Expliziter Pfad
print("\nVersuch 2: Expliziter Pfad")
env_path = "/home/envs/openai.env"
print(f"Lade .env von: {env_path}")
load_dotenv(dotenv_path=env_path)
openai_api_key = os.getenv("OPENAI_API_KEY")
print(f"OPENAI_API_KEY gefunden (explizit): {bool(openai_api_key)}")

# Prüfe, ob die Datei existiert
print(f"\nPrüfe, ob die Datei existiert: {env_path}")
print(f"Datei existiert: {os.path.exists(env_path)}")
if os.path.exists(env_path):
    try:
        with open(env_path, 'r') as f:
            content = f.read()
            print(f"Dateiinhalt (erste 100 Zeichen): {content[:100]}...")
    except Exception as e:
        print(f"Fehler beim Lesen der Datei: {e}")
else:
    print("Datei existiert nicht!")
```

#### Zu ergänzende Zeilen:
```python
import subprocess
# ...
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
    openai_api_key = get_api_key_from_pass()
    print(f"OPENAI_API_KEY gefunden (pass): {bool(openai_api_key)}")
    if openai_api_key:
        # Zeige nur die ersten und letzten 4 Zeichen des Schlüssels
        masked_key = openai_api_key[:4] + "*" * (len(openai_api_key) - 8) + openai_api_key[-4:]
        print(f"API-Schlüssel (maskiert): {masked_key}")
except Exception as e:
    print(f"Fehler beim Abrufen des API-Schlüssels: {e}")
```

## Zusammenfassung der Änderungen

1. **Entfernen der Abhängigkeit von python-dotenv**:
   - Die Imports von `dotenv` entfernen
   - Keine `.env`-Dateien mehr laden
   
2. **Hinzufügen der "pass"-Integration**:
   - Import von `subprocess` zum Ausführen des `pass`-Befehls
   - Implementierung der `get_api_key_from_pass`-Funktion in jeder relevanten Datei
   - Direkte Fehlerausgabe, wenn der Schlüssel nicht abgerufen werden kann
   
3. **Fehlerbehandlung**:
   - Klare Fehlermeldungen, wenn der API-Schlüssel nicht über `pass` abgerufen werden kann
   - Kein Fallback zur `.env`-Datei
   - Programm wird beendet, wenn der Schlüssel nicht verfügbar ist

## Umsetzungsreihenfolge

1. Zunächst die Änderungen in `generate_yaml_ui.py` vornehmen und testen
2. Dann die Änderungen in `llm_interface.py` vornehmen und testen
3. Zuletzt die Änderungen in `debug_env.py` vornehmen

## Voraussetzungen

- Der Password-Manager `pass` muss auf dem System installiert sein
- Ein Eintrag mit dem Namen "OPENAI_API_KEY" muss in `pass` vorhanden sein und den API-Schlüssel enthalten