#!/usr/bin/env python3
import os
import sys
import tempfile
import shutil
from pathlib import Path

print("=== Final Firebird Connection Test ===")

# Setze Umgebungsvariablen vor dem Import
os.environ["FIREBIRD_LIBRARY_PATH"] = str(Path("./lib/libfbclient.so").absolute())

# Versuche bekannte Umgebungsvariablen für Firebird
temp_dir = Path("./fb_temp").absolute()
if temp_dir.exists():
    shutil.rmtree(temp_dir)
temp_dir.mkdir(exist_ok=True)

print(f"Temporäres Verzeichnis: {temp_dir}")

# Bekannte Umgebungsvariablen für temporäre Verzeichnisse
env_vars = [
    "FIREBIRD_TMP",
    "FIREBIRD_TEMP",
    "FIREBIRD_TMPDIR",
    "FB_TMPDIR",
    "TMPDIR",
    "TMP",
    "TEMP"
]

for var in env_vars:
    os.environ[var] = str(temp_dir)
    print(f"Setze {var}={str(temp_dir)}")

# Versuche, den Firebird-Driver zu importieren
try:
    print("\nImportiere Firebird Driver...")
    from firebird import driver

    # Versuche verschiedene Verbindungsmethoden
    database = "./WINCASA2022.FDB"
    print(f"Datenbank: {database}")

    # Ansatz 1: Standard connect mit verschiedenen Parametern
    print("\nVerbindungsversuch 1: Standard connect mit session_time_zone...")
    try:
        conn = driver.connect(
            database=database,
            user="SYSDBA",
            password="masterkey",
            charset="WIN1252",
            session_time_zone="local"  # Versuche, Zeitzoneninformationen anzugeben
        )
        print("✅ Verbindung erfolgreich!")
        conn.close()
    except Exception as e:
        print(f"❌ Fehler: {str(e)}")
    
    # Ansatz 2: Verwende keine_db_triggers-Parameter
    print("\nVerbindungsversuch 2: Mit no_db_triggers...")
    try:
        conn = driver.connect(
            database=database,
            user="SYSDBA",
            password="masterkey",
            charset="WIN1252",
            no_db_triggers=True  # Deaktiviere Datenbank-Trigger
        )
        print("✅ Verbindung erfolgreich!")
        conn.close()
    except Exception as e:
        print(f"❌ Fehler: {str(e)}")

    # Ansatz 3: Versuche, das FB_HOME zu setzen
    print("\nVerbindungsversuch 3: Mit FB_HOME...")
    os.environ["FB_HOME"] = str(temp_dir)
    try:
        conn = driver.connect(
            database=database,
            user="SYSDBA",
            password="masterkey",
            charset="WIN1252"
        )
        print("✅ Verbindung erfolgreich!")
        conn.close()
    except Exception as e:
        print(f"❌ Fehler: {str(e)}")
        
    # Ansatz 4: Setze ISC_USER und ISC_PASSWORD
    print("\nVerbindungsversuch 4: Mit ISC_USER und ISC_PASSWORD...")
    os.environ["ISC_USER"] = "SYSDBA"
    os.environ["ISC_PASSWORD"] = "masterkey"
    try:
        conn = driver.connect(
            database=database,
            charset="WIN1252"
        )
        print("✅ Verbindung erfolgreich!")
        conn.close()
    except Exception as e:
        print(f"❌ Fehler: {str(e)}")

except ImportError as ie:
    print(f"❌ Import fehlgeschlagen: {str(ie)}")
    
except Exception as e:
    print(f"❌ Allgemeiner Fehler: {str(e)}")

# Zeige alle gesetzten Umgebungsvariablen
print("\nAlle gesetzten Umgebungsvariablen:")
for key, value in sorted(os.environ.items()):
    if any(x in key.lower() for x in ["fire", "fb_", "tmp", "temp", "isc"]):
        print(f"  {key}: {value}")