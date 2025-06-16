"""
WINCASA Dynamic UI Model Generator

Generates intelligent UI models from database schema and knowledge base.
Converts 400+ field mappings and 41 German business terms into structured UI models
for automatic form generation.

SessionID: htmx-migration-20250615
Author: Claude Code
"""

import json
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import re
from enum import Enum

logger = logging.getLogger(__name__)

class FieldType(Enum):
    """UI field types with semantic meaning"""
    TEXT = "text"
    EMAIL = "email" 
    PHONE = "phone"
    CURRENCY = "currency"
    NUMBER = "number"
    DATE = "date"
    BOOLEAN = "boolean"
    SELECT = "select"
    TEXTAREA = "textarea"
    PASSWORD = "password"
    URL = "url"
    HIDDEN = "hidden"

class ValidationRule(Enum):
    """Validation rules for form fields"""
    REQUIRED = "required"
    EMAIL_FORMAT = "email"
    PHONE_FORMAT = "phone"
    MIN_LENGTH = "minlength"
    MAX_LENGTH = "maxlength"
    PATTERN = "pattern"
    MIN_VALUE = "min"
    MAX_VALUE = "max"

@dataclass
class UIField:
    """Single form field with all UI generation information"""
    name: str                           # Technical field name (e.g., EEMAIL)
    german_label: str                   # Display label (e.g., "E-Mail Adresse")
    field_type: FieldType              # Input type for rendering
    is_required: bool = False          # Field is mandatory
    validation_rules: List[str] = field(default_factory=list)
    placeholder: Optional[str] = None   # Input placeholder text
    help_text: Optional[str] = None    # Field description
    related_entity: Optional[str] = None # Connected business entity
    sample_value: Optional[str] = None  # Example value for forms
    is_computed: bool = False          # Read-only calculated field
    group: Optional[str] = None        # Field grouping for layout

@dataclass
class UIModel:
    """Complete UI model for an entity with all fields and metadata"""
    entity_name: str                    # Technical name (e.g., eigentuemer)
    german_title: str                   # Display title (e.g., "Eigentümer")
    description: str                    # Entity description
    fields: List[UIField] = field(default_factory=list)
    relationships: Dict[str, str] = field(default_factory=dict)
    query_templates: List[str] = field(default_factory=list)
    primary_key: Optional[str] = None   # Main identifier field
    display_field: Optional[str] = None # Field for human display
    icon: Optional[str] = None          # UI icon class

