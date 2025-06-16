#!/usr/bin/env python3
"""
HTMX Static Generator Core
Generates complete HTML/HTMX application from Knowledge Base + Schema

SessionID: htmx-migration-20250615
Dependencies: Knowledge-System, SAD-Pipeline
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from jinja2 import Environment, FileSystemLoader, select_autoescape
import logging

# Standalone generator - no WINCASA imports needed for this phase

logger = logging.getLogger(__name__)

@dataclass
class UIModel:
    """UI Model for a business entity"""
    name: str
    display_name: str
    fields: List[Dict[str, Any]]
    primary_table: str
    key_fields: List[str]
    form_type: str  # 'search', 'filter', 'input'
    validation_rules: Dict[str, Any]

@dataclass
class ComponentSpec:
    """HTMX Component Specification"""
    name: str
    template_path: str
    endpoint: str
    method: str
    target: str
    trigger: str
    attributes: Dict[str, str]

class HTMXStaticGenerator:
    """
    Core HTMX Static Generator
    
    Generates complete static HTMX application from:
    - Knowledge Base (400+ field mappings)
    - Business Vocabulary (41 German terms)
    - SQL Templates
    """
    
    def __init__(self, output_dir: str = "dist/htmx"):
        self.output_dir = Path(output_dir)
        self.knowledge_base = None
        self.business_vocab = None
        self.alias_map = None
        self.ui_models = []
        self.components = []
        
        # Setup Jinja2 environment
        template_dir = Path(__file__).parent / "templates"
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(['html', 'xml'])
        )
        
        # Create output directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "assets").mkdir(exist_ok=True)
        (self.output_dir / "components").mkdir(exist_ok=True)
        (self.output_dir / "api").mkdir(exist_ok=True)
        
    def load_knowledge_systems(self):
        """Load all knowledge systems"""
        logger.info("Loading knowledge systems...")
        
        # Load knowledge base
        kb_path = Path("data/knowledge_base")
        
        with open(kb_path / "business_vocabulary.json", 'r', encoding='utf-8') as f:
            self.business_vocab = json.load(f)
            
        with open(kb_path / "alias_map.json", 'r', encoding='utf-8') as f:
            self.alias_map = json.load(f)
            
        logger.info(f"Loaded {len(self.business_vocab)} business terms")
        logger.info(f"Loaded {len(self.alias_map)} field mappings")
        
    def generate_ui_models(self) -> List[UIModel]:
        """Generate UI Models from Knowledge Base"""
        logger.info("Generating UI models from knowledge base...")
        
        ui_models = []
        
        # Core business entities
        for term, config in self.business_vocab.items():
            if term.startswith('_'):
                continue
                
            # Determine form type based on entity
            form_type = self._determine_form_type(term, config)
            
            # Generate fields from knowledge base
            fields = self._generate_fields_for_entity(term, config)
            
            # Create UI model
            ui_model = UIModel(
                name=term,
                display_name=config.get('description', term.title()),
                fields=fields,
                primary_table=config.get('primary_table', ''),
                key_fields=config.get('key_fields', []),
                form_type=form_type,
                validation_rules=self._generate_validation_rules(term, config)
            )
            
            ui_models.append(ui_model)
            
        logger.info(f"Generated {len(ui_models)} UI models")
        return ui_models
        
    def _determine_form_type(self, term: str, config: Dict) -> str:
        """Determine form type based on business entity"""
        search_entities = ['mieter', 'eigentümer', 'wohnung', 'objekt']
        filter_entities = ['konto', 'buchung', 'beschluss']
        
        if term in search_entities:
            return 'search'
        elif term in filter_entities:
            return 'filter'
        else:
            return 'input'
            
    def _generate_fields_for_entity(self, term: str, config: Dict) -> List[Dict[str, Any]]:
        """Generate form fields for entity from knowledge base"""
        fields = []
        
        # Use key_fields if available
        if 'key_fields' in config:
            for field in config['key_fields']:
                field_config = self._get_field_config(field)
                fields.append(field_config)
                
        # Add computed fields
        if 'computed' in config:
            fields.append({
                'name': f'{term}_computed',
                'type': 'computed',
                'label': f'{term.title()} (berechnet)',
                'formula': config['computed'],
                'readonly': True
            })
            
        # Add primary field for simple entities
        if 'primary_field' in config:
            field_name = config['primary_field'].split('.')[-1]
            fields.append({
                'name': field_name,
                'type': 'currency' if 'miete' in term.lower() else 'text',
                'label': config['description'],
                'required': True
            })
            
        return fields
        
    def _get_field_config(self, field_name: str) -> Dict[str, Any]:
        """Get field configuration from alias map"""
        # Check if field exists in alias map
        if field_name in self.alias_map:
            alias_config = self.alias_map[field_name]
            
            return {
                'name': field_name,
                'type': self._infer_field_type(field_name, alias_config),
                'label': self._generate_german_label(field_name),
                'required': False,
                'source_file': alias_config.get('source_file', '')
            }
        else:
            return {
                'name': field_name,
                'type': 'text',
                'label': self._generate_german_label(field_name),
                'required': False
            }
            
    def _infer_field_type(self, field_name: str, alias_config: Dict) -> str:
        """Infer HTML input type from field metadata"""
        field_lower = field_name.lower()
        
        if any(x in field_lower for x in ['miete', 'betrag', 'saldo', 'kosten']):
            return 'currency'
        elif any(x in field_lower for x in ['datum', 'date']):
            return 'date'
        elif any(x in field_lower for x in ['nr', 'id', 'number']):
            return 'number'
        elif any(x in field_lower for x in ['email', 'mail']):
            return 'email'
        elif any(x in field_lower for x in ['tel', 'phone', 'fon']):
            return 'tel'
        else:
            return 'text'
            
    def _generate_german_label(self, field_name: str) -> str:
        """Generate German label for field"""
        german_labels = {
            'EIGNR': 'Eigentümer-Nr.',
            'ENAME': 'Nachname',
            'EVNAME': 'Vorname',
            'ESTRASSE': 'Straße',
            'EPLZORT': 'PLZ/Ort',
            'BEWNR': 'Bewohner-Nr.',
            'BNAME': 'Nachname',
            'BVNAME': 'Vorname',
            'BSTR': 'Straße',
            'BPLZORT': 'PLZ/Ort',
            'ENR': 'Einheiten-Nr.',
            'ETYP': 'Wohnungstyp',
            'EFLAECHE': 'Wohnfläche',
            'EBEZ': 'Bezeichnung',
            'ONR': 'Objekt-Nr.',
            'OBEZ': 'Objektbezeichnung',
            'OSTRASSE': 'Straße',
            'OPLZORT': 'PLZ/Ort',
            'Z1': 'Kaltmiete',
            'Z2': 'Vorauszahlung',
            'Z3': 'Nebenkosten',
            'Z4': 'Heizkosten',
            'KBETRAG': 'Kontobetrag',
            'DATUM': 'Datum',
            'BETRAG': 'Betrag'
        }
        
        return german_labels.get(field_name, field_name.title())
        
    def _generate_validation_rules(self, term: str, config: Dict) -> Dict[str, Any]:
        """Generate validation rules for entity"""
        rules = {}
        
        # Currency fields
        if any(x in term for x in ['miete', 'kosten', 'betrag']):
            rules['currency'] = {
                'min': 0,
                'max': 100000,
                'step': 0.01
            }
            
        # Date fields
        if 'datum' in term.lower():
            rules['date'] = {
                'min': '1900-01-01',
                'max': '2030-12-31'
            }
            
        # Text length limits
        rules['text'] = {
            'maxlength': 255
        }
        
        return rules
        
    def generate_main_layout(self):
        """Generate main HTML layout"""
        logger.info("Generating main layout...")
        
        template = self.jinja_env.get_template('layout.html')
        content = template.render(
            title="WINCASA Property Management",
            business_entities=self.ui_models,
            version="HTMX 2.0"
        )
        
        with open(self.output_dir / "index.html", 'w', encoding='utf-8') as f:
            f.write(content)
            
    def generate_query_forms(self):
        """Generate query forms for each entity"""
        logger.info("Generating query forms...")
        
        template = self.jinja_env.get_template('query_form.html')
        
        for model in self.ui_models:
            if model.form_type == 'search':
                content = template.render(
                    entity=model,
                    form_id=f"form_{model.name}",
                    endpoint=f"/api/query/{model.name}",
                    target=f"#results_{model.name}"
                )
                
                form_path = self.output_dir / "components" / f"{model.name}_form.html"
                with open(form_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                    
    def generate_result_tables(self):
        """Generate result tables for each entity"""
        logger.info("Generating result tables...")
        
        template = self.jinja_env.get_template('result_table.html')
        
        for model in self.ui_models:
            content = template.render(
                entity=model,
                table_id=f"table_{model.name}",
                fields=model.fields[:10]  # Limit to first 10 fields
            )
            
            table_path = self.output_dir / "components" / f"{model.name}_table.html"
            with open(table_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
    def generate_css_assets(self):
        """Generate CSS assets with DaisyUI Integration"""
        logger.info("Generating CSS assets with DaisyUI...")
        
        css_content = """
