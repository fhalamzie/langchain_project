#!/usr/bin/env python3
"""
Debug script for UI Model Generator
"""

import json
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def debug_export_loading():
    """Debug the export schema loading"""
    export_path = Path("data/exports")
    
    print(f"Export path exists: {export_path.exists()}")
    print(f"Export path: {export_path.absolute()}")
    
    if export_path.exists():
        json_files = list(export_path.glob("*.json"))
        print(f"Found {len(json_files)} JSON files")
        
        for i, json_file in enumerate(json_files[:5]):  # Only first 5
            print(f"\n{i+1}. {json_file.name}")
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if data and isinstance(data, list) and len(data) > 0:
                        sample_record = data[0]
                        schema_name = json_file.stem.split('_', 1)[-1].title()
                        print(f"   Schema name: {schema_name}")
                        print(f"   Fields: {list(sample_record.keys())[:5]}...")
                        print(f"   Total fields: {len(sample_record)}")
                    else:
                        print(f"   Invalid data format")
            except Exception as e:
                print(f"   Error: {e}")

def test_single_schema():
    """Test loading a single schema"""
    try:
        from src.wincasa.core.ui_model_generator import UIModelGenerator
        
        print("\n=== Testing UIModelGenerator ===")
        generator = UIModelGenerator()
        
        print(f"Loaded schemas: {list(generator.export_schemas.keys())}")
        
        if generator.export_schemas:
            # Test with first available schema
            first_schema = list(generator.export_schemas.keys())[0]
            print(f"\nTesting with schema: {first_schema}")
            
            model = generator.generate_ui_model("test_entity", first_schema)
            print(f"Generated model with {len(model.fields)} fields")
            
            for field in model.fields[:3]:  # Show first 3 fields
                print(f"  {field.name}: {field.german_label} ({field.field_type.value})")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_export_loading()
    test_single_schema()