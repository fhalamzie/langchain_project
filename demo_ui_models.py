#!/usr/bin/env python3
"""
Demo script for generated UI models
Shows the power of automatic UI generation from knowledge base
"""

import json
import sys
from pathlib import Path

def load_ui_model(model_name: str) -> dict:
    """Load a UI model from JSON file"""
    model_path = Path(f"data/ui_models/{model_name}_ui_model.json")
    if not model_path.exists():
        return None
    
    with open(model_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def print_ui_model_summary(model: dict) -> None:
    """Print a nice summary of a UI model"""
    print(f"\n🏢 {model['german_title']} ({model['entity_name']})")
    print(f"   Fields: {len(model['fields'])}")
    print(f"   Primary Key: {model.get('primary_key', 'N/A')}")
    print(f"   Display Field: {model.get('display_field', 'N/A')}")
    
    # Group fields by type
    field_types = {}
    field_groups = {}
    
    for field in model['fields']:
        field_type = field['field_type']
        group = field.get('group', 'Andere')
        
        field_types[field_type] = field_types.get(field_type, 0) + 1
        if group not in field_groups:
            field_groups[group] = []
        field_groups[group].append(field)
    
    print(f"   Field Types: {dict(field_types)}")
    
    # Show field groups
    for group_name, fields in field_groups.items():
        if len(fields) > 2:  # Only show groups with multiple fields
            print(f"   📁 {group_name}: {len(fields)} fields")

def show_detailed_model(model_name: str) -> None:
    """Show detailed view of a specific model"""
    model = load_ui_model(model_name)
    if not model:
        print(f"❌ Model '{model_name}' not found")
        return
    
    print(f"\n{'='*60}")
    print(f"🔍 DETAILED VIEW: {model['german_title']}")
    print(f"{'='*60}")
    
    # Group fields
    field_groups = {}
    for field in model['fields']:
        group = field.get('group', 'Andere')
        if group not in field_groups:
            field_groups[group] = []
        field_groups[group].append(field)
    
    # Show each group
    for group_name, fields in field_groups.items():
        print(f"\n📁 {group_name} ({len(fields)} fields)")
        print("-" * 40)
        
        for field in fields[:5]:  # Show max 5 fields per group
            required = "🔴" if field['is_required'] else "⚪"
            field_type = field['field_type']
            placeholder = f" (placeholder: {field['placeholder']})" if field['placeholder'] else ""
            
            print(f"  {required} {field['name']}: {field['german_label']}")
            print(f"     Type: {field_type}{placeholder}")
            if field['validation_rules']:
                print(f"     Validation: {', '.join(field['validation_rules'])}")
            print()
        
        if len(fields) > 5:
            print(f"     ... and {len(fields) - 5} more fields")

def main():
    """Main demo function"""
    print("🎯 WINCASA Dynamic UI Model Generator - Demo")
    print("=" * 60)
    
    # Get all available models
    ui_models_path = Path("data/ui_models")
    if not ui_models_path.exists():
        print("❌ No UI models found. Run the generator first!")
        return
    
    model_files = list(ui_models_path.glob("*_ui_model.json"))
    model_names = [f.stem.replace('_ui_model', '') for f in model_files]
    
    print(f"📊 Found {len(model_names)} generated UI models")
    
    # Show summary of all models
    print("\n🏗️  UI MODEL OVERVIEW")
    print("-" * 60)
    
    total_fields = 0
    business_entities = []
    
    for model_name in sorted(model_names)[:10]:  # Show first 10
        model = load_ui_model(model_name)
        if model:
            print_ui_model_summary(model)
            total_fields += len(model['fields'])
            
            # Identify business entities (vs technical entities)
            if any(term in model_name for term in ['eigentuemer', 'mieter', 'wohnung', 'objekt']):
                business_entities.append(model_name)
    
    if len(model_names) > 10:
        print(f"\n   ... and {len(model_names) - 10} more models")
    
    print(f"\n📈 STATISTICS")
    print(f"   Total Models: {len(model_names)}")
    print(f"   Total Fields: {total_fields}")
    print(f"   Avg Fields per Model: {total_fields / len(model_names):.1f}")
    print(f"   Core Business Entities: {len(business_entities)}")
    
    # Show detailed view of a key business entity
    if 'eigentuemer' in model_names:
        show_detailed_model('eigentuemer')
    
    # Field type analysis across all models
    print(f"\n🔧 FIELD TYPE ANALYSIS")
    print("-" * 60)
    
    all_field_types = {}
    all_validation_rules = {}
    
    for model_name in model_names:
        model = load_ui_model(model_name)
        if model:
            for field in model['fields']:
                field_type = field['field_type']
                all_field_types[field_type] = all_field_types.get(field_type, 0) + 1
                
                for rule in field['validation_rules']:
                    all_validation_rules[rule] = all_validation_rules.get(rule, 0) + 1
    
    print("Most common field types:")
    for field_type, count in sorted(all_field_types.items(), key=lambda x: x[1], reverse=True):
        print(f"  {field_type}: {count} fields")
    
    print(f"\nValidation rules coverage:")
    for rule, count in sorted(all_validation_rules.items(), key=lambda x: x[1], reverse=True):
        print(f"  {rule}: {count} fields")
    
    print(f"\n✅ UI Model Generation Complete!")
    print(f"   Ready for HTMX component generation...")

if __name__ == "__main__":
    main()