/* WINCASA HTMX Styles with DaisyUI Integration */
@import url('https://cdn.jsdelivr.net/npm/daisyui@4.12.14/dist/full.min.css');
@import url('https://cdn.tailwindcss.com');

/* Custom WINCASA Theme for DaisyUI */
:root {
  --rounded-box: 0.5rem;
  --rounded-btn: 0.25rem;
  --rounded-badge: 0.125rem;
  --animation-btn: 0.25s;
  --animation-input: 0.2s;
  --btn-focus-scale: 0.95;
  --border-btn: 1px;
  --tab-border: 1px;
  --tab-radius: 0.5rem;
}

[data-theme="wincasa"] {
  --p: 221 83% 53%;
  --pf: 221 83% 48%;
  --pc: 0 0% 100%;
  --s: 197 37% 24%;
  --sf: 197 37% 19%;
  --sc: 0 0% 100%;
  --a: 175 84% 32%;
  --af: 175 84% 27%;
  --ac: 0 0% 100%;
  --n: 213 27% 14%;
  --nf: 216 28% 7%;
  --nc: 220 13% 91%;
  --b1: 0 0% 100%;
  --b2: 220 13% 95%;
  --b3: 220 13% 91%;
  --bc: 215 28% 17%;
  --in: 198 93% 60%;
  --inc: 0 0% 100%;
  --su: 158 64% 52%;
  --suc: 0 0% 100%;
  --wa: 43 96% 56%;
  --wac: 0 0% 100%;
  --er: 0 91% 71%;
  --erc: 0 0% 100%;
}

