#!/usr/bin/env python3
"""
Test script to verify Firebird connection with sqlalchemy-firebird dialect.
"""

import os
import sys
from pathlib import Path

# Setzen der Umgebungsvariable für den Firebird-Client-Pfad
lib_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'lib'))
os.environ['FIREBIRD_LIBRARY_PATH'] = os.path.join(lib_path, 'libfbclient.so')
print(f"FIREBIRD_LIBRARY_PATH set to: {os.environ['FIREBIRD_LIBRARY_PATH']}")

# Firebird Umgebungsvariablen setzen
fb_temp_dir = Path("./fb_temp").absolute()
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

# Importiere sqlalchemy-firebird Dialekt
try:
    import sqlalchemy_firebird
    print("✓ sqlalchemy-firebird dialect imported successfully.")
except ImportError as e:
    print(f"✗ Could not import sqlalchemy-firebird: {e}")
    sys.exit(1)

try:
    import fdb
    print("✓ fdb imported successfully.")
except ImportError as e:
    print(f"✗ Could not import fdb: {e}")
    sys.exit(1)

from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool

def test_firebird_connection():
    """Test Firebird connection with different approaches."""
    
    # Test 1: Direct sqlalchemy-firebird dialect
    print("\n=== Test 1: sqlalchemy-firebird dialect ===")
    db_path = "./WINCASA2022.FDB"
    if not os.path.exists(db_path):
        print(f"✗ Database file not found: {db_path}")
        return False
    
    print(f"Database path: {db_path}")
    
    try:
        # Test 1a: Direct fdb.connect (like generate_yaml_ui.py)
        print("Testing direct fdb.connect...")
        test_conn = fdb.connect(
            dsn=db_path,
            user="SYSDBA",
            password="masterkey",
            charset="WIN1252"
        )
        print("✓ Direct fdb.connect successful")
        test_conn.close()
        
        # Test 1b: SQLAlchemy with custom creator
        print("Testing SQLAlchemy with custom creator...")
        def creator():
            return fdb.connect(
                dsn=db_path,
                user="SYSDBA",
                password="masterkey",
                charset="WIN1252"
            )

        engine = create_engine(
            "firebird://",
            creator=creator,
            poolclass=StaticPool,
            echo=False
        )
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 FROM RDB$DATABASE"))
            test_result = result.fetchone()
            print(f"✓ SQLAlchemy connection successful: {test_result}")
            return True
            
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_dialect_registration():
    """Test if the firebird dialect is properly registered."""
    print("\n=== Test 2: Dialect Registration ===")
    
    try:
        import importlib.metadata
        dialects_group = 'sqlalchemy.dialects'
        entry_points = []
        
        try:
            eps = importlib.metadata.entry_points(group=dialects_group)
            if eps:
                for ep in eps:
                    entry_points.append(ep.name)
        except AttributeError:
            all_eps = importlib.metadata.entry_points()
            if dialects_group in all_eps:
                for ep in all_eps[dialects_group]:
                    entry_points.append(ep.name)
        
        if entry_points:
            print(f"Found entry points for '{dialects_group}':")
            firebird_dialects = [ep for ep in entry_points if 'firebird' in ep.lower()]
            for ep_name in sorted(list(set(entry_points))):
                marker = "✓" if 'firebird' in ep_name.lower() else " "
                print(f"  {marker} {ep_name}")
            
            if firebird_dialects:
                print(f"✓ Found Firebird dialects: {firebird_dialects}")
                return True
            else:
                print("✗ No Firebird dialects found in entry points")
                return False
        else:
            print(f"✗ No entry points found for group '{dialects_group}'")
            return False
            
    except Exception as e:
        print(f"✗ Error checking dialect registration: {e}")
        return False

if __name__ == "__main__":
    print("Testing Firebird connection setup...")
    
    dialect_ok = test_dialect_registration()
    connection_ok = test_firebird_connection()
    
    if dialect_ok and connection_ok:
        print("\n✓ All tests passed! Firebird connection should work.")
        sys.exit(0)
    else:
        print("\n✗ Some tests failed. Check the output above.")
        sys.exit(1)