class UIModelGenerator:
    """
    Generates UI models from WINCASA knowledge base and database schema.
    
    Combines:
    - 400+ field mappings from alias_map.json
    - 41 German business terms from business_vocabulary.json
    - Schema information from JSON exports
    - Relationship data from join_graph.json
    """
    
    def __init__(self, knowledge_base_path: str = "data/knowledge_base"):
        self.kb_path = Path(knowledge_base_path)
        self.alias_map: Dict[str, Any] = {}
        self.business_vocab: Dict[str, Any] = {}
        self.join_graph: Dict[str, Any] = {}
        self.export_schemas: Dict[str, Any] = {}
        
        logger.info(f"Initializing UI Model Generator with KB path: {self.kb_path}")
        self._load_knowledge_base()
        self._load_export_schemas()
    
    def _load_knowledge_base(self) -> None:
        """Load all knowledge base files"""
        try:
            # Load field mappings (400+ mappings)
            alias_map_path = self.kb_path / "alias_map.json"
            if alias_map_path.exists():
                with open(alias_map_path, 'r', encoding='utf-8') as f:
                    self.alias_map = json.load(f)
                logger.info(f"Loaded {len(self.alias_map)} field mappings")
            
            # Load German business vocabulary (41 terms)
            vocab_path = self.kb_path / "business_vocabulary.json"
            if vocab_path.exists():
                with open(vocab_path, 'r', encoding='utf-8') as f:
                    self.business_vocab = json.load(f)
                logger.info(f"Loaded {len(self.business_vocab)} business terms")
            
            # Load table relationships
            join_path = self.kb_path / "join_graph.json"
            if join_path.exists():
                with open(join_path, 'r', encoding='utf-8') as f:
                    self.join_graph = json.load(f)
                logger.info(f"Loaded join graph with {len(self.join_graph)} tables")
                
        except Exception as e:
            logger.error(f"Failed to load knowledge base: {e}")
            raise
    
    def _load_export_schemas(self) -> None:
        """Load database schemas from JSON exports"""
        export_path = Path("data/exports")
        if not export_path.exists():
            logger.warning(f"Export path not found: {export_path}")
            return
        
        try:
            schema_count = 0
            for json_file in export_path.glob("*.json"):
                if json_file.name.startswith("rag_"):
                    continue  # Skip RAG data files
                
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        
                        # Handle different JSON structures
                        sample_record = None
                        if isinstance(data, list) and len(data) > 0:
                            # Direct list format
                            sample_record = data[0]
                        elif isinstance(data, dict):
                            # Nested format with query_info
                            if 'data' in data and isinstance(data['data'], list) and len(data['data']) > 0:
                                sample_record = data['data'][0]
                            elif 'results' in data and isinstance(data['results'], list) and len(data['results']) > 0:
                                sample_record = data['results'][0]
                        
                        if sample_record and isinstance(sample_record, dict):
                            # Clean schema name: "01_eigentuemer" -> "Eigentuemer"
                            schema_name = json_file.stem.split('_', 1)[-1].title()
                            self.export_schemas[schema_name] = {
                                "sample_record": sample_record,
                                "field_count": len(sample_record),
                                "source_file": json_file.name
                            }
                            schema_count += 1
                            
                except Exception as file_error:
                    logger.warning(f"Failed to load {json_file.name}: {file_error}")
                        
            logger.info(f"Loaded {schema_count} export schemas")
            
        except Exception as e:
            logger.error(f"Failed to load export schemas: {e}")
    
    def _infer_field_type(self, field_name: str, sample_value: Any, field_mapping: Optional[Dict] = None) -> FieldType:
        """Infer UI field type from field name and sample data"""
        name_lower = field_name.lower()
        
        # Email detection
        if ('email' in name_lower or 'mail' in name_lower) and isinstance(sample_value, str):
            return FieldType.EMAIL
        
        # Phone detection  
        if ('tel' in name_lower or 'handy' in name_lower or 'phone' in name_lower):
            return FieldType.PHONE
        
        # Currency detection
        if (('betrag' in name_lower or 'kosten' in name_lower or 'miete' in name_lower or 
             'preis' in name_lower or 'saldo' in name_lower) and 
            isinstance(sample_value, (int, float))):
            return FieldType.CURRENCY
        
        # Date detection
        if ('datum' in name_lower or 'beginn' in name_lower or 'ende' in name_lower or
            'zeit' in name_lower):
            return FieldType.DATE
        
        # Boolean detection (German property management often uses 0/1)
        if isinstance(sample_value, (bool, int)) and sample_value in [0, 1, True, False]:
            return FieldType.BOOLEAN
        
        # Number detection
        if isinstance(sample_value, (int, float)) and 'nr' not in name_lower:
            return FieldType.NUMBER
        
        # Password detection
        if 'password' in name_lower or 'passwd' in name_lower:
            return FieldType.PASSWORD
        
        # URL detection
        if 'url' in name_lower or 'website' in name_lower:
            return FieldType.URL
        
        # Large text fields
        if ('beschreibung' in name_lower or 'bemerkung' in name_lower or 
            'notiz' in name_lower or 'text' in name_lower):
            return FieldType.TEXTAREA
        
        # Default to text
        return FieldType.TEXT
    
    def _get_german_label(self, field_name: str, entity_name: str = "") -> str:
        """Generate German label for field using business vocabulary"""
        
        # Check if field exists in business vocabulary
        for term, vocab_info in self.business_vocab.items():
            if 'key_fields' in vocab_info:
                if field_name.upper() in [f.upper() for f in vocab_info['key_fields']]:
                    return vocab_info.get('description', field_name)
            
            # Check aliases
            if 'aliases' in vocab_info:
                for alias in vocab_info['aliases']:
                    if field_name.upper() == alias.upper():
                        return vocab_info.get('description', field_name)
        
        # Check alias map for descriptions
        if field_name in self.alias_map:
            mapping = self.alias_map[field_name]
            if 'description' in mapping and mapping['description']:
                return mapping['description']
        
        # Generate from field name patterns
        name_lower = field_name.lower()
        
        # Common German property management field patterns
        patterns = {
            'eignr': 'Eigentümer-Nr.',
            'bewnr': 'Bewohner-Nr.',
            'onr': 'Objekt-Nr.',
            'enr': 'Einheit-Nr.',
            'email': 'E-Mail Adresse',
            'handy': 'Mobiltelefon',
            'tel': 'Telefon',
            'str': 'Straße',
            'plz': 'Postleitzahl',
            'ort': 'Ort',
            'kaltmiete': 'Kaltmiete',
            'warmmiete': 'Warmmiete',
            'nebenkosten': 'Nebenkosten',
            'beginn': 'Beginn',
            'ende': 'Ende',
            'qm': 'Quadratmeter',
            'saldo': 'Saldo',
            'betrag': 'Betrag'
        }
        
        for pattern, label in patterns.items():
            if pattern in name_lower:
                return label
        
        # Fallback: Clean up technical field name
        return field_name.replace('_', ' ').title()
    
    def _determine_validation_rules(self, field: UIField) -> List[str]:
        """Determine validation rules based on field type and business context"""
        rules = []
        
        if field.is_required:
            rules.append(ValidationRule.REQUIRED.value)
        
        if field.field_type == FieldType.EMAIL:
            rules.append(ValidationRule.EMAIL_FORMAT.value)
        
        if field.field_type == FieldType.PHONE:
            rules.append(ValidationRule.PHONE_FORMAT.value)
        
        if field.field_type == FieldType.CURRENCY:
            rules.append(f"{ValidationRule.MIN_VALUE.value}=0")
        
        # German property management specific rules
        name_lower = field.name.lower()
        if 'plz' in name_lower:
            rules.append(f"{ValidationRule.PATTERN.value}=\\d{{5}}")  # German postal code
        
        if 'email' in name_lower:
            rules.append(f"{ValidationRule.MAX_LENGTH.value}=255")
        
        return rules
    
    def _get_field_group(self, field_name: str, entity_name: str) -> Optional[str]:
        """Determine logical grouping for form fields"""
        name_lower = field_name.lower()
        
        # Contact information group
        if any(x in name_lower for x in ['email', 'tel', 'handy', 'fax']):
            return "Kontaktdaten"
        
        # Address information group  
        if any(x in name_lower for x in ['str', 'plz', 'ort', 'adresse']):
            return "Adresse"
        
        # Financial information group
        if any(x in name_lower for x in ['betrag', 'kosten', 'miete', 'saldo', 'preis']):
            return "Finanzinformationen"
        
        # Time/Date information group
        if any(x in name_lower for x in ['datum', 'beginn', 'ende', 'zeit']):
            return "Zeitangaben"
        
        # Technical IDs group
        if name_lower.endswith('nr') or name_lower.endswith('id'):
            return "Identifikatoren"
        
        return "Allgemeine Informationen"
    
    def generate_ui_model(self, entity_name: str, export_schema_name: Optional[str] = None) -> UIModel:
        """Generate complete UI model for an entity"""
        logger.info(f"Generating UI model for entity: {entity_name}")
        
        # Get business vocabulary information
        vocab_info = self.business_vocab.get(entity_name, {})
        german_title = vocab_info.get('description', entity_name.title())
        description = vocab_info.get('aliases', [entity_name])[0] if vocab_info.get('aliases') else entity_name
        
        # Create base UI model
        ui_model = UIModel(
            entity_name=entity_name,
            german_title=german_title,
            description=description
        )
        
        # Get schema information - improved lookup logic
        schema_info = None
        if export_schema_name and export_schema_name in self.export_schemas:
            schema_info = self.export_schemas[export_schema_name]
        else:
            # Try various naming patterns
            lookup_patterns = [
                entity_name.title(),                           # "eigentuemer" -> "Eigentuemer"
                entity_name.lower(),                           # Direct match
                entity_name.replace('ue', 'ü').title(),        # "eigentuemer" -> "Eigentümer"
                entity_name.replace('oe', 'ö').title(),        # Handle umlauts
                entity_name.replace('ae', 'ä').title()
            ]
            
            for pattern in lookup_patterns:
                if pattern in self.export_schemas:
                    schema_info = self.export_schemas[pattern]
                    break
            
            # Fallback: fuzzy matching
            if not schema_info:
                for schema_name, info in self.export_schemas.items():
                    if (entity_name.lower() in schema_name.lower() or 
                        schema_name.lower() in entity_name.lower()):
                        schema_info = info
                        break
        
        if not schema_info:
            logger.warning(f"No schema found for entity: {entity_name}")
            return ui_model
        
        sample_record = schema_info['sample_record']
        
        # Generate fields from schema
        for field_name, sample_value in sample_record.items():
            if field_name.startswith('_'):  # Skip internal fields
                continue
            
            # Get field mapping information
            field_mapping = self.alias_map.get(field_name)
            
            # Determine field properties
            field_type = self._infer_field_type(field_name, sample_value, field_mapping)
            german_label = self._get_german_label(field_name, entity_name)
            is_required = self._determine_if_required(field_name, sample_value)
            is_computed = field_mapping.get('is_computed', False) if field_mapping else False
            group = self._get_field_group(field_name, entity_name)
            
            # Create UI field
            ui_field = UIField(
                name=field_name,
                german_label=german_label,
                field_type=field_type,
                is_required=is_required,
                placeholder=self._generate_placeholder(field_name, field_type),
                help_text=field_mapping.get('description') if field_mapping else None,
                related_entity=vocab_info.get('primary_table'),
                sample_value=str(sample_value) if sample_value is not None else None,
                is_computed=is_computed,
                group=group
            )
            
            # Add validation rules
            ui_field.validation_rules = self._determine_validation_rules(ui_field)
            
            ui_model.fields.append(ui_field)
        
        # Set primary key and display field
        ui_model.primary_key = self._find_primary_key(ui_model.fields)
        ui_model.display_field = self._find_display_field(ui_model.fields)
        
        # Add relationships from join graph
        if entity_name in self.join_graph:
            ui_model.relationships = self.join_graph[entity_name]
        
        logger.info(f"Generated UI model with {len(ui_model.fields)} fields for {entity_name}")
        return ui_model
    
    def _determine_if_required(self, field_name: str, sample_value: Any) -> bool:
        """Determine if field should be required based on business rules"""
        name_lower = field_name.lower()
        
        # Primary keys are typically required
        if name_lower.endswith('nr') or name_lower.endswith('id'):
            return True
        
        # Important business fields
        required_patterns = ['name', 'bezeichnung', 'titel']
        if any(pattern in name_lower for pattern in required_patterns):
            return True
        
        # Not required if sample value is null/empty
        if sample_value is None or sample_value == "":
            return False
        
        return False
    
    def _generate_placeholder(self, field_name: str, field_type: FieldType) -> Optional[str]:
        """Generate helpful placeholder text for form fields"""
        name_lower = field_name.lower()
        
        placeholders = {
            FieldType.EMAIL: "beispiel@domain.de",
            FieldType.PHONE: "+49 123 456789",
            FieldType.CURRENCY: "0,00 €",
            FieldType.DATE: "TT.MM.JJJJ",
        }
        
        if field_type in placeholders:
            return placeholders[field_type]
        
        # Specific field placeholders
        if 'plz' in name_lower:
            return "12345"
        elif 'str' in name_lower:
            return "Musterstraße 1"
        elif 'ort' in name_lower:
            return "Berlin"
        
        return None
    
    def _find_primary_key(self, fields: List[UIField]) -> Optional[str]:
        """Find the primary key field"""
        for field in fields:
            name_lower = field.name.lower()
            if name_lower.endswith('nr') or name_lower.endswith('id'):
                return field.name
        return None
    
    def _find_display_field(self, fields: List[UIField]) -> Optional[str]:
        """Find the best field for human display"""
        # Look for name/description fields first
        for field in fields:
            name_lower = field.name.lower()
            if any(x in name_lower for x in ['name', 'bezeichnung', 'titel', 'beschreibung']):
                return field.name
        
        # Fallback to first text field
        for field in fields:
            if field.field_type == FieldType.TEXT:
                return field.name
        
        return None
    
    def generate_all_models(self) -> Dict[str, UIModel]:
        """Generate UI models for all known entities"""
        logger.info("Generating UI models for all entities")
        
        models = {}
        
        # Generate from business vocabulary
        for entity_name in self.business_vocab.keys():
            try:
                model = self.generate_ui_model(entity_name)
                models[entity_name] = model
            except Exception as e:
                logger.error(f"Failed to generate model for {entity_name}: {e}")
        
        # Generate from export schemas
        for schema_name in self.export_schemas.keys():
            entity_name = schema_name.lower().replace(" ", "_")
            if entity_name not in models:
                try:
                    model = self.generate_ui_model(entity_name, schema_name)
                    models[entity_name] = model
                except Exception as e:
                    logger.error(f"Failed to generate model for schema {schema_name}: {e}")
        
        logger.info(f"Generated {len(models)} UI models")
        return models
    
    def export_ui_models(self, output_path: str = "data/ui_models") -> None:
        """Export all UI models to JSON files"""
        output_dir = Path(output_path)
        output_dir.mkdir(exist_ok=True)
        
        models = self.generate_all_models()
        
        for entity_name, model in models.items():
            # Convert to dictionary for JSON serialization
            model_dict = {
                "entity_name": model.entity_name,
                "german_title": model.german_title,
                "description": model.description,
                "primary_key": model.primary_key,
                "display_field": model.display_field,
                "relationships": model.relationships,
                "query_templates": model.query_templates,
                "fields": [
                    {
                        "name": f.name,
                        "german_label": f.german_label,
                        "field_type": f.field_type.value,
                        "is_required": f.is_required,
                        "validation_rules": f.validation_rules,
                        "placeholder": f.placeholder,
                        "help_text": f.help_text,
                        "related_entity": f.related_entity,
                        "sample_value": f.sample_value,
                        "is_computed": f.is_computed,
                        "group": f.group
                    }
                    for f in model.fields
                ]
            }
            
            # Save to file
            output_file = output_dir / f"{entity_name}_ui_model.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(model_dict, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Exported {len(models)} UI models to {output_dir}")

def main():
    """Test the UI Model Generator"""
    logging.basicConfig(level=logging.INFO)
    
    try:
        generator = UIModelGenerator()
        
        # Test single entity generation
        model = generator.generate_ui_model("eigentuemer")
        print(f"Generated model for Eigentümer with {len(model.fields)} fields")
        
        # Export all models
        generator.export_ui_models()
        print("All UI models exported successfully")
        
    except Exception as e:
        logger.error(f"UI Model Generator failed: {e}")
        raise

if __name__ == "__main__":
    main()