/* WINCASA Custom Components */
.wincasa-hero {
  @apply hero min-h-[50vh] bg-base-200;
}

.wincasa-card {
  @apply card bg-base-100 shadow-xl;
}

.wincasa-table {
  @apply table table-zebra table-pin-rows table-pin-cols;
}

.wincasa-form {
  @apply space-y-4;
}

.wincasa-search-form {
  @apply grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-6;
}

.wincasa-results {
  @apply mt-6;
}

.wincasa-currency::before {
  content: "€ ";
  @apply text-base-content/60;
}

.wincasa-status-active {
  @apply badge badge-success;
}

.wincasa-status-inactive {
  @apply badge badge-error;
}

.wincasa-loading {
  @apply opacity-60 pointer-events-none;
}

/* HTMX Loading States */
.htmx-indicator {
  @apply hidden;
}

.htmx-request .htmx-indicator {
  @apply inline-block;
}

.htmx-swapping {
  @apply opacity-50;
}

/* German UI Labels */
.german-label {
  @apply text-sm font-medium text-base-content mb-2;
}

/* Responsive Grid for Property Management */
.property-grid {
  @apply grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6;
}

.tenant-grid {
  @apply grid grid-cols-1 md:grid-cols-2 gap-4;
}

/* WINCASA Specific Table Styles */
.mieter-table {
  @apply table table-compact table-zebra w-full;
}

.eigentuemer-table {
  @apply table table-lg table-zebra w-full;
}

.wohnung-table {
  @apply table table-md table-pin-rows w-full;
}

/* Currency Input Styling */
.currency-input {
  @apply input input-bordered w-full pl-8;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' fill='%236b7280' viewBox='0 0 16 16'%3E%3Cpath d='M4 10.781c.148 1.667 1.513 2.85 3.591 3.003V15h1.043v-1.216c2.27-.179 3.678-1.438 3.678-3.3 0-1.59-.947-2.51-2.956-3.028l-.722-.187V3.467c1.122.11 1.879.714 2.07 1.616h1.47c-.166-1.6-1.54-2.748-3.54-2.875V1H7.591v1.233c-1.939.23-3.27 1.472-3.27 3.156 0 1.454.966 2.483 2.661 2.917l.61.162v4.031c-1.149-.17-1.94-.8-2.131-1.718H4zm3.391-3.836c-1.043-.263-1.6-.825-1.6-1.616 0-.944.704-1.641 1.8-1.828v3.495l-.2-.05zm1.591 1.872c1.287.323 1.852.859 1.852 1.769 0 1.097-.826 1.828-2.2 1.939V8.73l.348.086z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: 8px center;
}

/* Responsive Design for Mobile */
@media (max-width: 768px) {
  .wincasa-search-form {
    @apply grid-cols-1 gap-3 p-4;
  }
  
  .property-grid {
    @apply grid-cols-1 gap-4;
  }
  
  .mieter-table,
  .eigentuemer-table,
  .wohnung-table {
    @apply table-xs;
  }
}

/* Dark Mode Adjustments */
@media (prefers-color-scheme: dark) {
  [data-theme="wincasa"] {
    --b1: 215 28% 17%;
    --b2: 213 27% 14%;
    --b3: 216 28% 12%;
    --bc: 220 13% 91%;
    --nc: 215 28% 17%;
  }
}
"""
        
        with open(self.output_dir / "assets" / "styles.css", 'w', encoding='utf-8') as f:
            f.write(css_content)
            
    def generate_js_assets(self):
        """Generate JavaScript assets"""
        logger.info("Generating JavaScript assets...")
        
        js_content = """
// WINCASA HTMX JavaScript Enhancements with DaisyUI

// Currency formatting (German locale)
function formatCurrency(value) {
    return new Intl.NumberFormat('de-DE', {
        style: 'currency',
        currency: 'EUR',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(value);
}

// Date formatting (German locale)
function formatDate(dateStr) {
    return new Date(dateStr).toLocaleDateString('de-DE', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
    });
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('🏠 WINCASA HTMX System initialized');
    
    // Format all currency fields
    document.querySelectorAll('.wincasa-currency, .currency').forEach(el => {
        const value = parseFloat(el.textContent);
        if (!isNaN(value)) {
            el.textContent = formatCurrency(value);
        }
    });
    
    // Format all date fields
    document.querySelectorAll('.date').forEach(el => {
        const dateStr = el.textContent;
        if (dateStr && dateStr !== '-' && dateStr !== '') {
            el.textContent = formatDate(dateStr);
        }
    });
    
    // Initialize tooltips for all elements with title attribute
    document.querySelectorAll('[title]').forEach(el => {
        el.classList.add('tooltip');
    });
});

