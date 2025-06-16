#!/usr/bin/env python3
"""
Regenerate JSON exports with corrected field names
"""

import sys
import os
sys.path.append('src')

from wincasa.data.json_exporter import JSONExporter

def regenerate_exports():
    """Regenerate all JSON exports with corrected SQL queries"""
    
    print("Regenerating JSON exports with corrected field names...\n")
    
    try:
        exporter = JSONExporter()
        
        # Export all queries
        print("Starting export of all queries...")
        results = exporter.export_all_queries()
        
        print(f"\nExport completed!")
        print(f"- Successful: {results['successful']}")
        print(f"- Failed: {results['failed']}")
        print(f"- Total queries: {results['total_queries']}")
        print(f"- Output directory: {results['output_dir']}")
        
        if results['errors']:
            print("\nErrors encountered:")
            for query, error in results['errors'].items():
                print(f"  - {query}: {error}")
                
    except Exception as e:
        print(f"Error during export: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    regenerate_exports()