"""
HTMX Component Generator for WINCASA

Generates reusable HTMX components from UI models.
Creates forms, tables, cards, and other UI elements with DaisyUI styling.

SessionID: htmx-migration-20250615
Author: Claude Code
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ComponentType(Enum):
    """Types of HTMX components we can generate"""
    FORM = "form"
    TABLE = "table"
    CARD = "card"
    LIST = "list"
    SEARCH = "search"
    FILTER = "filter"
    MODAL = "modal"
    STATS = "stats"

@dataclass
class HTMXComponent:
    """Represents a generated HTMX component"""
    name: str
    type: ComponentType
    template: str
    styles: List[str]
    scripts: Optional[str] = None
    description: Optional[str] = None

class HTMXComponentGenerator:
    """
    Generates HTMX components from UI models.
    Uses DaisyUI for styling and Alpine.js for minimal interactivity.
    """
    
    def __init__(self, ui_models_path: str = "data/ui_models", 
                 output_path: str = "static/components"):
        self.ui_models_path = Path(ui_models_path)
        self.output_path = Path(output_path)
        self.output_path.mkdir(parents=True, exist_ok=True)
        
        # DaisyUI theme colors
        self.theme = {
            "primary": "primary",
            "secondary": "secondary", 
            "accent": "accent",
            "neutral": "neutral",
            "base": "base-100",
            "info": "info",
            "success": "success",
            "warning": "warning",
            "error": "error"
        }
    
    def load_ui_model(self, model_name: str) -> Optional[Dict]:
        """Load a UI model from JSON file"""
        model_file = self.ui_models_path / f"{model_name}_ui_model.json"
        if not model_file.exists():
            logger.warning(f"UI model not found: {model_file}")
            return None
        
        with open(model_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def generate_form_component(self, ui_model: Dict) -> HTMXComponent:
        """Generate an HTMX form component from UI model"""
        entity_name = ui_model['entity_name']
        german_title = ui_model['german_title']
        fields = ui_model['fields']
        
        # Group fields by their group attribute
        field_groups = {}
        for field in fields:
            group = field.get('group', 'Allgemeine Informationen')
            if group not in field_groups:
                field_groups[group] = []
            field_groups[group].append(field)
        
        # Start building the form HTML
        form_html = f'''<form 
    id="{entity_name}-form"
    hx-post="/api/{entity_name}"
    hx-trigger="submit"
    hx-target="#result-container"
    hx-swap="innerHTML"
    hx-indicator="#loading-indicator"
    class="space-y-6"
    x-data="{{ formValid: false, errors: {{}} }}"
>
    <div class="card bg-base-100 shadow-xl">
        <div class="card-body">
            <h2 class="card-title text-2xl mb-6">
                <i class="fas fa-building mr-2"></i>
                {german_title}
            </h2>
            
            <!-- Loading Indicator -->
            <div id="loading-indicator" class="htmx-indicator">
                <div class="flex justify-center items-center p-4">
                    <span class="loading loading-spinner loading-lg"></span>
                </div>
            </div>
'''
        
        # Generate field groups
        for group_name, group_fields in field_groups.items():
            if len(group_fields) == 0:
                continue
                
            form_html += f'''
            <!-- {group_name} -->
            <div class="divider">{group_name}</div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
'''
            
            for field in group_fields:
                form_html += self._generate_form_field(field)
            
            form_html += '''
            </div>
'''
        
        # Add form actions
        form_html += '''
            <!-- Form Actions -->
            <div class="card-actions justify-end mt-6">
                <button type="reset" class="btn btn-ghost">
                    <i class="fas fa-undo mr-2"></i>
                    Zurücksetzen
                </button>
                <button type="submit" 
                        class="btn btn-primary"
                        :disabled="!formValid">
                    <i class="fas fa-save mr-2"></i>
                    Speichern
                </button>
            </div>
        </div>
    </div>
</form>

<!-- Result Container -->
<div id="result-container" class="mt-6"></div>
'''
        
        # Create component
        return HTMXComponent(
            name=f"{entity_name}_form",
            type=ComponentType.FORM,
            template=form_html,
            styles=["form-control", "input", "select", "textarea", "btn"],
            description=f"Form component for {german_title}"
        )
    
    def _generate_form_field(self, field: Dict) -> str:
        """Generate HTML for a single form field"""
        field_name = field['name']
        field_type = field['field_type']
        label = field['german_label']
        is_required = field['is_required']
        placeholder = field.get('placeholder', '')
        help_text = field.get('help_text', '')
        validation_rules = field.get('validation_rules', [])
        
        # Build validation attributes
        validation_attrs = []
        if is_required:
            validation_attrs.append('required')
        
        for rule in validation_rules:
            if '=' in rule:
                attr, value = rule.split('=', 1)
                validation_attrs.append(f'{attr}="{value}"')
            else:
                validation_attrs.append(rule)
        
        validation_str = ' '.join(validation_attrs)
        
        # Generate field based on type
        if field_type == 'select':
            return self._generate_select_field(field, validation_str)
        elif field_type == 'textarea':
            return self._generate_textarea_field(field, validation_str)
        elif field_type == 'boolean':
            return self._generate_checkbox_field(field)
        else:
            return self._generate_input_field(field, validation_str)
    
    def _generate_input_field(self, field: Dict, validation_str: str) -> str:
        """Generate standard input field"""
        field_name = field['name']
        field_type = field['field_type']
        label = field['german_label']
        placeholder = field.get('placeholder', '')
        is_required = field['is_required']
        
        # Map field types to HTML input types
        input_type_map = {
            'email': 'email',
            'phone': 'tel',
            'date': 'date',
            'number': 'number',
            'currency': 'number',
            'password': 'password',
            'url': 'url',
            'text': 'text'
        }
        
        html_type = input_type_map.get(field_type, 'text')
        
        # Add currency-specific attributes
        currency_attrs = ''
        if field_type == 'currency':
            currency_attrs = 'step="0.01" min="0"'
        
        return f'''
                <div class="form-control w-full">
                    <label class="label" for="{field_name}">
                        <span class="label-text">
                            {label}
                            {' <span class="text-error">*</span>' if is_required else ''}
                        </span>
                    </label>
                    <input 
                        type="{html_type}"
                        id="{field_name}"
                        name="{field_name}"
                        placeholder="{placeholder}"
                        class="input input-bordered w-full"
                        {validation_str}
                        {currency_attrs}
                        @blur="validateField('{field_name}')"
                    />
                    <label class="label" x-show="errors.{field_name}">
                        <span class="label-text-alt text-error" x-text="errors.{field_name}"></span>
                    </label>
                </div>
'''
    
    def _generate_select_field(self, field: Dict, validation_str: str) -> str:
        """Generate select dropdown field"""
        field_name = field['name']
        label = field['german_label']
        is_required = field['is_required']
        
        return f'''
                <div class="form-control w-full">
                    <label class="label" for="{field_name}">
                        <span class="label-text">
                            {label}
                            {' <span class="text-error">*</span>' if is_required else ''}
                        </span>
                    </label>
                    <select 
                        id="{field_name}"
                        name="{field_name}"
                        class="select select-bordered w-full"
                        {validation_str}
                        hx-get="/api/{field_name}/options"
                        hx-trigger="load"
                    >
                        <option value="">Bitte wählen...</option>
                    </select>
                </div>
'''
    
    def _generate_textarea_field(self, field: Dict, validation_str: str) -> str:
        """Generate textarea field"""
        field_name = field['name']
        label = field['german_label']
        placeholder = field.get('placeholder', '')
        is_required = field['is_required']
        
        return f'''
                <div class="form-control w-full md:col-span-2">
                    <label class="label" for="{field_name}">
                        <span class="label-text">
                            {label}
                            {' <span class="text-error">*</span>' if is_required else ''}
                        </span>
                    </label>
                    <textarea 
                        id="{field_name}"
                        name="{field_name}"
                        placeholder="{placeholder}"
                        class="textarea textarea-bordered w-full"
                        rows="4"
                        {validation_str}
                    ></textarea>
                </div>
'''
    
    def _generate_checkbox_field(self, field: Dict) -> str:
        """Generate checkbox field"""
        field_name = field['name']
        label = field['german_label']
        
        return f'''
                <div class="form-control w-full">
                    <label class="label cursor-pointer">
                        <span class="label-text">{label}</span>
                        <input 
                            type="checkbox"
                            id="{field_name}"
                            name="{field_name}"
                            class="checkbox checkbox-primary"
                            value="1"
                        />
                    </label>
                </div>
'''
    
    def generate_table_component(self, ui_model: Dict) -> HTMXComponent:
        """Generate an HTMX table component from UI model"""
        entity_name = ui_model['entity_name']
        german_title = ui_model['german_title']
        fields = ui_model['fields'][:8]  # Limit to first 8 fields for table
        
        table_html = f'''<div class="card bg-base-100 shadow-xl">
    <div class="card-body">
        <h2 class="card-title">
            <i class="fas fa-table mr-2"></i>
            {german_title} Übersicht
        </h2>
        
        <!-- Search Bar -->
        <div class="form-control mb-4">
            <input 
                type="search" 
                placeholder="Suchen..."
                class="input input-bordered w-full max-w-xs"
                hx-get="/api/{entity_name}/search"
                hx-trigger="keyup changed delay:500ms"
                hx-target="#table-body"
                name="q"
            />
        </div>
        
        <!-- Table -->
        <div class="overflow-x-auto">
            <table class="table table-zebra">
                <thead>
                    <tr>
'''
        
        # Generate table headers
        for field in fields:
            if not field.get('is_computed', False):  # Skip computed fields
                table_html += f'''                        <th>{field['german_label']}</th>
'''
        
        table_html += '''                        <th>Aktionen</th>
                    </tr>
                </thead>
                <tbody id="table-body" 
                       hx-get="/api/{entity_name}/list"
                       hx-trigger="load">
                    <!-- Data will be loaded here -->
                </tbody>
            </table>
        </div>
        
        <!-- Pagination -->
        <div class="join justify-center mt-4">
            <button class="join-item btn" hx-get="/api/{entity_name}/list?page=prev" hx-target="#table-body">«</button>
            <button class="join-item btn btn-active">1</button>
            <button class="join-item btn" hx-get="/api/{entity_name}/list?page=2" hx-target="#table-body">2</button>
            <button class="join-item btn" hx-get="/api/{entity_name}/list?page=3" hx-target="#table-body">3</button>
            <button class="join-item btn" hx-get="/api/{entity_name}/list?page=next" hx-target="#table-body">»</button>
        </div>
    </div>
</div>
'''
        
        return HTMXComponent(
            name=f"{entity_name}_table",
            type=ComponentType.TABLE,
            template=table_html,
            styles=["table", "table-zebra", "overflow-x-auto"],
            description=f"Table component for {german_title}"
        )
    
    def generate_search_component(self, ui_model: Dict) -> HTMXComponent:
        """Generate a search component with filters"""
        entity_name = ui_model['entity_name']
        german_title = ui_model['german_title']
        
        # Select key fields for search filters
        filter_fields = []
        for field in ui_model['fields']:
            if field['field_type'] in ['select', 'boolean'] or field['name'].endswith('nr'):
                filter_fields.append(field)
                if len(filter_fields) >= 4:
                    break
        
        search_html = f'''<div class="card bg-base-100 shadow-xl">
    <div class="card-body">
        <h2 class="card-title">
            <i class="fas fa-search mr-2"></i>
            {german_title} Suche
        </h2>
        
        <form hx-get="/api/{entity_name}/search"
              hx-target="#search-results"
              hx-trigger="submit, change from:select"
              class="space-y-4">
            
            <!-- Main Search -->
            <div class="form-control">
                <label class="label">
                    <span class="label-text">Suchbegriff</span>
                </label>
                <input type="search" 
                       name="q"
                       placeholder="Name, Nummer oder Beschreibung..."
                       class="input input-bordered w-full" />
            </div>
            
            <!-- Filters -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
'''
        
        # Add filter fields
        for field in filter_fields:
            if field['field_type'] == 'boolean':
                search_html += f'''
                <div class="form-control">
                    <label class="label cursor-pointer">
                        <span class="label-text">{field['german_label']}</span>
                        <input type="checkbox" 
                               name="{field['name']}"
                               class="checkbox checkbox-primary" />
                    </label>
                </div>
'''
            else:
                search_html += f'''
                <div class="form-control">
                    <label class="label">
                        <span class="label-text">{field['german_label']}</span>
                    </label>
                    <select name="{field['name']}" 
                            class="select select-bordered select-sm">
                        <option value="">Alle</option>
                        <!-- Options loaded via HTMX -->
                    </select>
                </div>
'''
        
        search_html += '''
            </div>
            
            <!-- Search Actions -->
            <div class="flex justify-between">
                <button type="reset" class="btn btn-ghost btn-sm">
                    <i class="fas fa-times mr-2"></i>
                    Filter zurücksetzen
                </button>
                <button type="submit" class="btn btn-primary btn-sm">
                    <i class="fas fa-search mr-2"></i>
                    Suchen
                </button>
            </div>
        </form>
    </div>
</div>

<!-- Search Results -->
<div id="search-results" class="mt-6">
    <!-- Results will be loaded here -->
</div>
'''
        
        return HTMXComponent(
            name=f"{entity_name}_search",
            type=ComponentType.SEARCH,
            template=search_html,
            styles=["form-control", "input", "select", "checkbox"],
            description=f"Search component for {german_title}"
        )
    
    def generate_card_component(self, ui_model: Dict) -> HTMXComponent:
        """Generate a card component for displaying single entity"""
        entity_name = ui_model['entity_name']
        german_title = ui_model['german_title']
        display_field = ui_model.get('display_field', 'name')
        
        card_html = f'''<div class="card bg-base-100 shadow-xl hover:shadow-2xl transition-shadow">
    <div class="card-body">
        <h2 class="card-title">
            <i class="fas fa-user mr-2"></i>
            <span hx-text="{{{display_field}}}">Loading...</span>
        </h2>
        
        <div class="stats stats-vertical lg:stats-horizontal shadow">
'''
        
        # Add key stats
        stat_fields = []
        for field in ui_model['fields']:
            if field['field_type'] in ['currency', 'number'] and not field.get('is_computed'):
                stat_fields.append(field)
                if len(stat_fields) >= 3:
                    break
        
        for field in stat_fields:
            icon = 'fa-euro-sign' if field['field_type'] == 'currency' else 'fa-hashtag'
            card_html += f'''
            <div class="stat">
                <div class="stat-figure text-primary">
                    <i class="fas {icon} text-3xl"></i>
                </div>
                <div class="stat-title">{field['german_label']}</div>
                <div class="stat-value" hx-text="{{{field['name']}}}">0</div>
            </div>
'''
        
        card_html += f'''
        </div>
        
        <div class="card-actions justify-end mt-4">
            <button class="btn btn-primary btn-sm"
                    hx-get="/api/{entity_name}/{{{{id}}}}"
                    hx-target="#modal-content"
                    hx-trigger="click"
                    onclick="document.getElementById('detail-modal').showModal()">
                <i class="fas fa-eye mr-2"></i>
                Details
            </button>
            <button class="btn btn-ghost btn-sm"
                    hx-get="/api/{entity_name}/{{{{id}}}}/edit"
                    hx-target="#modal-content">
                <i class="fas fa-edit mr-2"></i>
                Bearbeiten
            </button>
        </div>
    </div>
</div>
'''
        
        return HTMXComponent(
            name=f"{entity_name}_card",
            type=ComponentType.CARD,
            template=card_html,
            styles=["card", "stats", "stat"],
            description=f"Card component for {german_title}"
        )
    
    def generate_all_components(self) -> Dict[str, List[HTMXComponent]]:
        """Generate all components for all UI models"""
        all_components = {}
        
        # Get all UI model files
        model_files = list(self.ui_models_path.glob("*_ui_model.json"))
        logger.info(f"Found {len(model_files)} UI models to process")
        
        for model_file in model_files:
            model_name = model_file.stem.replace('_ui_model', '')
            
            # Skip meta models
            if model_name.startswith('_'):
                continue
            
            ui_model = self.load_ui_model(model_name)
            if not ui_model or len(ui_model.get('fields', [])) == 0:
                continue
            
            logger.info(f"Generating components for {model_name}")
            
            components = []
            
            # Generate different component types
            try:
                components.append(self.generate_form_component(ui_model))
                components.append(self.generate_table_component(ui_model))
                components.append(self.generate_search_component(ui_model))
                components.append(self.generate_card_component(ui_model))
            except Exception as e:
                logger.error(f"Failed to generate components for {model_name}: {e}")
                continue
            
            all_components[model_name] = components
        
        return all_components
    
    def save_components(self, components: Dict[str, List[HTMXComponent]]) -> None:
        """Save generated components to files"""
        for entity_name, entity_components in components.items():
            entity_dir = self.output_path / entity_name
            entity_dir.mkdir(exist_ok=True)
            
            for component in entity_components:
                # Save HTML template
                template_file = entity_dir / f"{component.name}.html"
                with open(template_file, 'w', encoding='utf-8') as f:
                    f.write(component.template)
                
                # Save component metadata
                meta_file = entity_dir / f"{component.name}.json"
                meta_data = {
                    "name": component.name,
                    "type": component.type.value,
                    "description": component.description,
                    "styles": component.styles,
                    "scripts": component.scripts
                }
                with open(meta_file, 'w', encoding='utf-8') as f:
                    json.dump(meta_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved {sum(len(c) for c in components.values())} components to {self.output_path}")
    
    def generate_component_library_index(self, components: Dict[str, List[HTMXComponent]]) -> None:
        """Generate an index page for the component library"""
        index_html = '''<!DOCTYPE html>
<html lang="de" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WINCASA HTMX Component Library</title>
    <link href="https://cdn.jsdelivr.net/npm/daisyui@4.4.24/dist/full.min.css" rel="stylesheet">
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/htmx.org@1.9.10"></script>
    <script src="https://unpkg.com/alpinejs@3.13.3/dist/cdn.min.js" defer></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
</head>
<body>
    <div class="container mx-auto p-4">
        <h1 class="text-4xl font-bold mb-8">
            <i class="fas fa-cube mr-3"></i>
            WINCASA HTMX Component Library
        </h1>
        
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
'''
        
        # Add cards for each entity
        for entity_name, entity_components in sorted(components.items()):
            component_count = len(entity_components)
            first_component = entity_components[0] if entity_components else None
            
            if first_component:
                index_html += f'''
            <div class="card bg-base-100 shadow-xl">
                <div class="card-body">
                    <h2 class="card-title">
                        <i class="fas fa-folder mr-2"></i>
                        {entity_name.replace('_', ' ').title()}
                    </h2>
                    <p>{component_count} Komponenten verfügbar</p>
                    <div class="card-actions justify-end">
                        <a href="{entity_name}/" class="btn btn-primary btn-sm">
                            <i class="fas fa-eye mr-2"></i>
                            Anzeigen
                        </a>
                    </div>
                </div>
            </div>
'''
        
        index_html += '''
        </div>
        
        <div class="divider mt-8"></div>
        
        <div class="stats shadow">
            <div class="stat">
                <div class="stat-figure text-primary">
                    <i class="fas fa-cube text-3xl"></i>
                </div>
                <div class="stat-title">Entities</div>
                <div class="stat-value">''' + str(len(components)) + '''</div>
            </div>
            
            <div class="stat">
                <div class="stat-figure text-secondary">
                    <i class="fas fa-code text-3xl"></i>
                </div>
                <div class="stat-title">Components</div>
                <div class="stat-value">''' + str(sum(len(c) for c in components.values())) + '''</div>
            </div>
        </div>
    </div>
</body>
</html>
'''
        
        index_file = self.output_path / "index.html"
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(index_html)
        
        logger.info(f"Generated component library index at {index_file}")

def main():
    """Generate HTMX components from UI models"""
    logging.basicConfig(level=logging.INFO)
    
    try:
        generator = HTMXComponentGenerator()
        
        # Generate all components
        components = generator.generate_all_components()
        
        # Save components to files
        generator.save_components(components)
        
        # Generate index page
        generator.generate_component_library_index(components)
        
        print(f"✅ Generated {sum(len(c) for c in components.values())} HTMX components")
        print(f"📁 Components saved to: static/components/")
        print(f"🌐 View component library at: static/components/index.html")
        
    except Exception as e:
        logger.error(f"Component generation failed: {e}")
        raise

if __name__ == "__main__":
    main()