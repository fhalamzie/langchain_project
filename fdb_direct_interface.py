import os
import fdb
from typing import List, Tuple, Dict, Any, Optional
from pathlib import Path
from sqlalchemy.engine.url import make_url


class FDBDirectInterface:
    """
    Direkte Firebird-Datenbankschnittstelle über den fdb-Treiber.
    Umgeht SQLAlchemy-Sperrprobleme durch direkte Verbindungshandhabung.
    """
    
    def __init__(self, dsn: str, user: str = "SYSDBA", password: str = "masterkey", charset: str = "WIN1252"):
        """
        Initialisiert die direkte FDB-Schnittstelle.
        
        Args:
            dsn: Datenbankpfad (z.B. "/path/to/database.fdb")
            user: Benutzername (Standard: "SYSDBA")
            password: Passwort (Standard: "masterkey")
            charset: Zeichensatz (Standard: "WIN1252")
        """
        self.dsn = dsn
        self.user = user
        self.password = password
        self.charset = charset
        
        # Firebird-Umgebungsvariablen setzen
        self._setup_firebird_environment()
        
        # Verbindung testen
        self._test_connection()
    
    def _setup_firebird_environment(self):
        """Setzt die notwendigen Firebird-Umgebungsvariablen."""
        # Temporäres Verzeichnis für Firebird erstellen
        fb_temp_dir = Path("./fb_temp_direct").absolute()
        if not fb_temp_dir.exists():
            fb_temp_dir.mkdir(exist_ok=True, parents=True)
        
        # Umgebungsvariablen setzen
        os.environ["FIREBIRD_TMP"] = str(fb_temp_dir)
        os.environ["FIREBIRD_TEMP"] = str(fb_temp_dir)
        os.environ["FB_TMPDIR"] = str(fb_temp_dir)
        os.environ["FIREBIRD_LOCK"] = str(fb_temp_dir)
        os.environ["FB_HOME"] = str(fb_temp_dir)
        os.environ["FIREBIRD_HOME"] = str(fb_temp_dir)
        
        # Firebird-Client-Bibliothek-Pfad setzen
        lib_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lib'))
        firebird_lib_path = os.path.join(lib_path, 'libfbclient.so')
        if os.path.exists(firebird_lib_path):
            os.environ['FIREBIRD_LIBRARY_PATH'] = firebird_lib_path
            print(f"FDBDirectInterface: FIREBIRD_LIBRARY_PATH set to: {firebird_lib_path}")
        
        print(f"FDBDirectInterface: Firebird temp directory set to: {fb_temp_dir}")
    
    def _test_connection(self):
        """Testet die Datenbankverbindung."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT rdb$relation_id FROM rdb$database")
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            print(f"✓ FDBDirectInterface: Verbindungstest erfolgreich. DB-ID: {result[0] if result else 'N/A'}")
        except Exception as e:
            print(f"✗ FDBDirectInterface: Verbindungstest fehlgeschlagen: {e}")
            raise
    
    def _get_connection(self):
        """Erstellt eine neue Datenbankverbindung."""
        try:
            # Versuche zuerst Server-Verbindung mit verschiedenen Anmeldeinformationen
            server_dsn = f"localhost:{self.dsn}"
            print(f"FDBDirectInterface: Versuche Server-Verbindung mit DSN: {server_dsn}")
            
            # Versuche verschiedene Benutzer/Passwort-Kombinationen für den Server
            server_credentials = [
                (self.user, self.password),
                ("SYSDBA", "masterkey"),
                ("sysdba", "masterkey"),
                ("SYSDBA", "masterkey123"),
            ]
            
            for user, password in server_credentials:
                try:
                    print(f"FDBDirectInterface: Versuche Server-Anmeldung mit User: {user}")
                    return fdb.connect(
                        dsn=server_dsn,
                        user=user,
                        password=password,
                        charset=self.charset
                    )
                except Exception as e_cred:
                    print(f"Server-Anmeldung mit {user} fehlgeschlagen: {e_cred}")
                    continue
            
            print("Alle Server-Anmeldeversuche fehlgeschlagen")
            
        except Exception as e_server:
            print(f"Server-Verbindung generell fehlgeschlagen: {e_server}")
        
        # Fallback zu direkter Embedded-Verbindung (wird wahrscheinlich fehlschlagen)
        try:
            print(f"FDBDirectInterface: Versuche Embedded-Verbindung mit DSN: {self.dsn}")
            return fdb.connect(
                dsn=self.dsn,
                user=self.user,
                password=self.password,
                charset=self.charset
            )
        except Exception as e_embedded:
            print(f"Embedded-Verbindung fehlgeschlagen: {e_embedded}")
            raise Exception(f"Weder Server- noch Embedded-Verbindung möglich. Letzter Fehler: {e_embedded}")
    
    def get_table_names(self) -> List[str]:
        """
        Gibt eine Liste aller Benutzertabellen zurück.
        
        Returns:
            Liste der Tabellennamen
        """
        query = """
        SELECT TRIM(rdb$relation_name) as table_name
        FROM rdb$relations
        WHERE rdb$view_blr IS NULL 
        AND (rdb$system_flag IS NULL OR rdb$system_flag = 0)
        AND rdb$relation_name NOT STARTING WITH 'RDB$'
        AND rdb$relation_name NOT STARTING WITH 'MON$'
        ORDER BY rdb$relation_name
        """
        
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query)
            
            tables = []
            for row in cursor.fetchall():
                table_name = row[0].strip() if row[0] else ""
                if table_name:
                    tables.append(table_name)
            
            cursor.close()
            print(f"FDBDirectInterface: {len(tables)} Benutzertabellen gefunden")
            return tables
            
        except Exception as e:
            print(f"Fehler beim Abrufen der Tabellennamen: {e}")
            return []
        finally:
            if conn:
                conn.close()
    
    def get_table_info(self, table_names: List[str]) -> str:
        """
        Gibt DDL-ähnliche Beschreibung für die angegebenen Tabellen zurück.
        
        Args:
            table_names: Liste der Tabellennamen
            
        Returns:
            Formatierte Tabellenbeschreibung für LLM
        """
        if not table_names:
            return "Keine Tabellen angegeben."
        
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            table_info_parts = []
            
            for table_name in table_names:
                table_name_upper = table_name.upper().strip()
                
                # Spalteninformationen abrufen
                column_query = """
                SELECT 
                    TRIM(rf.rdb$field_name) as column_name,
                    TRIM(f.rdb$field_type) as field_type,
                    f.rdb$field_length,
                    f.rdb$field_scale,
                    f.rdb$field_sub_type,
                    rf.rdb$null_flag,
                    TRIM(f.rdb$character_set_id) as charset_id,
                    f.rdb$character_length
                FROM rdb$relation_fields rf
                JOIN rdb$fields f ON rf.rdb$field_source = f.rdb$field_name
                WHERE TRIM(rf.rdb$relation_name) = ?
                ORDER BY rf.rdb$field_position
                """
                
                cursor.execute(column_query, (table_name_upper,))
                columns = cursor.fetchall()
                
                if not columns:
                    table_info_parts.append(f"Tabelle {table_name_upper}: Keine Spalten gefunden oder Tabelle existiert nicht.")
                    continue
                
                # Tabellenbeschreibung erstellen
                table_desc = [f"\nTabelle: {table_name_upper}"]
                table_desc.append("Spalten:")
                
                for col in columns:
                    col_name = col[0].strip() if col[0] else "UNKNOWN"
                    field_type = col[1]
                    field_length = col[2]
                    field_scale = col[3]
                    field_sub_type = col[4]
                    null_flag = col[5]
                    charset_id = col[6]
                    char_length = col[7]
                    
                    # Datentyp bestimmen
                    data_type = self._get_firebird_data_type(
                        field_type, field_length, field_scale, 
                        field_sub_type, charset_id, char_length
                    )
                    
                    # NULL/NOT NULL
                    nullable = "NOT NULL" if null_flag == 1 else "NULL"
                    
                    table_desc.append(f"  - {col_name}: {data_type} ({nullable})")
                
                # Primärschlüssel abrufen
                pk_query = """
                SELECT TRIM(sg.rdb$field_name) as column_name
                FROM rdb$relation_constraints rc
                JOIN rdb$index_segments sg ON rc.rdb$index_name = sg.rdb$index_name
                WHERE TRIM(rc.rdb$relation_name) = ?
                AND rc.rdb$constraint_type = 'PRIMARY KEY'
                ORDER BY sg.rdb$field_position
                """
                
                cursor.execute(pk_query, (table_name_upper,))
                pk_columns = [row[0].strip() for row in cursor.fetchall()]
                
                if pk_columns:
                    table_desc.append(f"Primärschlüssel: {', '.join(pk_columns)}")
                
                table_info_parts.append("\n".join(table_desc))
            
            cursor.close()
            return "\n".join(table_info_parts)
            
        except Exception as e:
            print(f"Fehler beim Abrufen der Tabelleninformationen: {e}")
            return f"Fehler beim Abrufen der Tabelleninformationen: {e}"
        finally:
            if conn:
                conn.close()
    
    def _get_firebird_data_type(self, field_type: int, field_length: Optional[int], 
                               field_scale: Optional[int], field_sub_type: Optional[int],
                               charset_id: Optional[int], char_length: Optional[int]) -> str:
        """
        Konvertiert Firebird-interne Feldtypen zu lesbaren Datentypen.
        
        Args:
            field_type: Firebird-Feldtyp-ID
            field_length: Feldlänge
            field_scale: Feldskala
            field_sub_type: Feldsubtyp
            charset_id: Zeichensatz-ID
            char_length: Zeichenlänge
            
        Returns:
            Lesbarer Datentyp-String
        """
        # Firebird-Datentyp-Mapping
        type_mapping = {
            7: "SMALLINT",
            8: "INTEGER", 
            10: "FLOAT",
            12: "DATE",
            13: "TIME",
            14: "CHAR",
            16: "BIGINT",
            27: "DOUBLE PRECISION",
            35: "TIMESTAMP",
            37: "VARCHAR",
            261: "BLOB"
        }
        
        base_type = type_mapping.get(field_type, f"UNKNOWN_TYPE_{field_type}")
        
        # Spezielle Behandlung für verschiedene Typen
        if field_type == 14:  # CHAR
            length = char_length if char_length else field_length
            if length:
                try:
                    # Vorsichtige Behandlung der Länge - ignoriere nicht-numerische Werte
                    length_val = int(length) if str(length).isdigit() else None
                    if length_val and length_val > 0:
                        return f"CHAR({length_val})"
                except (ValueError, TypeError):
                    pass
            return "CHAR"
            
        elif field_type == 37:  # VARCHAR
            length = char_length if char_length else field_length
            if length:
                try:
                    # Vorsichtige Behandlung der Länge - ignoriere nicht-numerische Werte
                    length_val = int(length) if str(length).isdigit() else None
                    if length_val and length_val > 0:
                        return f"VARCHAR({length_val})"
                except (ValueError, TypeError):
                    pass
            return "VARCHAR"
            
        elif field_type == 261:  # BLOB
            if field_sub_type == 1:
                return "BLOB SUB_TYPE TEXT"
            elif field_sub_type == 0:
                return "BLOB SUB_TYPE BINARY"
            else:
                return f"BLOB SUB_TYPE {field_sub_type}"
                
        elif field_type in [7, 8, 16] and field_scale and field_scale < 0:
            # NUMERIC/DECIMAL mit Skala
            precision = field_length if field_length else 18
            scale = abs(field_scale)
            return f"NUMERIC({precision},{scale})"
        
        return base_type
    
    def run_sql(self, query: str) -> List[Tuple]:
        """
        Führt eine SQL-SELECT-Abfrage aus und gibt die Ergebnisse zurück.
        
        Args:
            query: SQL-SELECT-Abfrage
            
        Returns:
            Liste von Tupeln mit den Abfrageergebnissen
        """
        if not query.strip():
            return []
        
        # Sicherheitscheck: Nur SELECT-Abfragen erlauben
        query_upper = query.strip().upper()
        if not query_upper.startswith('SELECT'):
            raise ValueError("Nur SELECT-Abfragen sind erlaubt")
        
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            print(f"FDBDirectInterface: Führe SQL aus: {query[:100]}...")
            cursor.execute(query)
            
            results = cursor.fetchall()
            cursor.close()
            
            print(f"FDBDirectInterface: {len(results)} Zeilen zurückgegeben")
            return results
            
        except Exception as e:
            print(f"Fehler beim Ausführen der SQL-Abfrage: {e}")
            print(f"Abfrage war: {query}")
            raise
        finally:
            if conn:
                conn.close()
    
    def get_column_names(self, query: str) -> List[str]:
        """
        Gibt die Spaltennamen für eine Abfrage zurück.
        
        Args:
            query: SQL-SELECT-Abfrage
            
        Returns:
            Liste der Spaltennamen
        """
        if not query.strip().upper().startswith('SELECT'):
            return []
        
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Abfrage mit LIMIT 0 ausführen, um nur die Metadaten zu erhalten
            limited_query = f"SELECT FIRST 0 * FROM ({query}) AS subquery"
            cursor.execute(limited_query)
            
            # Spaltennamen aus der Cursor-Beschreibung extrahieren
            column_names = [desc[0] for desc in cursor.description] if cursor.description else []
            cursor.close()
            
            return column_names
            
        except Exception as e:
            print(f"Fehler beim Abrufen der Spaltennamen: {e}")
            # Fallback: Versuche die ursprüngliche Abfrage mit FIRST 1
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                fallback_query = query.replace("SELECT", "SELECT FIRST 1", 1)
                cursor.execute(fallback_query)
                column_names = [desc[0] for desc in cursor.description] if cursor.description else []
                cursor.close()
                return column_names
            except:
                return []
        finally:
            if conn:
                conn.close()

    @classmethod
    def from_connection_string(cls, connection_string: str) -> 'FDBDirectInterface':
        """
        Erstellt eine FDBDirectInterface-Instanz aus einem SQLAlchemy-Connection-String.
        
        Args:
            connection_string: SQLAlchemy-Connection-String (z.B. "firebird+fdb://user:pass@//path/to/db.fdb")
            
        Returns:
            FDBDirectInterface-Instanz
        """
        try:
            url_info = make_url(connection_string)
            
            # DSN aus der URL extrahieren
            dsn = str(url_info.database)
            if dsn.startswith("//"):
                dsn = dsn[1:]  # Entferne führende "//"
            
            user = url_info.username or "SYSDBA"
            password = url_info.password or "masterkey"
            
            # Charset aus Query-Parametern extrahieren, falls vorhanden
            charset = "WIN1252"
            if url_info.query:
                charset = url_info.query.get('charset', charset)
            
            print(f"FDBDirectInterface: Erstelle Instanz für DSN: {dsn}, User: {user}")
            
            return cls(dsn=dsn, user=user, password=password, charset=charset)
            
        except Exception as e:
            print(f"Fehler beim Parsen des Connection-Strings: {e}")
            raise