// HTMX Event Handlers
document.body.addEventListener('htmx:beforeRequest', function(evt) {
    // Add DaisyUI loading state
    evt.target.classList.add('wincasa-loading');
    
    // Show loading toast
    showToast('🔄 Lade Daten...', 'info');
});

document.body.addEventListener('htmx:afterRequest', function(evt) {
    // Remove loading state
    evt.target.classList.remove('wincasa-loading');
    
    // Format any new currency/date fields
    formatDynamicContent(evt.target);
    
    // Show success/error toast
    if (evt.detail.xhr.status === 200) {
        showToast('✅ Daten erfolgreich geladen', 'success');
    } else {
        showToast('❌ Fehler beim Laden der Daten', 'error');
    }
});

document.body.addEventListener('htmx:responseError', function(evt) {
    showToast('🚨 Server-Fehler: ' + evt.detail.xhr.status, 'error');
});

// DaisyUI Toast System
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-top toast-end`;
    
    const alertClass = {
        'info': 'alert-info',
        'success': 'alert-success', 
        'error': 'alert-error',
        'warning': 'alert-warning'
    }[type] || 'alert-info';
    
    toast.innerHTML = `
        <div class="alert ${alertClass}">
            <span>${message}</span>
        </div>
    `;
    
    document.body.appendChild(toast);
    
    // Auto-remove after 3 seconds
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

// Format dynamic content (for HTMX-loaded content)
function formatDynamicContent(container) {
    container.querySelectorAll('.wincasa-currency, .currency').forEach(el => {
        const value = parseFloat(el.textContent);
        if (!isNaN(value)) {
            el.textContent = formatCurrency(value);
        }
    });
    
    container.querySelectorAll('.date').forEach(el => {
        const dateStr = el.textContent;
        if (dateStr && dateStr !== '-' && dateStr !== '') {
            el.textContent = formatDate(dateStr);
        }
    });
}

// Custom validation with DaisyUI feedback
function validateCurrency(input) {
    const value = parseFloat(input.value);
    
    // Remove any existing error styling
    input.classList.remove('input-error');
    
    if (isNaN(value) || value < 0) {
        input.classList.add('input-error');
        input.setCustomValidity('Bitte geben Sie einen gültigen Betrag ein');
        showToast('❌ Ungültiger Betrag eingegeben', 'error');
        return false;
    }
    
    input.setCustomValidity('');
    input.classList.add('input-success');
    
    // Remove success styling after 2 seconds
    setTimeout(() => {
        input.classList.remove('input-success');
    }, 2000);
    
    return true;
}

// Quick Search Templates
function setQuickSearch(entityName, searchTerm) {
    const form = document.getElementById(`form_${entityName}`);
    if (form) {
        // Find the first text input and set the search term
        const firstInput = form.querySelector('input[type="text"]');
        if (firstInput) {
            firstInput.value = searchTerm;
            firstInput.focus();
            
            // Trigger the search automatically
            setTimeout(() => {
                form.requestSubmit();
            }, 500);
        }
    }
}

// Table Management Functions
function toggleAllRows(entityName) {
    const mainCheckbox = event.target;
    const tableId = `table_${entityName}`;
    const table = document.getElementById(tableId);
    
    if (table) {
        const rowCheckboxes = table.querySelectorAll('tbody input[type="checkbox"]');
        rowCheckboxes.forEach(checkbox => {
            checkbox.checked = mainCheckbox.checked;
        });
        
        updateBulkActions(entityName);
    }
}

function updateBulkActions(entityName) {
    const table = document.getElementById(`table_${entityName}`);
    const bulkActions = document.getElementById(`bulk-actions-${entityName}`);
    const selectedCount = document.getElementById(`selected-count-${entityName}`);
    
    if (table && bulkActions && selectedCount) {
        const checkedBoxes = table.querySelectorAll('tbody input[type="checkbox"]:checked');
        const count = checkedBoxes.length;
        
        selectedCount.textContent = count;
        
        if (count > 0) {
            bulkActions.classList.remove('hidden');
        } else {
            bulkActions.classList.add('hidden');
        }
    }
}

function sortTable(entityName, fieldName) {
    // This would trigger an HTMX request to sort the data
    const table = document.getElementById(`table_${entityName}`);
    if (table) {
        htmx.ajax('GET', `/api/sort/${entityName}/${fieldName}`, {
            target: `#table_${entityName} tbody`,
            swap: 'innerHTML'
        });
    }
}

