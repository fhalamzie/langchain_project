#!/usr/bin/env python3
"""
WINCASA Layer 4 JSON Loader
Lädt die vorexportierten Layer 4 JSON-Dateien für die Streamlit-App
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

class Layer4JSONLoader:
    """Lädt Layer 4 JSON-Exporte aus dem konfigurierten exports/ Verzeichnis"""
    
    def __init__(self):
        # Load path configuration
        import json as config_json
        with open('config/sql_paths.json', 'r') as f:
            path_config = config_json.load(f)
        
        # Path to Layer 4 JSON exports
        self.json_dir = Path(path_config['json_exports_dir'])
        self.data_cache = {}
        
        # Load metadata
        self.load_metadata()
        
    def load_metadata(self):
        """Lädt die Export-Zusammenfassung"""
        try:
            summary_path = self.json_dir / "_export_summary.json"
            if summary_path.exists():
                with open(summary_path, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
            else:
                self.metadata = {}
        except Exception as e:
            logger.error(f"Fehler beim Laden der Metadaten: {e}")
            self.metadata = {}
    
    def list_available_queries(self) -> List[Dict[str, Any]]:
        """Listet alle verfügbaren Layer 4 JSON-Exporte"""
        queries = []
        
        # Definiere die Query-Kategorien basierend auf Layer 4
        categories = {
            'stammdaten': {
                '01_eigentuemer': 'Eigentümer mit Banking & Portfolio',
                '03_aktuelle_mieter': 'Aktuelle Mieterbeziehungen',
                '04_alle_mieter': 'Historische Mieterdaten',
                '05_objekte': 'Immobilienportfolio',
                '07_wohnungen': 'Wohnungsdetails mit Belegung'
            },
            'finanzen': {
                '09_konten': 'Kontenplan mit Salden',
                '10_eigentuemer_konten': 'Eigentümerkonten-Details',
                '11_mieter_konten': 'Mieterkonten-Tracking',
                '12_bank_konten': 'Bankverbindungen',
                '26_detaillierte_buchungen': 'Komplette Transaktionshistorie',
                '27_konten_saldenliste': 'Kontensaldenliste',
                '28_nebenkostenkonten_matrix': 'Nebenkosten-Aufschlüsselung'
            },
            'governance': {
                '13_weg_eigentuemer': 'WEG-Eigentümerstruktur',
                '14_eigentuemer_op': 'Offene Posten Eigentümer',
                '16_beiraete': 'Beiratsverwaltung',
                '17_beschluesse': 'Beschlussverfolgung',
                '18_versammlungen': 'Versammlungsverwaltung',
                '19_etv_presence': 'Versammlungspräsenz'
            },
            'analysen': {
                '20_monatliche_mieteinnahmen': 'Monatliche Mieteinnahmen',
                '21_forderungsalterung': 'Forderungsalterung',
                '22_leerstandsanalyse': 'Leerstandsanalyse',
                '23_instandhaltungskosten': 'Instandhaltungskosten',
                '24_ruecklagenanalyse': 'Rücklagenanalyse',
                '25_objektbezogene_sachkonten': 'Objektbezogene GL-Konten'
            },
            'spezial': {
                '29_eigentuemer_zahlungshistorie': 'Zahlungshistorie (parametrisiert)',
                '30_weg_zahlungsuebersicht': 'WEG-Zahlungsübersicht (parametrisiert)',
                '31_durchlaufende_posten': 'Durchlaufende Posten',
                '32_sonderentnahmen': 'Sonderentnahmen',
                '33_ruecklagen_management': 'Rücklagen-Management',
                '34_spezielle_kontenklassen': 'Spezielle Kontenklassen',
                '35_buchungskonten_uebersicht': 'Buchungskonten-Übersicht (parametrisiert)'
            }
        }
        
        # Erstelle Query-Liste mit Metadaten
        for category, queries_dict in categories.items():
            for query_name, description in queries_dict.items():
                json_file = self.json_dir / f"{query_name}.json"
                if json_file.exists():
                    # Lade Metadaten aus der Datei
                    try:
                        with open(json_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            query_info = data.get('query_info', {})
                            summary = data.get('summary', {})
                            
                            queries.append({
                                'name': query_name,
                                'category': category,
                                'description': description,
                                'file': json_file.name,
                                'rows': summary.get('row_count', 0),
                                'generated': query_info.get('generated', 'N/A'),
                                'exists': True
                            })
                    except Exception as e:
                        logger.error(f"Fehler beim Laden von {json_file}: {e}")
                else:
                    queries.append({
                        'name': query_name,
                        'category': category,
                        'description': description,
                        'file': f"{query_name}.json",
                        'rows': 0,
                        'exists': False
                    })
        
        return queries
    
    def load_json_data(self, query_name: str) -> Optional[Dict[str, Any]]:
        """Lädt eine spezifische JSON-Datei"""
        # Check cache first
        if query_name in self.data_cache:
            return self.data_cache[query_name]
        
        json_file = self.json_dir / f"{query_name}.json"
        if not json_file.exists():
            logger.warning(f"JSON-Datei nicht gefunden: {json_file}")
            return None
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.data_cache[query_name] = data
                return data
        except Exception as e:
            logger.error(f"Fehler beim Laden von {json_file}: {e}")
            return None
    
    def search_in_json(self, search_term: str, max_results: int = 100) -> List[Dict[str, Any]]:
        """Sucht in allen JSON-Dateien nach einem Begriff"""
        results = []
        search_lower = search_term.lower()
        
        # Durchsuche alle verfügbaren Queries
        for query_info in self.list_available_queries():
            if not query_info['exists']:
                continue
                
            query_name = query_info['name']
            data = self.load_json_data(query_name)
            
            if data and 'data' in data:
                for row in data['data']:
                    # Suche in allen Feldern
                    if any(search_lower in str(value).lower() for value in row.values()):
                        results.append({
                            'query': query_name,
                            'category': query_info['category'],
                            'data': row
                        })
                        
                        if len(results) >= max_results:
                            return results
        
        return results
    
    def get_summary_statistics(self) -> Dict[str, Any]:
        """Gibt eine Zusammenfassung der verfügbaren Daten zurück"""
        stats = {
            'total_queries': 0,
            'total_rows': 0,
            'categories': {},
            'largest_datasets': []
        }
        
        queries = self.list_available_queries()
        stats['total_queries'] = len([q for q in queries if q['exists']])
        
        # Sammle Statistiken nach Kategorie
        for query in queries:
            if query['exists']:
                category = query['category']
                if category not in stats['categories']:
                    stats['categories'][category] = {
                        'count': 0,
                        'rows': 0
                    }
                stats['categories'][category]['count'] += 1
                stats['categories'][category]['rows'] += query['rows']
                stats['total_rows'] += query['rows']
        
        # Finde die größten Datensätze
        sorted_queries = sorted([q for q in queries if q['exists']], 
                              key=lambda x: x['rows'], reverse=True)
        stats['largest_datasets'] = sorted_queries[:10]
        
        return stats