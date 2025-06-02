import os
import sys
import logging
import importlib
import sqlalchemy
from sqlalchemy import create_engine
import fdb  # Frühzeitig importieren

# Ausführliches Logging aktivieren
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
logging.getLogger('sqlalchemy.dialects').setLevel(logging.DEBUG)

# Setze Umgebungsvariablen ähnlich wie in firebird_sql_agent.py
lib_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'lib'))
os.environ['FIREBIRD_LIBRARY_PATH'] = os.path.join(lib_path, 'libfbclient.so')
print(f"FIREBIRD_LIBRARY_PATH set to: {os.environ['FIREBIRD_LIBRARY_PATH']}")

# Firebird Temp-Verzeichnis setzen
fb_temp_dir = os.path.abspath("./fb_temp")
os.makedirs(fb_temp_dir, exist_ok=True)
os.environ["FIREBIRD_TMP"] = fb_temp_dir
os.environ["FIREBIRD_TEMP"] = fb_temp_dir
os.environ["FIREBIRD_TMPDIR"] = fb_temp_dir
os.environ["FB_TMPDIR"] = fb_temp_dir
os.environ["FB_HOME"] = os.path.abspath(".")
os.environ["FIREBIRD_HOME"] = os.path.abspath(".")

# Importieren und prüfen, ob der Firebird-Dialekt registriert ist
print("\n--- Prüfe verfügbare SQLAlchemy-Dialekte ---")
print(f"SQLAlchemy Version: {sqlalchemy.__version__}")
print(f"FDB Version: {fdb.__version__}")

# Versuche, das Dialektmodul direkt zu importieren
print("\n--- Versuche Dialektmodule direkt zu importieren ---")
try:
    import sqlalchemy.dialects.firebird
    print("✓ sqlalchemy.dialects.firebird konnte importiert werden")
except ImportError as e:
    print(f"✗ sqlalchemy.dialects.firebird konnte nicht importiert werden: {e}")

try:
    import sqlalchemy.dialects.firebird.fdb
    print("✓ sqlalchemy.dialects.firebird.fdb konnte importiert werden")
except ImportError as e:
    print(f"✗ sqlalchemy.dialects.firebird.fdb konnte nicht importiert werden: {e}")

# Prüfe alle verfügbaren Dialekte
print("\n--- Registrierte SQLAlchemy-Dialekte ---")
for name in sqlalchemy.dialects.__all__:
    print(f"Dialekt: {name}")
    dialect_module = importlib.import_module(f"sqlalchemy.dialects.{name}")
    if hasattr(dialect_module, "__all__"):
        print(f"  Treiber: {dialect_module.__all__}")

# Test 1: Verbindung mit firebird+fdb:// URL-Format
print("\n--- Test 1: Verbindung mit firebird+fdb:// URL ---")
try:
    # Verwende einen einfachen Test-Connection-String (anpassen)
    test_url = "firebird+fdb://sysdba:masterkey@localhost/test.fdb"
    engine = create_engine(test_url)
    print(f"✓ Engine erstellt mit URL: {test_url}")
    # Versuch einer Verbindung (wird wahrscheinlich fehlschlagen wegen Testdatenbank)
    try:
        with engine.connect() as conn:
            print("✓ Verbindung erfolgreich hergestellt")
    except Exception as e:
        print(f"✗ Verbindung fehlgeschlagen: {e}")
except Exception as e:
    print(f"✗ Engine-Erstellung fehlgeschlagen: {e}")

# Test 2: Verbindung mit firebird:// URL-Format (ohne +fdb)
print("\n--- Test 2: Verbindung mit firebird:// URL ---")
try:
    test_url = "firebird://sysdba:masterkey@localhost/test.fdb"
    engine = create_engine(test_url)
    print(f"✓ Engine erstellt mit URL: {test_url}")
    try:
        with engine.connect() as conn:
            print("✓ Verbindung erfolgreich hergestellt")
    except Exception as e:
        print(f"✗ Verbindung fehlgeschlagen: {e}")
except Exception as e:
    print(f"✗ Engine-Erstellung fehlgeschlagen: {e}")

# Test 3: Mit creator-Funktion und verschiedenen URL-Formaten
print("\n--- Test 3: Verwendung einer creator-Funktion ---")
for url_format in ["firebird+fdb://sysdba:masterkey@localhost/test.fdb", 
                  "firebird://sysdba:masterkey@localhost/test.fdb"]:
    print(f"\nTeste URL: {url_format}")
    try:
        def creator():
            return fdb.connect(
                dsn="test.fdb",
                user="sysdba",
                password="masterkey",
                charset="WIN1252"
            )
        
        engine = create_engine(
            url_format,
            creator=creator,
        )
        print(f"✓ Engine erstellt mit URL: {url_format} und creator-Funktion")
    except Exception as e:
        print(f"✗ Engine-Erstellung fehlgeschlagen: {e}")

# Test 4: Installation des SQLAlchemy-Firebird-Dialekts überprüfen
print("\n--- Test 4: Überprüfe SQLAlchemy-Firebird-Dialekt-Installation ---")
try:
    from pip._internal.operations.freeze import freeze
    
    print("Installierte Pakete, die mit SQLAlchemy oder Firebird zu tun haben:")
    for pkg in freeze():
        if "sqlalchemy" in pkg.lower() or "firebird" in pkg.lower() or "fdb" in pkg.lower():
            print(f"  {pkg}")
except ImportError:
    print("Konnte pip nicht importieren, um installierte Pakete zu überprüfen")

# Test 5: Pfade im sys.path überprüfen
print("\n--- Test 5: Python-Pfade überprüfen ---")
print("Relevante Pfade im sys.path:")
for path in sys.path:
    if "site-packages" in path or "dist-packages" in path:
        print(f"  {path}")

print("\nSQL Alchemy dialect entry points:")
try:
    import pkg_resources
    for entry_point in pkg_resources.iter_entry_points(group='sqlalchemy.dialects'):
        print(f"  {entry_point.name} -> {entry_point.module_name}")
except ImportError:
    print("Konnte pkg_resources nicht importieren")