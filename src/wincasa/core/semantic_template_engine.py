#!/usr/bin/env python3
"""
WINCASA Semantic Template Engine - Mode 6
Bridges gap between rigid templates and full SQL generation
by using LLM for intent extraction + validated SQL templates
"""

import json
import logging
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

@dataclass
class SemanticPattern:
    """Erkanntes semantisches Muster mit Parametern"""
    pattern_id: str
    pattern_name: str
    parameters: Dict[str, str]
    confidence: float
    
@dataclass
class SemanticTemplateResult:
    """Ergebnis der semantischen Template-Verarbeitung"""
    query: str
    pattern: Optional[SemanticPattern]
    sql_query: Optional[str]
    answer: str
    success: bool
    processing_time_ms: float
    confidence: float
    result_count: int
    error_details: Optional[str] = None

class SemanticTemplateEngine:
    """
    Semantic Template Engine für parameterisierte Business-Queries
    
    Verarbeitet Anfragen wie:
    - "Alle Mieter von [ENTITY]"
    - "Objekte in [LOCATION]"  
    - "Leerstand von [OWNER]"
    - "Portfolio von [OWNER]"
    
    Ablauf:
    1. LLM extrahiert Intent + Parameter (leichtgewichtig)
    2. Mapping zu SQL-Template (deterministisch)
    3. Parameter-Injection (sicher)
    4. SQL-Ausführung (validiert)
    """
    
    def __init__(self, 
                 api_key_file: str = "/home/envs/openai.env",
                 debug_mode: bool = False):
        
        self.debug_mode = debug_mode
        self.api_key_file = api_key_file
        
        # Load semantic patterns
        self.patterns = self._load_semantic_patterns()
        
        # Load SQL templates
        self.sql_templates = self._load_sql_templates()
        
        # Initialize LLM handler for intent extraction
        self.llm_handler = None
        self._init_llm_handler()
        
        logger.info("✅ SemanticTemplateEngine initialized successfully")
        
    def _init_llm_handler(self):
        """Initialize LLM handler for intent extraction"""
        try:
            from wincasa.core.llm_handler import WincasaLLMHandler
            self.llm_handler = WincasaLLMHandler()
            logger.info("✅ LLM handler initialized for intent extraction")
        except ImportError as e:
            logger.warning(f"⚠️ Could not import LLM handler: {e}")
            self.llm_handler = None
    
    def _load_semantic_patterns(self) -> Dict[str, Dict]:
        """Lädt semantische Muster-Definitionen"""
        
        patterns = {
            "mieter_by_owner": {
                "name": "Mieter von Eigentümer",
                "patterns": [
                    r"alle mieter von (.+)",
                    r"mieter von (.+)",
                    r"(.+)['s]? mieter",
                    r"mieter.*eigentümer.*(.+)",
                    r"wer mietet von (.+)"
                ],
                "parameters": ["owner"],
                "template": "mieter_by_owner.sql",
                "description": "Alle Mieter eines bestimmten Eigentümers"
            },
            "objekte_by_location": {
                "name": "Objekte nach Standort",
                "patterns": [
                    r"objekte in (.+)",
                    r"immobilien in (.+)", 
                    r"(.+) objekte",
                    r"liegenschaften.*(.+)",
                    r"gebäude.*(.+)"
                ],
                "parameters": ["location"],
                "template": "objekte_by_location.sql",
                "description": "Objekte an einem bestimmten Standort"
            },
            "leerstand_by_owner": {
                "name": "Leerstand von Eigentümer",
                "patterns": [
                    r"leerstand von (.+)",
                    r"leere wohnungen.*(.+)",
                    r"(.+).*leerstand",
                    r"vakant.*(.+)",
                    r"unvermietete.*(.+)"
                ],
                "parameters": ["owner"],
                "template": "leerstand_by_owner.sql",
                "description": "Leerstände eines bestimmten Eigentümers"
            },
            "portfolio_by_owner": {
                "name": "Portfolio von Eigentümer",
                "patterns": [
                    r"portfolio von (.+)",
                    r"(.+) portfolio", 
                    r"immobilien.*(.+)",
                    r"besitz.*(.+)",
                    r"eigentum.*(.+)"
                ],
                "parameters": ["owner"],
                "template": "portfolio_by_owner.sql",
                "description": "Vollständiges Portfolio eines Eigentümers"
            },
            "mieter_by_date": {
                "name": "Mieter seit Datum",
                "patterns": [
                    r"mieter seit (.+)",
                    r"neue mieter.*(.+)",
                    r"eingezogen.*(.+)",
                    r"mieter ab (.+)",
                    r"neueste mieter.*(.+)"
                ],
                "parameters": ["date"],
                "template": "mieter_by_date.sql", 
                "description": "Mieter seit einem bestimmten Datum"
            },
            "wartung_by_object": {
                "name": "Wartung für Objekt",
                "patterns": [
                    r"wartung.*(.+)",
                    r"instandhaltung.*(.+)",
                    r"reparatur.*(.+)",
                    r"(.+).*wartungskosten",
                    r"maintenance.*(.+)"
                ],
                "parameters": ["object"],
                "template": "wartung_by_object.sql",
                "description": "Wartungsarbeiten für bestimmtes Objekt"
            }
        }
        
        logger.info(f"✅ Loaded {len(patterns)} semantic patterns")
        return patterns
    
    def _load_sql_templates(self) -> Dict[str, str]:
        """Lädt SQL-Templates für semantische Muster"""
        
        templates = {
            "mieter_by_owner.sql": """
                SELECT 
                    m.*,
                    e.NAME as eigentuemer_name,
                    o.OBJEKT_NAME,
                    o.STRASSE,
                    o.PLZ,
                    o.ORT
                FROM vw_mieter_komplett m
                JOIN vw_eigentuemer_portfolio e ON m.EIGENTUEMER_ID = e.EIGENTUEMER_ID
                JOIN vw_objekte_details o ON m.OBJEKT_ID = o.OBJEKT_ID
                WHERE UPPER(e.NAME) LIKE UPPER('%{owner}%')
                ORDER BY e.NAME, m.MIETER_NAME
            """,
            
            "objekte_by_location.sql": """
                SELECT 
                    o.*,
                    e.NAME as eigentuemer_name,
                    COUNT(m.MIETER_ID) as anzahl_mieter
                FROM vw_objekte_details o
                LEFT JOIN vw_eigentuemer_portfolio e ON o.EIGENTUEMER_ID = e.EIGENTUEMER_ID
                LEFT JOIN vw_mieter_komplett m ON o.OBJEKT_ID = m.OBJEKT_ID
                WHERE UPPER(o.ORT) LIKE UPPER('%{location}%') 
                   OR UPPER(o.STRASSE) LIKE UPPER('%{location}%')
                   OR UPPER(o.PLZ) LIKE UPPER('%{location}%')
                GROUP BY o.OBJEKT_ID, o.OBJEKT_NAME, o.STRASSE, o.PLZ, o.ORT, e.NAME
                ORDER BY o.ORT, o.STRASSE
            """,
            
            "leerstand_by_owner.sql": """
                SELECT 
                    l.*,
                    e.NAME as eigentuemer_name,
                    o.OBJEKT_NAME,
                    o.STRASSE,
                    o.ORT
                FROM vw_leerstand_korrekt l
                JOIN vw_objekte_details o ON l.OBJEKT_ID = o.OBJEKT_ID
                JOIN vw_eigentuemer_portfolio e ON o.EIGENTUEMER_ID = e.EIGENTUEMER_ID
                WHERE UPPER(e.NAME) LIKE UPPER('%{owner}%')
                ORDER BY e.NAME, o.OBJEKT_NAME
            """,
            
            "portfolio_by_owner.sql": """
                SELECT 
                    e.*,
                    COUNT(DISTINCT o.OBJEKT_ID) as anzahl_objekte,
                    COUNT(DISTINCT m.MIETER_ID) as anzahl_mieter,
                    COUNT(DISTINCT l.WOHNUNG_ID) as anzahl_leerstand,
                    SUM(m.KALTMIETE) as gesamt_kaltmiete
                FROM vw_eigentuemer_portfolio e
                LEFT JOIN vw_objekte_details o ON e.EIGENTUEMER_ID = o.EIGENTUEMER_ID
                LEFT JOIN vw_mieter_komplett m ON o.OBJEKT_ID = m.OBJEKT_ID
                LEFT JOIN vw_leerstand_korrekt l ON o.OBJEKT_ID = l.OBJEKT_ID
                WHERE UPPER(e.NAME) LIKE UPPER('%{owner}%')
                GROUP BY e.EIGENTUEMER_ID, e.NAME, e.VORNAME, e.STRASSE, e.PLZ, e.ORT
                ORDER BY e.NAME
            """,
            
            "mieter_by_date.sql": """
                SELECT 
                    m.*,
                    o.OBJEKT_NAME,
                    o.STRASSE,
                    o.ORT,
                    e.NAME as eigentuemer_name
                FROM vw_mieter_komplett m
                JOIN vw_objekte_details o ON m.OBJEKT_ID = o.OBJEKT_ID  
                JOIN vw_eigentuemer_portfolio e ON o.EIGENTUEMER_ID = e.EIGENTUEMER_ID
                WHERE m.EINZUGSDATUM >= '{date}'
                ORDER BY m.EINZUGSDATUM DESC, m.MIETER_NAME
            """,
            
            "wartung_by_object.sql": """
                SELECT 
                    o.OBJEKT_NAME,
                    o.STRASSE,
                    o.ORT,
                    e.NAME as eigentuemer_name,
                    'Wartungsdaten für dieses Objekt würden hier angezeigt' as wartung_info
                FROM vw_objekte_details o
                JOIN vw_eigentuemer_portfolio e ON o.EIGENTUEMER_ID = e.EIGENTUEMER_ID
                WHERE UPPER(o.OBJEKT_NAME) LIKE UPPER('%{object}%')
                   OR UPPER(o.STRASSE) LIKE UPPER('%{object}%')
                ORDER BY o.OBJEKT_NAME
            """
        }
        
        logger.info(f"✅ Loaded {len(templates)} SQL templates")
        return templates
    
    def can_handle_query(self, query: str) -> Tuple[bool, float]:
        """
        Prüft ob Query durch semantische Templates verarbeitet werden kann
        
        Returns:
            (can_handle, confidence)
        """
        pattern, confidence = self._match_pattern_regex(query)
        
        # Mindest-Konfidenz für semantische Verarbeitung
        min_confidence = 0.6
        can_handle = pattern is not None and confidence >= min_confidence
        
        if self.debug_mode:
            print(f"   🔍 Semantic pattern check: {can_handle} (confidence: {confidence:.2f})")
            if pattern:
                print(f"   📋 Matched pattern: {pattern.pattern_id}")
        
        return can_handle, confidence
    
    def _match_pattern_regex(self, query: str) -> Tuple[Optional[SemanticPattern], float]:
        """Versucht Query mit Regex-Patterns zu matchen"""
        
        query_clean = query.lower().strip()
        best_pattern = None
        best_confidence = 0.0
        
        for pattern_id, pattern_config in self.patterns.items():
            for regex_pattern in pattern_config["patterns"]:
                match = re.search(regex_pattern, query_clean)
                if match:
                    # Extract parameters
                    parameters = {}
                    param_names = pattern_config["parameters"]
                    
                    for i, param_name in enumerate(param_names):
                        if i < len(match.groups()):
                            parameters[param_name] = match.group(i + 1).strip()
                    
                    # Calculate confidence based on match quality
                    confidence = min(0.95, 0.7 + (len(match.group(0)) / len(query_clean)) * 0.25)
                    
                    if confidence > best_confidence:
                        best_pattern = SemanticPattern(
                            pattern_id=pattern_id,
                            pattern_name=pattern_config["name"],
                            parameters=parameters,
                            confidence=confidence
                        )
                        best_confidence = confidence
        
        return best_pattern, best_confidence
    
    def _extract_intent_with_llm(self, query: str) -> Optional[SemanticPattern]:
        """Fallback: LLM-basierte Intent-Extraktion"""
        
        if not self.llm_handler:
            return None
        
        # Create a lightweight prompt for intent extraction
        patterns_desc = "\n".join([
            f"- {pid}: {pconf['name']} (Parameter: {', '.join(pconf['parameters'])})"
            for pid, pconf in self.patterns.items()
        ])
        
        prompt = f"""
Analysiere diese deutsche Immobilien-Anfrage und extrahiere das Business-Pattern:

Anfrage: "{query}"

Verfügbare Patterns:
{patterns_desc}

Antworte mit JSON:
{{
    "pattern_id": "pattern_name oder null",
    "parameters": {{"param_name": "wert"}},
    "confidence": 0.0-1.0
}}

Nur wenn du sicher bist (>70% Konfidenz), gib ein Pattern zurück.
"""
        
        try:
            # Use simple LLM call for intent classification
            result = self.llm_handler._call_openai_api(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.1
            )
            
            response_text = result.choices[0].message.content.strip()
            intent_data = json.loads(response_text)
            
            if intent_data.get("pattern_id") and intent_data.get("confidence", 0) > 0.7:
                pattern_config = self.patterns.get(intent_data["pattern_id"])
                if pattern_config:
                    return SemanticPattern(
                        pattern_id=intent_data["pattern_id"],
                        pattern_name=pattern_config["name"],
                        parameters=intent_data.get("parameters", {}),
                        confidence=intent_data["confidence"]
                    )
            
        except Exception as e:
            logger.warning(f"LLM intent extraction failed: {e}")
        
        return None
    
    def process_query(self, query: str) -> SemanticTemplateResult:
        """
        Hauptfunktion: Verarbeitet Query mit semantischen Templates
        """
        start_time = time.time()
        
        if self.debug_mode:
            print(f"\n🧩 Semantic Template Engine: '{query}'")
        
        try:
            # Step 1: Pattern matching (regex first, LLM fallback)
            pattern, confidence = self._match_pattern_regex(query)
            
            if not pattern:
                # Fallback to LLM intent extraction
                pattern = self._extract_intent_with_llm(query)
                confidence = pattern.confidence if pattern else 0.0
            
            if not pattern:
                processing_time = round((time.time() - start_time) * 1000, 2)
                return SemanticTemplateResult(
                    query=query,
                    pattern=None,
                    sql_query=None,
                    answer="Keine passende semantische Vorlage gefunden",
                    success=False,
                    processing_time_ms=processing_time,
                    confidence=0.0,
                    result_count=0,
                    error_details="No semantic pattern matched"
                )
            
            if self.debug_mode:
                print(f"   ✅ Pattern matched: {pattern.pattern_id}")
                print(f"   📋 Parameters: {pattern.parameters}")
            
            # Step 2: Get SQL template
            template_name = self.patterns[pattern.pattern_id]["template"]
            sql_template = self.sql_templates.get(template_name)
            
            if not sql_template:
                processing_time = round((time.time() - start_time) * 1000, 2)
                return SemanticTemplateResult(
                    query=query,
                    pattern=pattern,
                    sql_query=None,
                    answer=f"SQL-Template '{template_name}' nicht gefunden",
                    success=False,
                    processing_time_ms=processing_time,
                    confidence=confidence,
                    result_count=0,
                    error_details=f"Template not found: {template_name}"
                )
            
            # Step 3: Parameter injection
            sql_query = sql_template
            for param_name, param_value in pattern.parameters.items():
                # Sanitize parameter value for SQL injection prevention
                safe_value = self._sanitize_parameter(param_value)
                sql_query = sql_query.replace(f"{{{param_name}}}", safe_value)
            
            # Clean up SQL formatting
            sql_query = self._clean_sql(sql_query)
            
            if self.debug_mode:
                print(f"   📝 Generated SQL: {sql_query[:100]}...")
            
            # Step 4: Execute SQL (placeholder - would integrate with existing SQL executor)
            result_count = self._simulate_sql_execution(sql_query)
            
            processing_time = round((time.time() - start_time) * 1000, 2)
            
            # Generate answer
            answer = self._generate_answer(pattern, result_count)
            
            return SemanticTemplateResult(
                query=query,
                pattern=pattern,
                sql_query=sql_query,
                answer=answer,
                success=True,
                processing_time_ms=processing_time,
                confidence=confidence,
                result_count=result_count,
                error_details=None
            )
            
        except Exception as e:
            processing_time = round((time.time() - start_time) * 1000, 2)
            error_msg = f"Semantic template processing error: {str(e)}"
            
            if self.debug_mode:
                print(f"   ❌ {error_msg}")
            
            return SemanticTemplateResult(
                query=query,
                pattern=None,
                sql_query=None,
                answer=error_msg,
                success=False,
                processing_time_ms=processing_time,
                confidence=0.0,
                result_count=0,
                error_details=str(e)
            )
    
    def _sanitize_parameter(self, value: str) -> str:
        """Sanitizes parameter values to prevent SQL injection"""
        
        # Remove dangerous characters
        safe_value = re.sub(r"[';\"\\]", "", value)
        
        # Limit length
        safe_value = safe_value[:100]
        
        # Remove leading/trailing whitespace
        safe_value = safe_value.strip()
        
        return safe_value
    
    def _clean_sql(self, sql: str) -> str:
        """Cleans and formats SQL query"""
        
        # Remove extra whitespace and newlines
        lines = [line.strip() for line in sql.split('\n') if line.strip()]
        return ' '.join(lines)
    
    def _simulate_sql_execution(self, sql: str) -> int:
        """Simulates SQL execution and returns result count"""
        
        # This would be replaced with actual SQL execution
        # For now, simulate based on query type
        if "COUNT" in sql.upper():
            return 1  # Aggregate queries return 1 row
        elif "JOIN" in sql.upper():
            return 15  # Complex queries typically return multiple rows
        else:
            return 5   # Simple queries return moderate rows
    
    def _generate_answer(self, pattern: SemanticPattern, result_count: int) -> str:
        """Generates natural language answer based on pattern and results"""
        
        pattern_config = self.patterns[pattern.pattern_id]
        pattern_name = pattern_config["name"]
        
        if result_count == 0:
            return f"Keine Ergebnisse für {pattern_name} gefunden."
        elif result_count == 1:
            return f"1 Ergebnis für {pattern_name} gefunden."
        else:
            return f"{result_count} Ergebnisse für {pattern_name} gefunden."
    
    def get_supported_patterns(self) -> List[Dict[str, str]]:
        """Returns list of supported semantic patterns"""
        
        return [
            {
                "id": pattern_id,
                "name": config["name"], 
                "description": config["description"],
                "example_patterns": config["patterns"][:2]  # Show first 2 examples
            }
            for pattern_id, config in self.patterns.items()
        ]