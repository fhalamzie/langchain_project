#!/usr/bin/env python3
"""
WINCASA JSON Search Application
Simple search interface for pre-exported JSON data
"""

import os
import json
import glob
from datetime import datetime
from typing import List, Dict, Any, Optional

# Load path configuration
import json as config_json
with open('config/sql_paths.json', 'r') as f:
    path_config = config_json.load(f)
JSON_DIR = path_config['json_exports_dir']

class WincasaJSONSearch:
    """Search interface for WINCASA JSON exports"""
    
    def __init__(self):
        self.json_dir = JSON_DIR
        self.data_cache = {}
        self.load_all_data()
    
    def load_all_data(self):
        """Load all JSON files into memory for fast searching"""
        json_files = glob.glob(os.path.join(self.json_dir, '*.json'))
        
        for json_file in json_files:
            if os.path.basename(json_file).startswith('_'):
                continue  # Skip metadata files
                
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                query_name = os.path.basename(json_file).replace('.json', '')
                self.data_cache[query_name] = {
                    'info': data.get('query_info', {}),
                    'columns': data.get('columns', []),
                    'data': data.get('data', []),
                    'row_count': len(data.get('data', []))
                }
            except Exception as e:
                print(f"Error loading {json_file}: {e}")
    
    def list_available_queries(self) -> List[Dict[str, Any]]:
        """List all available queries with metadata"""
        queries = []
        for query_name, query_data in self.data_cache.items():
            queries.append({
                'name': query_name,
                'rows': query_data['row_count'],
                'purpose': query_data['info'].get('business_purpose', 'N/A'),
                'tables': query_data['info'].get('main_tables', [])
            })
        return sorted(queries, key=lambda x: x['rows'], reverse=True)
    
    def search_all(self, search_term: str, max_results: int = 100) -> List[Dict[str, Any]]:
        """Search across all JSON files for a term"""
        results = []
        search_lower = search_term.lower()
        
        for query_name, query_data in self.data_cache.items():
            for row in query_data['data']:
                # Search in all fields
                if any(search_lower in str(value).lower() for value in row.values()):
                    results.append({
                        'query': query_name,
                        'data': row
                    })
                    
                    if len(results) >= max_results:
                        return results
        
        return results
    
    def search_by_field(self, field_name: str, value: Any, exact_match: bool = False) -> List[Dict[str, Any]]:
        """Search for specific field value across all queries"""
        results = []
        
        for query_name, query_data in self.data_cache.items():
            if field_name not in query_data['columns']:
                continue
                
            for row in query_data['data']:
                if field_name in row:
                    if exact_match:
                        if row[field_name] == value:
                            results.append({
                                'query': query_name,
                                'data': row
                            })
                    else:
                        if str(value).lower() in str(row[field_name]).lower():
                            results.append({
                                'query': query_name,
                                'data': row
                            })
        
        return results
    
    def get_entity_by_id(self, entity_type: str, entity_id: Any) -> Optional[Dict[str, Any]]:
        """Get specific entity by ID"""
        id_mappings = {
            'eigentuemer': 'EIGNR',
            'bewohner': 'BEWNR',
            'objekt': 'ONR',
            'wohnung': 'ENR',
            'konto': 'KNR'
        }
        
        if entity_type.lower() not in id_mappings:
            return None
            
        field_name = id_mappings[entity_type.lower()]
        results = self.search_by_field(field_name, entity_id, exact_match=True)
        
        return results[0] if results else None
    
    def get_financial_summary(self) -> Dict[str, Any]:
        """Get financial summary from available data"""
        summary = {
            'total_transactions': 0,
            'total_accounts': 0,
            'total_owners': 0,
            'total_tenants': 0,
            'total_properties': 0,
            'total_units': 0
        }
        
        # Count from specific queries
        if '18_detaillierte_buchungen_layer4' in self.data_cache:
            summary['total_transactions'] = self.data_cache['18_detaillierte_buchungen_layer4']['row_count']
            
        if '05_konten_enhanced_layer4' in self.data_cache:
            summary['total_accounts'] = self.data_cache['05_konten_enhanced_layer4']['row_count']
            
        if '01_eigentuemer_enhanced_layer4' in self.data_cache:
            summary['total_owners'] = self.data_cache['01_eigentuemer_enhanced_layer4']['row_count']
            
        if '02a_aktuelle_mieter_layer4' in self.data_cache:
            summary['total_tenants'] = self.data_cache['02a_aktuelle_mieter_layer4']['row_count']
            
        if '03_objekte_enhanced_layer4' in self.data_cache:
            summary['total_properties'] = self.data_cache['03_objekte_enhanced_layer4']['row_count']
            
        if '04_wohnungen_enhanced_layer4' in self.data_cache:
            summary['total_units'] = self.data_cache['04_wohnungen_enhanced_layer4']['row_count']
        
        return summary


def main():
    """Example usage of the search interface"""
    print("WINCASA JSON Search System")
    print("=" * 50)
    
    # Initialize search
    search = WincasaJSONSearch()
    
    # Show available queries
    print("\nAvailable Data Sources:")
    queries = search.list_available_queries()
    for q in queries[:10]:  # Show top 10
        print(f"- {q['name']}: {q['rows']} rows")
    
    # Show summary
    print("\nSystem Summary:")
    summary = search.get_financial_summary()
    for key, value in summary.items():
        print(f"- {key}: {value}")
    
    # Example searches
    print("\nExample Searches:")
    
    # Search for a specific owner
    owner = search.get_entity_by_id('eigentuemer', 239)
    if owner:
        print(f"\nOwner 239: {owner['data'].get('ENAME', 'N/A')}")
    
    # Search across all data
    results = search.search_all('Berlin', max_results=5)
    print(f"\nFound {len(results)} results for 'Berlin'")
    
    # Interactive search loop
    print("\n" + "=" * 50)
    print("Interactive Search (type 'quit' to exit)")
    
    while True:
        search_term = input("\nSearch term: ").strip()
        if search_term.lower() == 'quit':
            break
            
        results = search.search_all(search_term, max_results=10)
        print(f"\nFound {len(results)} results:")
        
        for i, result in enumerate(results[:5], 1):
            print(f"\n{i}. From: {result['query']}")
            # Show first few fields
            for key, value in list(result['data'].items())[:5]:
                print(f"   {key}: {value}")


if __name__ == "__main__":
    main()