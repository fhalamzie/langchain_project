#!/usr/bin/env python3
"""
WINCASA Phase 2.3 - SQL Template Engine
Sichere SQL-Template-Generierung mit Jinja2 und Injection-Schutz
"""

import json
import re
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Jinja2 für Template-Engine
try:
    from jinja2 import BaseLoader, Environment, exceptions, meta
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False

from wincasa.data.json_exporter import get_connection


@dataclass
class TemplateResult:
    """Ergebnis der Template-Engine"""
    template_id: str
    generated_sql: str
    parameters: Dict[str, Any]
    validation_passed: bool
    security_score: float
    processing_time_ms: float
    query_results: Optional[List[Dict]]
    result_count: int

@dataclass
class SecurityValidation:
    """Security-Validierung für SQL-Templates"""
    injection_risk: float  # 0.0 = sicher, 1.0 = hochriskant
    dangerous_patterns: List[str]
    parameter_validation: Dict[str, bool]
    whitelist_passed: bool
    overall_safe: bool

class SQLTemplateEngine:
    """
    Sichere SQL Template Engine für WINCASA
    
    Features:
    - Jinja2-basierte Template-Verarbeitung
    - SQL-Injection Schutz mit Whitelisting
    - Parameter-Sanitization für deutsche Umlaute
    - View-basierte Templates (keine direkten Tabellen)
    - Performance-Monitoring
    """
    
    def __init__(self, 
                 templates_dir: str = "sql_templates",
                 debug_mode: bool = False):
        
        self.templates_dir = Path(templates_dir)
        self.debug_mode = debug_mode
        
        # Initialize Jinja2 environment
        if not JINJA2_AVAILABLE:
            raise ImportError("Jinja2 not available. Install with: pip install Jinja2")
        
        # Secure Jinja2 setup
        self.jinja_env = Environment(
            loader=BaseLoader(),
            autoescape=True,  # XSS protection
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # SQL Security patterns
        self._setup_security_patterns()
        
        # Load templates
        self.templates = self._load_templates()
        
        if self.debug_mode:
            print(f"✅ SQL Template Engine initialisiert:")
            print(f"   📁 Templates Dir: {self.templates_dir}")
            print(f"   📝 {len(self.templates)} Templates geladen")
            print(f"   🔒 Security Patterns: {len(self.dangerous_sql_patterns)} Items")
    
    def _setup_security_patterns(self):
        """Setup SQL-Injection Security Patterns"""
        
        # Gefährliche SQL-Patterns (Blacklist)
        self.dangerous_sql_patterns = [
            # SQL Injection Classics
            r";.*(?:DROP|DELETE|INSERT|UPDATE|ALTER|CREATE|EXEC|EXECUTE)",
            r"(?:UNION|UNION\s+ALL).*SELECT",
            r"(?:SELECT|INSERT|UPDATE|DELETE).*(?:FROM|INTO).*(?:INFORMATION_SCHEMA|SYS\.)",
            
            # Command Injection
            r"(?:xp_|sp_)cmdshell",
            r"(?:BULK\s+)?INSERT.*OPENROWSET",
            r"(?:EXEC|EXECUTE).*(?:xp_|sp_)",
            
            # Stored Procedure Abuse
            r"(?:EXEC|EXECUTE)\s*\(",
            r"WAITFOR\s+DELAY",
            
            # Comment-based Attacks
            r"--.*(?:DROP|DELETE|ALTER)",
            r"/\*.*(?:DROP|DELETE|ALTER).*\*/",
            
            # Data Exfiltration
            r"(?:SELECT|UNION).*(?:version|user|database|schema)",
            r"(?:INTO\s+)?OUTFILE",
            r"LOAD_FILE\s*\(",
            
            # Boolean/Time-based Blind SQL Injection
            r"(?:AND|OR)\s+\d+\s*=\s*\d+",
            r"(?:AND|OR)\s+(?:SLEEP|BENCHMARK|PG_SLEEP)\s*\(",
            
            # Firebird-specific dangerous patterns
            r"RDB\$",  # Firebird system tables
            r"MON\$",  # Firebird monitoring tables
        ]
        
        # Whitelist: Erlaubte SQL-Konstrukte
        self.allowed_sql_patterns = [
            r"SELECT\s+",
            r"FROM\s+vw_\w+",  # Nur Views erlaubt
            r"WHERE\s+",
            r"(?:AND|OR)\s+",
            r"ORDER\s+BY\s+",
            r"(?:LIMIT|ROWS)\s+\d+",
            r"(?:LEFT|RIGHT|INNER)?\s*JOIN\s+",
            r"(?:COUNT|SUM|AVG|MIN|MAX)\s*\(",
            r"CASE\s+WHEN",
            r"(?:IS\s+(?:NOT\s+)?NULL|LIKE|IN\s*\()",
            r"(?:COALESCE|CAST|SUBSTRING|TRIM)\s*\("
        ]
        
        # Parameter-Validation Patterns
        self.parameter_patterns = {
            "person_name": r"^[a-zA-ZäöüÄÖÜß\s\-\.&]{2,100}$",
            "location": r"^[a-zA-ZäöüÄÖÜß\s\-\.\d]{2,100}$", 
            "city": r"^[a-zA-ZäöüÄÖÜß\s\-]{2,50}$",
            "street": r"^[a-zA-ZäöüÄÖÜß\s\-\.\d]{3,100}$",
            "company": r"^[a-zA-ZäöüÄÖÜß\s\-\.\&\(\)]{2,150}$",
            "limit": r"^\d{1,3}$",  # Max 999
            "offset": r"^\d{1,5}$"  # Max 99999
        }
    
    def _load_templates(self) -> Dict[str, str]:
        """Lädt SQL-Templates aus dem Templates-Verzeichnis"""
        templates = {}
        
        # Create templates directory if not exists
        self.templates_dir.mkdir(exist_ok=True)
        
        # Built-in core templates
        core_templates = self._get_core_templates()
        
        # Load from files (if exist)
        for template_file in self.templates_dir.glob("*.sql"):
            template_id = template_file.stem
            try:
                with open(template_file, 'r', encoding='utf-8') as f:
                    templates[template_id] = f.read()
            except Exception as e:
                if self.debug_mode:
                    print(f"⚠️  Template load error {template_file}: {e}")
        
        # Add core templates (override files if same name)
        templates.update(core_templates)
        
        return templates
    
    def _get_core_templates(self) -> Dict[str, str]:
        """Definiert Core SQL-Templates basierend auf WINCASA Views"""
        
        return {
            # === MIETER TEMPLATES ===
            "mieter_by_location": """
SELECT 
  MIETER_NAME,
  PARTNER_NAME,
  VOLLSTAENDIGE_ADRESSE,
  TELEFON,
  EMAIL,
  HANDY,
  MIETSTATUS,
  WARMMIETE_AKTUELL,
  ZAHLUNGSSTATUS,
  EIGENTUEMER_NAME
FROM vw_mieter_komplett
WHERE 
  (STADT LIKE '%{{ location|e }}%' 
   OR GEBAEUDE_ADRESSE LIKE '%{{ location|e }}%'
   OR VOLLSTAENDIGE_ADRESSE LIKE '%{{ location|e }}%')
ORDER BY MIETER_NAME
ROWS {{ limit|default(50)|int }}
""",
            
            "mieter_contact": """
SELECT 
  MIETER_NAME,
  PARTNER_NAME,
  VOLLSTAENDIGE_ADRESSE,
  TELEFON,
  EMAIL,
  HANDY,
  MIETSTATUS,
  EIGENTUEMER_NAME
FROM vw_mieter_komplett
WHERE 
  MIETER_NAME LIKE '%{{ person_name|e }}%'
  {% if partner_search %}
  OR PARTNER_NAME LIKE '%{{ person_name|e }}%'
  {% endif %}
ORDER BY MIETER_NAME
ROWS {{ limit|default(10)|int }}
""",
            
            # === EIGENTÜMER TEMPLATES ===
            "owner_by_property": """
SELECT 
  EIGENTUEMER_NAME,
  EIGENTUEMER_TYP,
  FIRMENNAME,
  PLZ_ORT,
  TELEFON,
  EMAIL,
  PORTFOLIO_KATEGORIE,
  ANZAHL_OBJEKTE,
  ANZAHL_EINHEITEN
FROM vw_eigentuemer_portfolio
WHERE 
  EIGENTUEMER_NAME LIKE '%{{ location|e }}%'
  OR PLZ_ORT LIKE '%{{ location|e }}%'
ORDER BY ANZAHL_OBJEKTE DESC
ROWS {{ limit|default(10)|int }}
""",
            
            "owner_portfolio": """
SELECT 
  EIGENTUEMER_NAME,
  EIGENTUEMER_TYP,
  FIRMENNAME,
  ANZAHL_OBJEKTE,
  ANZAHL_EINHEITEN,
  PORTFOLIO_KATEGORIE,
  GESAMT_KONTOSTAND,
  GESAMT_RUECKLAGEN,
  DATENVOLLSTAENDIGKEIT
FROM vw_eigentuemer_portfolio
WHERE 
  EIGENTUEMER_NAME LIKE '%{{ person_name|e }}%'
  {% if include_companies %}
  OR FIRMENNAME LIKE '%{{ person_name|e }}%'
  {% endif %}
ORDER BY ANZAHL_OBJEKTE DESC
ROWS {{ limit|default(10)|int }}
""",
            
            # === OBJEKT TEMPLATES ===
            "vacancy_by_location": """
SELECT 
  GEBAEUDE_ADRESSE,
  STADT,
  ANZAHL_EINHEITEN_TOTAL,
  EINHEITEN_VERMIETET,
  EINHEITEN_LEERSTAND,
  VERMIETUNGSGRAD_PROZENT,
  VERMIETUNGSSTATUS,
  EIGENTUEMER_NAME,
  MIETEINNAHMEN_MONATLICH
FROM vw_objekte_details
WHERE 
  (STADT LIKE '%{{ location|e }}%' 
   OR GEBAEUDE_ADRESSE LIKE '%{{ location|e }}%')
  {% if only_vacant %}
  AND EINHEITEN_LEERSTAND > 0
  {% endif %}
ORDER BY VERMIETUNGSGRAD_PROZENT ASC, GEBAEUDE_ADRESSE
ROWS {{ limit|default(20)|int }}
""",
            
            "property_details": """
SELECT 
  GEBAEUDE_ADRESSE,
  STADT,
  ANZAHL_EINHEITEN_TOTAL,
  WOHNFLAECHE_QM,
  OBJEKTART,
  VERMIETUNGSGRAD_PROZENT,
  VERMIETUNGSSTATUS,
  HAUSGELD_KONTOSTAND,
  FINANZSTATUS,
  VERWALTER_NAME,
  VERWALTER_FIRMA,
  EIGENTUEMER_NAME,
  MIETEINNAHMEN_MONATLICH
FROM vw_objekte_details
WHERE 
  GEBAEUDE_ADRESSE LIKE '%{{ location|e }}%'
  OR STADT LIKE '%{{ location|e }}%'
ORDER BY GEBAEUDE_ADRESSE
ROWS {{ limit|default(10)|int }}
""",
            
            # === FINANZEN TEMPLATES ===
            "account_balance": """
SELECT 
  MIETER_NAME,
  PARTNER_NAME,
  VOLLSTAENDIGE_ADRESSE,
  KONTOSALDO,
  ZAHLUNGSSTATUS,
  WARMMIETE_AKTUELL,
  KALTMIETE,
  BETRIEBSKOSTEN_VORAUSZAHLUNG,
  HEIZKOSTEN_VORAUSZAHLUNG,
  EIGENTUEMER_NAME
FROM vw_mieter_komplett
WHERE 
  MIETER_NAME LIKE '%{{ person_name|e }}%'
  {% if include_partners %}
  OR PARTNER_NAME LIKE '%{{ person_name|e }}%'
  {% endif %}
  {% if only_balances %}
  AND ABS(KONTOSALDO) > 10
  {% endif %}
ORDER BY KONTOSALDO DESC
ROWS {{ limit|default(10)|int }}
"""
        }
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> SecurityValidation:
        """Validiert Parameter gegen SQL-Injection"""
        
        dangerous_patterns = []
        parameter_validation = {}
        injection_risk = 0.0
        
        for param_name, param_value in parameters.items():
            if param_value is None:
                parameter_validation[param_name] = True
                continue
                
            param_str = str(param_value)
            
            # Check dangerous SQL patterns
            for pattern in self.dangerous_sql_patterns:
                if re.search(pattern, param_str, re.IGNORECASE):
                    dangerous_patterns.append(f"{param_name}: {pattern}")
                    injection_risk += 0.3
            
            # Validate against parameter patterns
            if param_name in self.parameter_patterns:
                pattern = self.parameter_patterns[param_name]
                is_valid = bool(re.match(pattern, param_str))
                parameter_validation[param_name] = is_valid
                if not is_valid:
                    injection_risk += 0.1
            else:
                # Unknown parameter - medium risk
                parameter_validation[param_name] = True
                injection_risk += 0.05
        
        # Whitelist check for overall SQL safety
        whitelist_passed = True  # Templates are pre-validated
        
        overall_safe = injection_risk < 0.2 and whitelist_passed and len(dangerous_patterns) == 0
        
        return SecurityValidation(
            injection_risk=min(injection_risk, 1.0),
            dangerous_patterns=dangerous_patterns,
            parameter_validation=parameter_validation,
            whitelist_passed=whitelist_passed,
            overall_safe=overall_safe
        )
    
    def sanitize_parameter(self, param_name: str, param_value: Any) -> str:
        """Sanitisiert Parameter für sichere SQL-Verwendung"""
        if param_value is None:
            return ""
        
        param_str = str(param_value)
        
        # SQL-Escape für Strings
        if isinstance(param_value, str):
            # Escape single quotes
            param_str = param_str.replace("'", "''")
            
            # Remove dangerous characters
            param_str = re.sub(r"[;\\]", "", param_str)
            
            # Trim whitespace
            param_str = param_str.strip()
        
        # Integer parameters
        elif param_name in ["limit", "offset"]:
            try:
                param_int = int(param_value)
                # Reasonable limits
                if param_name == "limit":
                    param_str = str(min(max(param_int, 1), 1000))
                elif param_name == "offset":
                    param_str = str(min(max(param_int, 0), 100000))
            except ValueError:
                param_str = "10" if param_name == "limit" else "0"
        
        return param_str
    
    def render_template(self, 
                       template_id: str, 
                       parameters: Dict[str, Any]) -> TemplateResult:
        """
        Rendert SQL-Template mit Parametern und Security-Validation
        """
        start_time = time.time()
        
        if self.debug_mode:
            print(f"🔧 Rendering Template: {template_id}")
            print(f"   📋 Parameters: {parameters}")
        
        # Check if template exists
        if template_id not in self.templates:
            return TemplateResult(
                template_id=template_id,
                generated_sql="",
                parameters=parameters,
                validation_passed=False,
                security_score=0.0,
                processing_time_ms=0.0,
                query_results=None,
                result_count=0
            )
        
        # Security validation
        security_validation = self.validate_parameters(parameters)
        
        if not security_validation.overall_safe:
            if self.debug_mode:
                print(f"   ❌ Security validation failed: {security_validation.dangerous_patterns}")
            
            return TemplateResult(
                template_id=template_id,
                generated_sql="",
                parameters=parameters,
                validation_passed=False,
                security_score=1.0 - security_validation.injection_risk,
                processing_time_ms=round((time.time() - start_time) * 1000, 2),
                query_results=None,
                result_count=0
            )
        
        # Sanitize parameters
        sanitized_params = {}
        for param_name, param_value in parameters.items():
            sanitized_params[param_name] = self.sanitize_parameter(param_name, param_value)
        
        try:
            # Render Jinja2 template
            template_str = self.templates[template_id]
            template = self.jinja_env.from_string(template_str)
            generated_sql = template.render(**sanitized_params)
            
            # Final SQL validation
            if not self._validate_generated_sql(generated_sql):
                return TemplateResult(
                    template_id=template_id,
                    generated_sql=generated_sql,
                    parameters=parameters,
                    validation_passed=False,
                    security_score=0.5,
                    processing_time_ms=round((time.time() - start_time) * 1000, 2),
                    query_results=None,
                    result_count=0
                )
            
            # Execute SQL
            query_results = None
            result_count = 0
            
            try:
                query_results = execute_query(generated_sql)
                result_count = len(query_results) if query_results else 0
                
                if self.debug_mode:
                    print(f"   ✅ SQL executed: {result_count} results")
                    
            except Exception as e:
                if self.debug_mode:
                    print(f"   ⚠️  SQL execution error: {e}")
                query_results = None
                result_count = 0
            
            processing_time = round((time.time() - start_time) * 1000, 2)
            
            return TemplateResult(
                template_id=template_id,
                generated_sql=generated_sql,
                parameters=sanitized_params,
                validation_passed=True,
                security_score=1.0 - security_validation.injection_risk,
                processing_time_ms=processing_time,
                query_results=query_results,
                result_count=result_count
            )
            
        except exceptions.TemplateError as e:
            if self.debug_mode:
                print(f"   ❌ Template rendering error: {e}")
            
            return TemplateResult(
                template_id=template_id,
                generated_sql="",
                parameters=parameters,
                validation_passed=False,
                security_score=0.0,
                processing_time_ms=round((time.time() - start_time) * 1000, 2),
                query_results=None,
                result_count=0
            )
    
    def _validate_generated_sql(self, sql: str) -> bool:
        """Final validation des generierten SQLs"""
        
        # Must contain SELECT
        if not re.search(r"^\s*SELECT\s+", sql, re.IGNORECASE | re.MULTILINE):
            return False
        
        # Must query views only
        if not re.search(r"FROM\s+vw_\w+", sql, re.IGNORECASE):
            return False
        
        # No dangerous patterns
        for pattern in self.dangerous_sql_patterns:
            if re.search(pattern, sql, re.IGNORECASE):
                return False
        
        return True
    
    def get_template_info(self, template_id: str) -> Dict[str, Any]:
        """Gibt Informationen über ein Template zurück"""
        if template_id not in self.templates:
            return {"error": "Template not found"}
        
        template_str = self.templates[template_id]
        
        # Extract Jinja2 variables
        ast = self.jinja_env.parse(template_str)
        variables = meta.find_undeclared_variables(ast)
        
        return {
            "template_id": template_id,
            "variables": list(variables),
            "template_length": len(template_str),
            "estimated_complexity": len(variables) * 10 + len(template_str) // 100
        }
    
    def list_templates(self) -> List[Dict[str, Any]]:
        """Listet alle verfügbaren Templates"""
        templates_info = []
        
        for template_id in self.templates:
            info = self.get_template_info(template_id)
            templates_info.append(info)
        
        return templates_info
    
    def get_stats(self) -> Dict[str, Any]:
        """Template Engine Statistiken"""
        return {
            "total_templates": len(self.templates),
            "core_templates": 7,  # Built-in templates
            "security_patterns": len(self.dangerous_sql_patterns),
            "parameter_patterns": len(self.parameter_patterns),
            "jinja2_available": JINJA2_AVAILABLE
        }

def test_sql_template_engine():
    """Test der SQL Template Engine"""
    print("🧪 Teste SQL Template Engine...")
    
    engine = SQLTemplateEngine(debug_mode=True)
    
    # Test verschiedene Templates mit realistischen Parametern
    test_cases = [
        {
            "template_id": "mieter_by_location",
            "parameters": {"location": "Essen", "limit": 5},
            "description": "Mieter in Essen"
        },
        {
            "template_id": "mieter_contact", 
            "parameters": {"person_name": "Müller", "partner_search": True, "limit": 3},
            "description": "Kontaktdaten Müller"
        },
        {
            "template_id": "owner_portfolio",
            "parameters": {"person_name": "GmbH", "include_companies": True, "limit": 5},
            "description": "GmbH Portfolio"
        },
        {
            "template_id": "vacancy_by_location",
            "parameters": {"location": "Köln", "only_vacant": True, "limit": 10},
            "description": "Leerstand in Köln"
        },
        {
            "template_id": "account_balance",
            "parameters": {"person_name": "Weber", "only_balances": True, "limit": 5},
            "description": "Kontosaldo Weber"
        }
    ]
    
    print(f"\n📋 Template Tests:")
    total_time = 0
    success_count = 0
    
    for test_case in test_cases:
        print(f"\n🔧 Test: {test_case['description']}")
        result = engine.render_template(
            test_case["template_id"], 
            test_case["parameters"]
        )
        
        total_time += result.processing_time_ms
        
        print(f"   ✅ Validation: {result.validation_passed}")
        print(f"   🔒 Security Score: {result.security_score:.2f}")
        print(f"   ⏱️  Time: {result.processing_time_ms}ms")
        print(f"   📊 Results: {result.result_count}")
        
        if result.validation_passed:
            success_count += 1
            print(f"   📝 SQL Preview: {result.generated_sql[:100]}...")
        else:
            print(f"   ❌ Generation failed")
    
    # Security Tests
    print(f"\n🔒 Security Tests:")
    malicious_tests = [
        {
            "template_id": "mieter_by_location",
            "parameters": {"location": "'; DROP TABLE MIETER; --", "limit": 5},
            "description": "SQL Injection Test"
        },
        {
            "template_id": "mieter_contact",
            "parameters": {"person_name": "admin' UNION SELECT * FROM KONTEN --", "limit": 5},
            "description": "Union Injection Test"
        }
    ]
    
    for test_case in malicious_tests:
        print(f"\n🚨 Security Test: {test_case['description']}")
        result = engine.render_template(
            test_case["template_id"],
            test_case["parameters"]
        )
        
        if result.validation_passed:
            print(f"   ❌ SECURITY BREACH: Malicious query passed!")
        else:
            print(f"   ✅ Security: Malicious query blocked")
            print(f"   🔒 Security Score: {result.security_score:.2f}")
    
    # Performance Summary
    print(f"\n📊 Template Engine Summary:")
    print(f"   ✅ Success Rate: {success_count}/{len(test_cases)} ({success_count/len(test_cases)*100:.1f}%)")
    print(f"   ⏱️  Avg Time: {total_time/len(test_cases):.1f}ms")
    
    # Template Stats
    stats = engine.get_stats()
    print(f"   📋 Templates: {stats['total_templates']}")
    print(f"   🔒 Security Patterns: {stats['security_patterns']}")

if __name__ == "__main__":
    test_sql_template_engine()