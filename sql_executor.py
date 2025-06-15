#!/usr/bin/env python3
"""
WINCASA Layer 2 SQL Executor
Führt SQL-Queries gegen Firebird-Datenbank aus
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import firebird.driver
import pandas as pd

from config_loader import WincasaConfig

logger = logging.getLogger(__name__)

class WincasaSQLExecutor:
    """SQL-Ausführung für WINCASA Firebird-Datenbank"""
    
    def __init__(self):
        self.config = WincasaConfig()
        self.connection = None
        self.sql_templates = self._load_sql_templates()
    
    def _load_sql_templates(self) -> Dict[str, str]:
        """Lädt alle SQL-Templates aus den .sql Dateien"""
        sql_dir = Path(__file__).parent
        templates = {}
        
        # Lade SQL-Templates
        sql_files = [
            'enhanced_queries_layer2.sql',
            'enhanced_queries_layer2_buchungskonten.sql', 
            'enhanced_queries_layer2_owner_payments.sql',
            'enhanced_queries_layer2_part2.sql',
            'enhanced_queries_layer2_part3.sql',
            'enhanced_queries_layer2_phase1_fixes.sql',
            'enhanced_queries_layer2_phase2_financial.sql',
            'enhanced_queries_layer2_special_accounts.sql',
            'layer2_additional_queries.sql',
            'layer2_improved_queries.sql'
        ]
        
        for sql_file in sql_files:
            file_path = sql_dir / sql_file
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # Parse SQL queries (simple approach - split on comments)
                        queries = self._parse_sql_file(content)
                        templates.update(queries)
                except Exception as e:
                    logger.warning(f"Fehler beim Laden von {sql_file}: {e}")
        
        logger.info(f"SQL-Templates geladen: {len(templates)} Queries")
        return templates
    
    def _parse_sql_file(self, content: str) -> Dict[str, str]:
        """Parst SQL-Datei und extrahiert einzelne Queries"""
        queries = {}
        current_query = ""
        current_name = None
        
        for line in content.split('\n'):
            line = line.strip()
            
            # Erkenne Query-Namen aus Kommentaren
            if line.startswith('-- Query') or line.startswith('-- QUERY'):
                if current_name and current_query.strip():
                    queries[current_name] = current_query.strip()
                
                # Extrahiere Query-Namen
                if ':' in line:
                    current_name = line.split(':', 1)[1].strip()
                else:
                    # Fallback
                    current_name = line.replace('--', '').strip()
                current_query = ""
            
            elif not line.startswith('--') and line:
                current_query += line + '\n'
        
        # Letzte Query hinzufügen
        if current_name and current_query.strip():
            queries[current_name] = current_query.strip()
        
        return queries
    
    def connect(self) -> bool:
        """Verbindung zur Datenbank aufbauen"""
        try:
            if self.connection:
                return True
            
            db_config = self.config.get_db_config()
            
            self.connection = firebird.driver.connect(
                database=db_config['database'],
                user=db_config['user'],
                password=db_config['password'],
                charset=db_config['charset']
            )
            
            logger.info("Datenbank-Verbindung erfolgreich")
            return True
            
        except Exception as e:
            logger.error(f"Datenbank-Verbindung fehlgeschlagen: {e}")
            return False
    
    def execute_query(self, query: str, params: Dict[str, Any] = None) -> pd.DataFrame:
        """Führt SQL-Query aus und gibt DataFrame zurück"""
        if not self.connect():
            raise Exception("Keine Datenbank-Verbindung")
        
        try:
            cursor = self.connection.cursor()
            
            # Parameter ersetzen (einfache Implementierung)
            if params:
                for key, value in params.items():
                    placeholder = f":{key}"
                    if isinstance(value, str):
                        query = query.replace(placeholder, f"'{value}'")
                    else:
                        query = query.replace(placeholder, str(value))
            
            cursor.execute(query)
            
            # Ergebnisse holen
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            
            # DataFrame erstellen
            df = pd.DataFrame(rows, columns=columns)
            
            cursor.close()
            logger.info(f"Query erfolgreich ausgeführt: {len(df)} Zeilen")
            
            return df
            
        except Exception as e:
            logger.error(f"Fehler bei Query-Ausführung: {e}")
            raise
    
    def get_available_queries(self) -> List[str]:
        """Gibt Liste verfügbarer Query-Templates zurück"""
        return list(self.sql_templates.keys())
    
    def execute_template(self, template_name: str, params: Dict[str, Any] = None) -> pd.DataFrame:
        """Führt vordefiniertes SQL-Template aus"""
        if template_name not in self.sql_templates:
            raise ValueError(f"Unbekanntes Template: {template_name}")
        
        query = self.sql_templates[template_name]
        return self.execute_query(query, params)
    
    def search_tenants_by_address(self, address: str) -> pd.DataFrame:
        """Sucht Mieter nach Adresse"""
        # Einfache Adresssuche (kann erweitert werden)
        query = """
        SELECT DISTINCT 
            B.BEWNAME AS MIETER_NAME,
            B.BEWVNAME AS MIETER_VORNAME,
            B.BEWTELEFON AS TELEFON,
            B.BEWEMAIL AS EMAIL,
            O.OBEZ AS ADRESSE,
            W.WHGNR AS WOHNUNG,
            B.BVON AS MIETBEGINN,
            B.BWARN AS BETREUER
        FROM BEWOHNER B
        JOIN WOHNUNG W ON B.ONR = W.ONR AND B.ENR = W.ENR
        JOIN OBJEKTE O ON W.ONR = O.ONR
        WHERE O.OBEZ LIKE :address
          AND B.VENDE IS NULL
          AND O.ONR < 890
        ORDER BY O.OBEZ, W.WHGNR
        """
        
        # Adresse für LIKE-Suche vorbereiten
        search_address = f"%{address}%"
        
        return self.execute_query(query, {'address': search_address})
    
    def get_property_info(self, address: str) -> Dict[str, Any]:
        """Holt Immobilien-Info für Adresse"""
        query = """
        SELECT 
            O.ONR,
            O.OBEZ AS ADRESSE,
            O.OSTR AS STRASSE,
            O.OPLZ AS PLZ,
            O.OORT AS ORT,
            COUNT(W.ENR) AS ANZAHL_WOHNUNGEN,
            COUNT(B.BEWNAME) AS ANZAHL_MIETER
        FROM OBJEKTE O
        LEFT JOIN WOHNUNG W ON O.ONR = W.ONR
        LEFT JOIN BEWOHNER B ON W.ONR = B.ONR AND W.ENR = B.ENR AND B.VENDE IS NULL
        WHERE O.OBEZ LIKE :address
          AND O.ONR < 890
        GROUP BY O.ONR, O.OBEZ, O.OSTR, O.OPLZ, O.OORT
        """
        
        search_address = f"%{address}%"
        df = self.execute_query(query, {'address': search_address})
        
        if df.empty:
            return None
        
        return df.iloc[0].to_dict()
    
    def close(self):
        """Schließt Datenbank-Verbindung"""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("Datenbank-Verbindung geschlossen")
    
    def __enter__(self):
        """Context Manager Entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context Manager Exit"""
        self.close()


def test_sql_executor():
    """Test-Funktion für SQL Executor"""
    print("=== WINCASA SQL Executor Test ===")
    
    with WincasaSQLExecutor() as executor:
        # Verfügbare Queries anzeigen
        queries = executor.get_available_queries()
        print(f"\n✅ {len(queries)} SQL-Templates geladen")
        
        # Test: Suche nach Marienstr. 26
        print("\n🔍 Suche nach Mietern in Marienstr. 26...")
        try:
            tenants = executor.search_tenants_by_address("Marienstr. 26")
            print(f"Gefunden: {len(tenants)} Mieter")
            if not tenants.empty:
                print(tenants[['MIETER_NAME', 'MIETER_VORNAME', 'ADRESSE', 'WOHNUNG']].head())
        except Exception as e:
            print(f"❌ Fehler bei Mieter-Suche: {e}")
        
        # Test: Immobilien-Info
        print("\n🏠 Immobilien-Info für Marienstr. 26...")
        try:
            property_info = executor.get_property_info("Marienstr. 26")
            if property_info:
                print(f"ONR: {property_info['ONR']}")
                print(f"Adresse: {property_info['ADRESSE']}")
                print(f"Wohnungen: {property_info['ANZAHL_WOHNUNGEN']}")
                print(f"Mieter: {property_info['ANZAHL_MIETER']}")
            else:
                print("Keine Immobilie gefunden")
        except Exception as e:
            print(f"❌ Fehler bei Immobilien-Info: {e}")


if __name__ == "__main__":
    test_sql_executor()