function changePageSize(entityName, pageSize) {
    htmx.ajax('GET', `/api/results/${entityName}?limit=${pageSize}&page=1`, {
        target: `#table_${entityName} tbody`,
        swap: 'innerHTML'
    });
}

function exportSelected(entityName) {
    const table = document.getElementById(`table_${entityName}`);
    const checkedBoxes = table.querySelectorAll('tbody input[type="checkbox"]:checked');
    const selectedIds = Array.from(checkedBoxes).map(cb => cb.value);
    
    if (selectedIds.length > 0) {
        // Create form data
        const form = new FormData();
        selectedIds.forEach(id => form.append('ids[]', id));
        
        // Trigger export
        htmx.ajax('POST', `/api/export/${entityName}/selected`, {
            values: Object.fromEntries(form),
            target: '_blank'
        });
        
        showToast(`📤 Export von ${selectedIds.length} Einträgen gestartet`, 'info');
    }
}

function clearSelection(entityName) {
    const table = document.getElementById(`table_${entityName}`);
    if (table) {
        const checkboxes = table.querySelectorAll('input[type="checkbox"]');
        checkboxes.forEach(cb => cb.checked = false);
        updateBulkActions(entityName);
        showToast('🔄 Auswahl aufgehoben', 'info');
    }
}

// Auto-complete for search fields (integrates with WINCASA Optimized Search)
function setupAutoComplete(input, entityName) {
    let debounceTimer;
    
    input.addEventListener('input', function() {
        clearTimeout(debounceTimer);
        
        debounceTimer = setTimeout(() => {
            const query = input.value.trim();
            
            if (query.length >= 2) {
                htmx.ajax('GET', `/api/autocomplete/${entityName}?q=${encodeURIComponent(query)}`, {
                    target: `#autocomplete-${input.id}`,
                    swap: 'innerHTML'
                });
            }
        }, 300);
    });
}

// Theme switching (optional)
function toggleTheme() {
    const html = document.documentElement;
    const currentTheme = html.getAttribute('data-theme');
    const newTheme = currentTheme === 'wincasa' ? 'dark' : 'wincasa';
    
    html.setAttribute('data-theme', newTheme);
    localStorage.setItem('wincasa-theme', newTheme);
    
    showToast(`🎨 Theme geändert zu: ${newTheme}`, 'info');
}

// Load saved theme
const savedTheme = localStorage.getItem('wincasa-theme');
if (savedTheme) {
    document.documentElement.setAttribute('data-theme', savedTheme);
}

console.log('✅ WINCASA HTMX JavaScript loaded successfully');
"""
        
        with open(self.output_dir / "assets" / "app.js", 'w', encoding='utf-8') as f:
            f.write(js_content)
            
    def generate_templates(self):
        """Generate Jinja2 templates"""
        logger.info("Creating template directory structure...")
        
        template_dir = Path(__file__).parent / "templates"
        template_dir.mkdir(exist_ok=True)
        
        # Main layout template with DaisyUI
        layout_template = """<!DOCTYPE html>
<html lang="de" data-theme="wincasa">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdn.jsdelivr.net/npm/daisyui@4.12.14/dist/full.min.css" rel="stylesheet" type="text/css" />
    <link href="/assets/styles.css" rel="stylesheet">
    <script src="https://unpkg.com/htmx.org@1.9.10"></script>
    <script src="/assets/app.js"></script>
