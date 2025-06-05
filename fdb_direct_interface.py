import os
import threading
import time
from collections import deque
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import fdb
from sqlalchemy.engine.url import make_url


class ConnectionPool:
    """Einfacher Thread-sicherer Verbindungspool für Firebird-Verbindungen."""

    def __init__(
        self, dsn: str, user: str, password: str, charset: str, max_size: int = 5
    ):
        self.dsn = dsn
        self.user = user
        self.password = password
        self.charset = charset
        self.max_size = max_size
        self._pool = deque()
        self._lock = threading.Lock()
        self._active_connections = 0

    def get_connection(self, timeout: float = 5.0) -> fdb.Connection:
        """Holt eine Verbindung aus dem Pool oder erstellt eine neue."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            with self._lock:
                if self._pool:
                    return self._pool.popleft()
                if self._active_connections < self.max_size:
                    self._active_connections += 1
                    return self._create_new_connection()
            time.sleep(0.1)
        raise TimeoutError("Timeout beim Warten auf eine Datenbankverbindung")

    def release_connection(self, conn: fdb.Connection):
        """Gibt eine Verbindung an den Pool zurück."""
        with self._lock:
            if len(self._pool) < self.max_size:
                self._pool.append(conn)
            else:
                try:
                    conn.close()
                except:
                    pass
                self._active_connections -= 1

    def _create_new_connection(self) -> fdb.Connection:
        """Erstellt eine neue Firebird-Verbindung."""
        # Versuche Server-Verbindung
        server_dsn = f"localhost:{self.dsn}"
        server_credentials = [
            (self.user, self.password),
            ("SYSDBA", "masterkey"),
            ("sysdba", "masterkey"),
            ("SYSDBA", "masterkey123"),
        ]

        for user, password in server_credentials:
            try:
                return fdb.connect(
                    dsn=server_dsn, user=user, password=password, charset=self.charset
                )
            except:
                continue

        # Fallback zu Embedded-Verbindung
        try:
            return fdb.connect(
                dsn=self.dsn,
                user=self.user,
                password=self.password,
                charset=self.charset,
            )
        except Exception as e:
            raise Exception(f"Weder Server- noch Embedded-Verbindung möglich: {e}")

    def close_all(self):
        """Schließt alle Verbindungen im Pool."""
        with self._lock:
            while self._pool:
                try:
                    self._pool.popleft().close()
                except:
                    pass
            self._active_connections = 0


class FDBDirectInterface:
    """
    Direkte Firebird-Datenbankschnittstelle über den fdb-Treiber.
    Umgeht SQLAlchemy-Sperrprobleme durch direkte Verbindungshandhabung.
    Implementiert einen Verbindungspool für bessere Performance.
    """

    def __init__(
        self,
        dsn: str,
        user: str = "SYSDBA",
        password: str = "masterkey",
        charset: str = "WIN1252",
        pool_size: int = 5,
    ):
        """
        Initialisiert die direkte FDB-Schnittstelle mit Verbindungspool.

        Args:
            dsn: Datenbankpfad (z.B. "/path/to/database.fdb")
            user: Benutzername (Standard: "SYSDBA")
            password: Passwort (Standard: "masterkey")
            charset: Zeichensatz (Standard: "WIN1252")
            pool_size: Maximale Anzahl an Verbindungen im Pool (Standard: 5)
        """
        self.dsn = dsn
        self.user = user
        self.password = password
        self.charset = charset

        # Firebird-Umgebungsvariablen setzen
        self._setup_firebird_environment()

        # Verbindungspool initialisieren
        self.pool = ConnectionPool(dsn, user, password, charset, pool_size)

        # Verbindung testen
        self._test_connection()

        # Metadaten-Cache initialisieren
        self.table_names_cache = None
        self.table_info_cache = {}

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
        lib_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "lib"))
        firebird_lib_path = os.path.join(lib_path, "libfbclient.so")
        if os.path.exists(firebird_lib_path):
            os.environ["FIREBIRD_LIBRARY_PATH"] = firebird_lib_path
            print(
                f"FDBDirectInterface: FIREBIRD_LIBRARY_PATH set to: {firebird_lib_path}"
            )

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
            print(
                f"✓ FDBDirectInterface: Verbindungstest erfolgreich. DB-ID: {result[0] if result else 'N/A'}"
            )
        except Exception as e:
            print(f"✗ FDBDirectInterface: Verbindungstest fehlgeschlagen: {e}")
            raise

    def _get_connection(self):
        """Holt eine Verbindung aus dem Pool."""
        return self.pool.get_connection()

    def _release_connection(self, conn):
        """Gibt eine Verbindung an den Pool zurück."""
        self.pool.release_connection(conn)

    def get_table_names(self, use_cache: bool = True) -> List[str]:
        """
        Gibt eine Liste aller Benutzertabellen zurück.
        Verwendet Caching für bessere Performance.

        Args:
            use_cache: Ob der Cache verwendet werden soll (Standard: True)

        Returns:
            Liste der Tabellennamen
        """
        if use_cache and self.table_names_cache is not None:
            return self.table_names_cache

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

            # Cache aktualisieren
            self.table_names_cache = tables
            return tables

        except Exception as e:
            print(f"Fehler beim Abrufen der Tabellennamen: {e}")
            return []
        finally:
            if conn:
                self._release_connection(conn)

    def get_table_info(self, table_names: List[str], use_cache: bool = True) -> str:
        """
        Gibt DDL-ähnliche Beschreibung für die angegebenen Tabellen zurück.
        Verwendet Caching für bessere Performance.

        Args:
            table_names: Liste der Tabellennamen
            use_cache: Ob der Cache verwendet werden soll (Standard: True)

        Returns:
            Formatierte Tabellenbeschreibung für LLM
        """
        if not table_names:
            return "Keine Tabellen angegeben."

        # Nicht gecachte Tabellen identifizieren
        uncached_tables = []
        cached_info = []

        if use_cache:
            for table_name in table_names:
                table_name_upper = table_name.upper().strip()
                if table_name_upper in self.table_info_cache:
                    cached_info.append(self.table_info_cache[table_name_upper])
                else:
                    uncached_tables.append(table_name_upper)
        else:
            uncached_tables = [table_name.upper().strip() for table_name in table_names]

        # Informationen für nicht gecachte Tabellen abrufen
        if uncached_tables:
            conn = None
            try:
                conn = self._get_connection()
                cursor = conn.cursor()

                # Batch-Abfrage für Spalteninformationen
                placeholders = ",".join(["?"] * len(uncached_tables))
                column_query = f"""
                SELECT
                    TRIM(rf.rdb$relation_name) as table_name,
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
                WHERE TRIM(rf.rdb$relation_name) IN ({placeholders})
                ORDER BY rf.rdb$relation_name, rf.rdb$field_position
                """

                cursor.execute(column_query, uncached_tables)
                columns = cursor.fetchall()

                # Batch-Abfrage für Primärschlüssel
                pk_query = f"""
                SELECT
                    TRIM(rc.rdb$relation_name) as table_name,
                    TRIM(sg.rdb$field_name) as column_name
                FROM rdb$relation_constraints rc
                JOIN rdb$index_segments sg ON rc.rdb$index_name = sg.rdb$index_name
                WHERE TRIM(rc.rdb$relation_name) IN ({placeholders})
                AND rc.rdb$constraint_type = 'PRIMARY KEY'
                ORDER BY rc.rdb$relation_name, sg.rdb$field_position
                """

                cursor.execute(pk_query, uncached_tables)
                pk_results = cursor.fetchall()

                # Ergebnisse gruppieren
                table_columns = {}
                for row in columns:
                    table_name = row[0].strip()
                    if table_name not in table_columns:
                        table_columns[table_name] = []
                    table_columns[table_name].append(row[1:])

                table_pks = {}
                for row in pk_results:
                    table_name = row[0].strip()
                    column_name = row[1].strip()
                    if table_name not in table_pks:
                        table_pks[table_name] = []
                    table_pks[table_name].append(column_name)

                # Tabellenbeschreibungen erstellen
                for table_name in uncached_tables:
                    table_desc = [f"\nTabelle: {table_name}"]
                    table_desc.append("Spalten:")

                    for col in table_columns.get(table_name, []):
                        col_name = col[0].strip() if col[0] else "UNKNOWN"
                        field_type = col[1]
                        field_length = col[2]
                        field_scale = col[3]
                        field_sub_type = col[4]
                        null_flag = col[5]
                        charset_id = col[6]
                        char_length = col[7]

                        data_type = self._get_firebird_data_type(
                            field_type,
                            field_length,
                            field_scale,
                            field_sub_type,
                            charset_id,
                            char_length,
                        )

                        nullable = "NOT NULL" if null_flag == 1 else "NULL"
                        table_desc.append(f"  - {col_name}: {data_type} ({nullable})")

                    if table_name in table_pks:
                        table_desc.append(
                            f"Primärschlüssel: {', '.join(table_pks[table_name])}"
                        )

                    table_info = "\n".join(table_desc)
                    self.table_info_cache[table_name] = table_info
                    cached_info.append(table_info)

            except Exception as e:
                print(f"Fehler beim Abrufen der Tabelleninformationen: {e}")
                return f"Fehler beim Abrufen der Tabelleninformationen: {e}"
            finally:
                if conn:
                    self._release_connection(conn)

        return "\n".join(cached_info)

    def _get_firebird_data_type(
        self,
        field_type: int,
        field_length: Optional[int],
        field_scale: Optional[int],
        field_sub_type: Optional[int],
        charset_id: Optional[int],
        char_length: Optional[int],
    ) -> str:
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
            261: "BLOB",
        }

        original_field_type_for_debug = field_type  # For logging
        try:
            # Ensure field_type is an integer for dictionary lookup
            lookup_field_type = int(field_type)
        except (ValueError, TypeError):
            lookup_field_type = field_type  # Keep original if conversion fails, will likely lead to UNKNOWN
            print(
                f"DEBUG FDB TYPE: Could not convert field_type '{original_field_type_for_debug}' to int. Using original for lookup."
            )

        base_type = type_mapping.get(
            lookup_field_type, f"UNKNOWN_TYPE_{original_field_type_for_debug}"
        )

        # Debugging log
        if "UNKNOWN_TYPE" in base_type:
            print(
                f"DEBUG FDB TYPE: Original field_type='{original_field_type_for_debug}', Lookup field_type='{lookup_field_type}', Result='{base_type}'"
            )

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
        if not query_upper.startswith("SELECT"):
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
                self._release_connection(conn)

    def get_column_names(self, query: str) -> List[str]:
        """
        Gibt die Spaltennamen für eine Abfrage zurück.

        Args:
            query: SQL-SELECT-Abfrage

        Returns:
            Liste der Spaltennamen
        """
        if not query.strip().upper().startswith("SELECT"):
            return []

        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Abfrage mit LIMIT 0 ausführen, um nur die Metadaten zu erhalten
            limited_query = f"SELECT FIRST 0 * FROM ({query}) AS subquery"
            cursor.execute(limited_query)

            # Spaltennamen aus der Cursor-Beschreibung extrahieren
            column_names = (
                [desc[0] for desc in cursor.description] if cursor.description else []
            )
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
                column_names = (
                    [desc[0] for desc in cursor.description]
                    if cursor.description
                    else []
                )
                cursor.close()
                return column_names
            except:
                return []
        finally:
            if conn:
                self._release_connection(conn)

    @classmethod
    def from_connection_string(
        cls, connection_string: str, pool_size: int = 5
    ) -> "FDBDirectInterface":
        """
        Erstellt eine FDBDirectInterface-Instanz aus einem SQLAlchemy-Connection-String.

        Args:
            connection_string: SQLAlchemy-Connection-String (z.B. "firebird+fdb://user:pass@//path/to/db.fdb")
            pool_size: Größe des Verbindungspools (Standard: 5)

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
                charset = url_info.query.get("charset", charset)

            print(f"FDBDirectInterface: Erstelle Instanz für DSN: {dsn}, User: {user}")

            return cls(
                dsn=dsn,
                user=user,
                password=password,
                charset=charset,
                pool_size=pool_size,
            )

        except Exception as e:
            print(f"Fehler beim Parsen des Connection-Strings: {e}")
            raise
