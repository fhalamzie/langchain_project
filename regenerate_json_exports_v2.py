#!/usr/bin/env python3
"""
Regenerate JSON exports with corrected field names
"""

import sys
import os
sys.path.append('src')

from wincasa.data.json_exporter import export_all_queries

def regenerate_exports():
    """Regenerate all JSON exports with corrected SQL queries"""
    
    print("Regenerating JSON exports with corrected field names...\n")
    
    try:
        # Export all queries
        print("Starting export of all queries...")
        export_all_queries()
        
        print("\nExport completed!")
        print("Check the data/exports directory for updated JSON files.")
                
    except Exception as e:
        print(f"Error during export: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    regenerate_exports()