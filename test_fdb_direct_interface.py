#!/usr/bin/env python3
"""
Test-Skript für die direkte FDB-Schnittstelle.
Testet die FDBDirectInterface-Klasse unabhängig vom Langchain SQL Agent.
"""

import os
import sys
from pathlib import Path

# Setzen der Umgebungsvariable für den Firebird-Client-Pfad (wie in test_firebird_connection.py)
lib_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'lib'))
os.environ['FIREBIRD_LIBRARY_PATH'] = os.path.join(lib_path, 'libfbclient.so')
print(f"FIREBIRD_LIBRARY_PATH set to: {os.environ['FIREBIRD_LIBRARY_PATH']}")

# Firebird Umgebungsvariablen setzen
fb_temp_dir = Path("./fb_temp_test").absolute()
if not fb_temp_dir.exists():
    fb_temp_dir.mkdir(exist_ok=True, parents=True)

print(f"Setting Firebird environment variables. Temp dir: {fb_temp_dir}")
os.environ["FIREBIRD_TMP"] = str(fb_temp_dir)
os.environ["FIREBIRD_TEMP"] = str(fb_temp_dir)
os.environ["FIREBIRD_TMPDIR"] = str(fb_temp_dir)
os.environ["FB_TMPDIR"] = str(fb_temp_dir)
os.environ["TMPDIR"] = str(fb_temp_dir)
os.environ["TMP"] = str(fb_temp_dir)
os.environ["TEMP"] = str(fb_temp_dir)

project_root_for_fb_home = Path(os.path.dirname(__file__)).absolute()
os.environ["FB_HOME"] = str(project_root_for_fb_home)
os.environ["FIREBIRD_HOME"] = str(project_root_for_fb_home)
os.environ["FIREBIRD_LOCK"] = str(fb_temp_dir)

# Teste fdb-Import
try:
    import fdb
    print("✓ fdb imported successfully.")
except ImportError as e:
    print(f"✗ Could not import fdb: {e}")
    sys.exit(1)

# Füge das aktuelle Verzeichnis zum Python-Pfad hinzu
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fdb_direct_interface import FDBDirectInterface


def test_fdb_direct_interface():
    """Testet die FDBDirectInterface-Klasse."""
    
    print("=== Test der FDBDirectInterface ===")
    
    # Verbindungsparameter
    db_connection_string = "firebird+fdb://sysdba:masterkey@//home/projects/langchain_project/WINCASA2022.FDB"
    
    try:
        print(f"1. Initialisiere FDBDirectInterface mit: {db_connection_string}")
        fdb_interface = FDBDirectInterface.from_connection_string(db_connection_string)
        print("✓ FDBDirectInterface erfolgreich initialisiert")
        
        print("\n2. Teste get_table_names()...")
        table_names = fdb_interface.get_table_names()
        print(f"✓ {len(table_names)} Tabellen gefunden:")
        for i, table in enumerate(table_names[:10]):  # Zeige nur die ersten 10
            print(f"   {i+1}. {table}")
        if len(table_names) > 10:
            print(f"   ... und {len(table_names) - 10} weitere Tabellen")
        
        if table_names:
            # Teste get_table_info mit der ersten Tabelle
            test_table = table_names[0]
            print(f"\n3. Teste get_table_info() für Tabelle '{test_table}'...")
            table_info = fdb_interface.get_table_info([test_table])
            print("✓ Tabelleninformationen abgerufen:")
            print(table_info[:500] + "..." if len(table_info) > 500 else table_info)
            
            # Teste eine einfache SQL-Abfrage
            print(f"\n4. Teste run_sql() mit einfacher Abfrage auf '{test_table}'...")
            simple_query = f"SELECT FIRST 3 * FROM {test_table}"
            try:
                results = fdb_interface.run_sql(simple_query)
                print(f"✓ SQL-Abfrage erfolgreich ausgeführt. {len(results)} Zeilen zurückgegeben:")
                for i, row in enumerate(results):
                    print(f"   Zeile {i+1}: {row}")
            except Exception as e_sql:
                print(f"✗ Fehler bei SQL-Abfrage: {e_sql}")
            
            # Teste get_column_names
            print(f"\n5. Teste get_column_names() für Abfrage auf '{test_table}'...")
            try:
                column_names = fdb_interface.get_column_names(simple_query)
                print(f"✓ Spaltennamen abgerufen: {column_names}")
            except Exception as e_cols:
                print(f"✗ Fehler beim Abrufen der Spaltennamen: {e_cols}")
        
        # Teste spezifische BEWOHNER-Tabelle, falls vorhanden
        if "BEWOHNER" in table_names:
            print(f"\n6. Spezialtest für BEWOHNER-Tabelle...")
            bewohner_info = fdb_interface.get_table_info(["BEWOHNER"])
            print("✓ BEWOHNER-Tabelleninformationen:")
            print(bewohner_info)
            
            # Teste Abfrage auf BEWOHNER
            bewohner_query = "SELECT FIRST 5 * FROM BEWOHNER"
            try:
                bewohner_results = fdb_interface.run_sql(bewohner_query)
                print(f"✓ BEWOHNER-Abfrage erfolgreich. {len(bewohner_results)} Zeilen:")
                for i, row in enumerate(bewohner_results):
                    print(f"   Bewohner {i+1}: {row}")
            except Exception as e_bewohner:
                print(f"✗ Fehler bei BEWOHNER-Abfrage: {e_bewohner}")
        else:
            print("\n6. BEWOHNER-Tabelle nicht gefunden - überspringe spezifischen Test")
        
        print("\n=== Test der FDBDirectInterface abgeschlossen ===")
        return True
        
    except Exception as e:
        print(f"✗ Fehler beim Testen der FDBDirectInterface: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_connection_string_parsing():
    """Testet das Parsen verschiedener Connection-Strings."""
    
    print("\n=== Test des Connection-String-Parsings ===")
    
    test_strings = [
        "firebird+fdb://sysdba:masterkey@//home/projects/langchain_project/WINCASA2022.FDB",
        "firebird+fdb://user:pass@//path/to/database.fdb",
        "firebird+fdb://sysdba@//database.fdb",  # Ohne Passwort
    ]
    
    for i, conn_str in enumerate(test_strings, 1):
        print(f"\n{i}. Teste Connection-String: {conn_str}")
        try:
            # Nur das Parsen testen, nicht die tatsächliche Verbindung
            from sqlalchemy.engine.url import make_url
            url_info = make_url(conn_str)
            
            dsn = str(url_info.database)
            if dsn.startswith("//"):
                dsn = dsn[1:]
            
            user = url_info.username or "SYSDBA"
            password = url_info.password or "masterkey"
            
            print(f"   ✓ Geparst: DSN='{dsn}', User='{user}', Password='{'*' * len(password)}'")
            
        except Exception as e:
            print(f"   ✗ Fehler beim Parsen: {e}")
    
    print("\n=== Connection-String-Parsing-Test abgeschlossen ===")


if __name__ == "__main__":
    print("Starte Tests für die direkte FDB-Schnittstelle...\n")
    
    # Teste Connection-String-Parsing
    test_connection_string_parsing()
    
    # Teste die eigentliche FDB-Schnittstelle
    success = test_fdb_direct_interface()
    
    if success:
        print("\n🎉 Alle Tests erfolgreich abgeschlossen!")
        sys.exit(0)
    else:
        print("\n❌ Tests fehlgeschlagen!")
        sys.exit(1)