</head>
<body class="bg-base-100">
    <!-- Navigation -->
    <div class="navbar bg-base-300 shadow-lg">
        <div class="navbar-start">
            <div class="dropdown">
                <div tabindex="0" role="button" class="btn btn-ghost lg:hidden">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h8m-8 6h16"></path>
                    </svg>
                </div>
                <ul tabindex="0" class="menu menu-sm dropdown-content mt-3 z-[1] p-2 shadow bg-base-100 rounded-box w-52">
                    <li><a href="#search">🔍 Suche</a></li>
                    <li><a href="#analytics">📊 Analytics</a></li>
                    <li><a href="#reports">📋 Reports</a></li>
                </ul>
            </div>
            <a class="btn btn-ghost text-xl font-bold">🏠 WINCASA</a>
        </div>
        <div class="navbar-center hidden lg:flex">
            <ul class="menu menu-horizontal px-1">
                <li><a href="#search" class="btn btn-ghost">🔍 Suche</a></li>
                <li><a href="#analytics" class="btn btn-ghost">📊 Analytics</a></li>
                <li><a href="#reports" class="btn btn-ghost">📋 Reports</a></li>
            </ul>
        </div>
        <div class="navbar-end">
            <div class="dropdown dropdown-end">
                <div tabindex="0" role="button" class="btn btn-ghost btn-circle">
                    <div class="indicator">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-5 5v-5z"></path>
                        </svg>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Hero Section -->
    <div class="wincasa-hero">
        <div class="hero-content text-center">
            <div class="max-w-md">
                <h1 class="text-5xl font-bold">{{ title }}</h1>
                <p class="py-6">Intelligentes Property Management System mit AI-powered Query Engine</p>
                <div class="stats shadow">
                    <div class="stat">
                        <div class="stat-title">Eigentümer</div>
                        <div class="stat-value text-primary">311</div>
                    </div>
                    <div class="stat">
                        <div class="stat-title">Mieter</div>
                        <div class="stat-value text-secondary">189</div>
                    </div>
                    <div class="stat">
                        <div class="stat-title">Objekte</div>
                        <div class="stat-value text-accent">77</div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Main Content -->
    <main class="container mx-auto px-4 py-8">
        <div class="property-grid">
            {% for entity in business_entities %}
            {% if entity.form_type == 'search' %}
            <div class="wincasa-card">
                <div class="card-body">
                    <h2 class="card-title">
                        {% if entity.name == 'mieter' %}🏠{% elif entity.name == 'eigentümer' %}👤{% elif entity.name == 'wohnung' %}🏘️{% elif entity.name == 'objekt' %}🏢{% else %}📋{% endif %}
                        {{ entity.display_name }}
                    </h2>
                    
                    <!-- Form Container -->
                    <div hx-get="/components/{{ entity.name }}_form.html" 
                         hx-target="#form_{{ entity.name }}" 
                         hx-trigger="load"
                         class="wincasa-form">
                        <div id="form_{{ entity.name }}" class="loading loading-spinner loading-lg">
                            <div class="skeleton h-32 w-full"></div>
                        </div>
                    </div>
                    
                    <!-- Results Container -->
                    <div id="results_{{ entity.name }}" class="wincasa-results"></div>
                </div>
            </div>
            {% endif %}
            {% endfor %}
        </div>
        
        <!-- Analytics Dashboard -->
        <div class="divider"></div>
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-8">
            <div class="card bg-base-100 shadow-xl">
                <div class="card-body">
                    <h3 class="card-title">📊 Query Analytics</h3>
                    <div class="stats stats-vertical lg:stats-horizontal shadow">
                        <div class="stat">
                            <div class="stat-title">Heute</div>
                            <div class="stat-value text-sm">0 Queries</div>
                            <div class="stat-desc">↗︎ 0% seit gestern</div>
                        </div>
                        <div class="stat">
                            <div class="stat-title">Diese Woche</div>
                            <div class="stat-value text-sm">0 Queries</div>
                            <div class="stat-desc">↗︎ 0% seit letzter Woche</div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="card bg-base-100 shadow-xl">
                <div class="card-body">
                    <h3 class="card-title">⚡ System Status</h3>
                    <div class="flex flex-col gap-2">
                        <div class="flex justify-between items-center">
                            <span>Query Engine</span>
                            <div class="badge badge-success">Online</div>
                        </div>
                        <div class="flex justify-between items-center">
                            <span>Knowledge Base</span>
                            <div class="badge badge-success">400+ Mappings</div>
                        </div>
                        <div class="flex justify-between items-center">
                            <span>Database</span>
                            <div class="badge badge-success">Connected</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </main>
    
    <!-- Footer -->
    <footer class="footer footer-center p-10 bg-base-200 text-base-content">
        <aside>
            <p class="font-bold">
                WINCASA Property Management {{ version }}
                <br/>Powered by HTMX + DaisyUI
            </p>
            <p>Copyright © 2025 - All rights reserved</p>
        </aside>
    </footer>
</body>
</html>"""

        with open(template_dir / "layout.html", 'w', encoding='utf-8') as f:
            f.write(layout_template)
            
        # Query form template with DaisyUI
        form_template = """<form hx-post="{{ endpoint }}" 
      hx-target="{{ target }}" 
      hx-indicator="#loading-{{ entity.name }}"
      id="{{ form_id }}"
      class="wincasa-search-form">
    
    {% for field in entity.fields %}
    <fieldset class="fieldset">
        <label class="label german-label" for="{{ field.name }}">
            <span>{{ field.label }}</span>
            {% if field.required %}<span class="text-error">*</span>{% endif %}
        </label>
        
        {% if field.type == 'currency' %}
        <input type="number" 
               id="{{ field.name }}" 
               name="{{ field.name }}" 
               class="input input-bordered currency-input"
               placeholder="0,00"
               step="0.01"
               min="0"
               onblur="validateCurrency(this)"
               {% if field.required %}required{% endif %}>
        
        {% elif field.type == 'date' %}
        <input type="date" 
               id="{{ field.name }}" 
               name="{{ field.name }}" 
               class="input input-bordered"
               {% if field.required %}required{% endif %}>
        
        {% elif field.type == 'number' %}
        <input type="number" 
               id="{{ field.name }}" 
               name="{{ field.name }}" 
               class="input input-bordered"
               placeholder="Nummer eingeben"
               {% if field.required %}required{% endif %}>
               
        {% elif field.type == 'email' %}
        <input type="email" 
               id="{{ field.name }}" 
               name="{{ field.name }}" 
               class="input input-bordered"
               placeholder="email@beispiel.de"
               {% if field.required %}required{% endif %}>
               
        {% elif field.type == 'tel' %}
        <input type="tel" 
               id="{{ field.name }}" 
               name="{{ field.name }}" 
               class="input input-bordered"
               placeholder="+49 123 456789"
               {% if field.required %}required{% endif %}>
               
        {% else %}
        <input type="text" 
               id="{{ field.name }}" 
               name="{{ field.name }}" 
               class="input input-bordered"
               placeholder="{{ field.label }} eingeben"
               {% if field.required %}required{% endif %}>
        {% endif %}
        
        {% if field.source_file %}
        <label class="label">
            <span class="label-text-alt">Quelle: {{ field.source_file }}</span>
        </label>
        {% endif %}
    </fieldset>
    {% endfor %}
    
    <div class="form-actions col-span-full flex gap-4 justify-end mt-6">
        <button type="submit" class="btn btn-primary">
            <span class="htmx-indicator loading loading-spinner loading-xs" id="loading-{{ entity.name }}"></span>
            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
            </svg>
            Suchen
        </button>
        <button type="reset" class="btn btn-outline">
            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
            </svg>
            Zurücksetzen
        </button>
        
        <!-- Quick Search Chips -->
        <div class="dropdown dropdown-end">
            <div tabindex="0" role="button" class="btn btn-ghost btn-sm">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
                Vorlagen
            </div>
            <ul tabindex="0" class="dropdown-content z-[1] menu p-2 shadow bg-base-100 rounded-box w-52">
                {% if entity.name == 'mieter' %}
                <li><a onclick="setQuickSearch('{{ entity.name }}', 'Müller')">Mieter "Müller"</a></li>
                <li><a onclick="setQuickSearch('{{ entity.name }}', 'Berlin')">Mieter in Berlin</a></li>
                <li><a onclick="setQuickSearch('{{ entity.name }}', 'aktuelle')">Aktuelle Mieter</a></li>
                {% elif entity.name == 'eigentümer' %}
                <li><a onclick="setQuickSearch('{{ entity.name }}', 'WEG')">WEG Eigentümer</a></li>
                <li><a onclick="setQuickSearch('{{ entity.name }}', 'Portfolio')">Portfolio Übersicht</a></li>
                {% elif entity.name == 'wohnung' %}
                <li><a onclick="setQuickSearch('{{ entity.name }}', 'Leerstand')">Leerstehende Wohnungen</a></li>
                <li><a onclick="setQuickSearch('{{ entity.name }}', '3 Zimmer')">3-Zimmer Wohnungen</a></li>
                {% endif %}
            </ul>
        </div>
    </div>
</form>"""

        with open(template_dir / "query_form.html", 'w', encoding='utf-8') as f:
            f.write(form_template)
            
        # Result table template with DaisyUI
        table_template = """<div class="results-container">
    <div class="flex justify-between items-center mb-4">
        <h3 class="text-lg font-semibold">
            📊 Ergebnisse: {{ entity.display_name }}
        </h3>
        
        <!-- Export Options -->
        <div class="dropdown dropdown-end">
            <div tabindex="0" role="button" class="btn btn-sm btn-outline">
                <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                </svg>
                Export
            </div>
            <ul tabindex="0" class="dropdown-content z-[1] menu p-2 shadow bg-base-100 rounded-box w-52">
                <li><a hx-get="/api/export/{{ entity.name }}/csv" hx-target="_blank">📄 CSV Export</a></li>
                <li><a hx-get="/api/export/{{ entity.name }}/excel" hx-target="_blank">📊 Excel Export</a></li>
                <li><a hx-get="/api/export/{{ entity.name }}/pdf" hx-target="_blank">📋 PDF Report</a></li>
            </ul>
        </div>
    </div>
    
    <!-- Results Stats -->
    <div class="stats stats-horizontal shadow mb-4" 
         hx-get="/api/stats/{{ entity.name }}" 
         hx-trigger="load">
        <div class="stat">
            <div class="stat-title">Gefundene Einträge</div>
            <div class="stat-value text-primary">-</div>
            <div class="stat-desc">wird geladen...</div>
        </div>
        
        <div class="stat">
            <div class="stat-title">Ladezeit</div>
            <div class="stat-value text-secondary">-</div>
            <div class="stat-desc">Millisekunden</div>
        </div>
    </div>
    
    <!-- Table Container -->
    <div class="overflow-x-auto bg-base-100 rounded-lg shadow">
        <table class="wincasa-table {% if entity.name == 'mieter' %}mieter-table{% elif entity.name == 'eigentümer' %}eigentuemer-table{% elif entity.name == 'wohnung' %}wohnung-table{% else %}table{% endif %}" 
               id="{{ table_id }}">
            <thead>
                <tr>
                    <th>
                        <label>
                            <input type="checkbox" class="checkbox" onclick="toggleAllRows('{{ entity.name }}')" />
                        </label>
                    </th>
                    {% for field in fields %}
                    <th class="cursor-pointer hover:bg-base-200" 
                        onclick="sortTable('{{ entity.name }}', '{{ field.name }}')">
                        <div class="flex items-center gap-2">
                            {{ field.label }}
                            <svg class="w-3 h-3 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4"></path>
                            </svg>
                        </div>
                    </th>
                    {% endfor %}
                    <th>Aktionen</th>
                </tr>
            </thead>
            <tbody hx-get="/api/results/{{ entity.name }}" 
                   hx-trigger="load"
                   hx-target="this"
                   hx-indicator="#loading-table-{{ entity.name }}">
                <tr>
                    <td colspan="{{ fields|length + 2 }}" class="text-center py-8">
                        <div class="flex flex-col items-center gap-4">
                            <span class="loading loading-spinner loading-lg" id="loading-table-{{ entity.name }}"></span>
                            <span class="text-base-content/60">Lade Daten...</span>
                        </div>
                    </td>
                </tr>
            </tbody>
        </table>
    </div>
    
    <!-- Pagination -->
    <div class="flex justify-between items-center mt-4">
        <div class="text-sm text-base-content/70">
            Zeige <span id="rows-info-{{ entity.name }}">0</span> von <span id="total-rows-{{ entity.name }}">0</span> Einträgen
        </div>
        
        <div class="join" 
             hx-get="/api/pagination/{{ entity.name }}" 
             hx-target="this"
             hx-trigger="load">
            <button class="join-item btn btn-sm">«</button>
            <button class="join-item btn btn-sm">Seite 1</button>
            <button class="join-item btn btn-sm">»</button>
        </div>
        
        <!-- Rows per page -->
        <select class="select select-sm select-bordered" onchange="changePageSize('{{ entity.name }}', this.value)">
            <option value="10">10 pro Seite</option>
            <option value="25" selected>25 pro Seite</option>
            <option value="50">50 pro Seite</option>
            <option value="100">100 pro Seite</option>
        </select>
    </div>
    
    <!-- Bulk Actions (when rows selected) -->
    <div id="bulk-actions-{{ entity.name }}" class="alert alert-info mt-4 hidden">
        <svg class="stroke-current shrink-0 w-6 h-6" fill="none" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
        </svg>
        <span>
            <span id="selected-count-{{ entity.name }}">0</span> Einträge ausgewählt
        </span>
        <div>
            <button class="btn btn-sm btn-outline" onclick="exportSelected('{{ entity.name }}')">Ausgewählte exportieren</button>
            <button class="btn btn-sm btn-outline" onclick="clearSelection('{{ entity.name }}')">Auswahl aufheben</button>
        </div>
    </div>
</div>"""

        with open(template_dir / "result_table.html", 'w', encoding='utf-8') as f:
            f.write(table_template)
            
    def generate_api_endpoints_manifest(self):
        """Generate manifest of required API endpoints for CGI implementation"""
        logger.info("Generating API endpoints manifest...")
        
        endpoints = {
            "query_endpoints": [],
            "result_endpoints": [],
            "component_endpoints": []
        }
        
        for model in self.ui_models:
            # Query endpoints
            endpoints["query_endpoints"].append({
                "path": f"/api/query/{model.name}",
                "method": "POST",
                "handler": f"query_{model.name}",
                "parameters": [field['name'] for field in model.fields],
                "returns": "JSON result set"
            })
            
            # Result endpoints
            endpoints["result_endpoints"].append({
                "path": f"/api/results/{model.name}",
                "method": "GET", 
                "handler": f"results_{model.name}",
                "parameters": ["page", "limit"],
                "returns": "HTML table rows"
            })
            
            # Component endpoints
            endpoints["component_endpoints"].append({
                "path": f"/components/{model.name}_form.html",
                "method": "GET",
                "handler": "static_file",
                "returns": "HTML form component"
            })
            
        manifest_path = self.output_dir / "api" / "endpoints_manifest.json"
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(endpoints, f, indent=2, ensure_ascii=False)
            
    def generate_all(self):
        """Generate complete HTMX application"""
        logger.info("Starting HTMX Static Generator...")
        
        # Load knowledge systems
        self.load_knowledge_systems()
        
        # Generate UI models
        self.ui_models = self.generate_ui_models()
        
        # Generate templates first
        self.generate_templates()
        
        # Generate HTML components
        self.generate_main_layout()
        self.generate_query_forms()
        self.generate_result_tables()
        
        # Generate assets
        self.generate_css_assets()
        self.generate_js_assets()
        
        # Generate API manifest
        self.generate_api_endpoints_manifest()
        
        logger.info(f"HTMX application generated in: {self.output_dir}")
        logger.info(f"Generated {len(self.ui_models)} UI models")
        logger.info("Ready for CGI API implementation")

def main():
    """CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="WINCASA HTMX Static Generator")
    parser.add_argument("--output", "-o", default="dist/htmx", 
                       help="Output directory")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Verbose logging")
    
    args = parser.parse_args()
    
    # Setup logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Generate HTMX application
    generator = HTMXStaticGenerator(args.output)
    generator.generate_all()
    
    print(f"✅ HTMX application generated successfully in: {args.output}")
    print("🚀 Next: Implement CGI API endpoints")

if __name__ == "__main__":
    main()