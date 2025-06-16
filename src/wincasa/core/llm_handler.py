#!/usr/bin/env python3
"""
WINCASA Layer 2 LLM Handler
Echte LLM-Integration für alle Provider
"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional

# LLM Provider Imports
try:
    import openai
except ImportError:
    openai = None

try:
    import anthropic
except ImportError:
    anthropic = None

try:
    import requests
except ImportError:
    requests = None

try:
    import pandas as pd
except ImportError:
    pd = None

from wincasa.data.json_exporter import get_connection
# from wincasa.tools.wincasa_tools import WincasaTools  # Missing - comment out for now

from wincasa.utils.config_loader import WincasaConfig
from wincasa.data.layer4_json_loader import Layer4JSONLoader

# Import query path logger if available
try:
    from wincasa.monitoring.query_path_logger import query_path_logger
    QUERY_PATH_LOGGING = True
except ImportError:
    QUERY_PATH_LOGGING = False

logger = logging.getLogger('llm_handler')
perf_logger = logging.getLogger('performance')

class WincasaLLMHandler:
    """Echte LLM-Integration für alle WINCASA Modi"""
    
    def __init__(self):
        self.config = WincasaConfig()
        self.system_prompt = self._load_system_prompt()
        # SQL functionality provided by database_connection module
        self.json_exporter = None
        self.layer4_json_loader = Layer4JSONLoader()
        # self.tools = WincasaTools()  # Missing - comment out for now
        
    def _load_system_prompt(self) -> str:
        """Lädt System-Prompt basierend auf aktuellem Modus"""
        prompt = self.config.load_system_prompt()
        if prompt is None:
            # System prompt file not found, use fallback
            return self._get_fallback_prompt()
        return prompt
    
    def _get_fallback_prompt(self) -> str:
        """Fallback System-Prompt falls Datei nicht gefunden"""
        return """Du bist ein WEG-Verwaltungsassistent für das WINCASA-System.
        
Kernaufgaben:
- Eigentümer-, Mieter- und Finanzdatenanalyse
- BetrKV-konforme Nebenkostenabrechnung
- Management-Reporting und Rücklagenverwaltung

Wichtige Regeln:
- ONR < 890 (schließt Testdaten aus)
- Deutsche WEG-Terminologie verwenden
- Präzise und hilfsbereite Antworten geben"""

    def _load_system_prompt_for_mode(self, mode: str) -> str:
        """Lädt System-Prompt für spezifischen Mode ohne Config neu zu laden"""
        base_path = Path(__file__).parent.parent / 'utils'
        
        # Check for Enhanced Layer 4 prompts first, fall back to standard Layer 4, then Layer 2
        prompt_files = {
            'json_standard': base_path / 'VERSION_A_JSON_LAYER4_ENHANCED.md',
            'json_vanilla': base_path / 'VERSION_A_JSON_LAYER4_VANILLA.md',
            'sql_standard': base_path / 'VERSION_B_SQL_LAYER4_ENHANCED.md',
            'sql_vanilla': base_path / 'VERSION_B_SQL_LAYER4_VANILLA.md',
            'sql_system': base_path / 'VERSION_B_SQL_LAYER4_ENHANCED.md'  # Add mapping for SQL_SYSTEM
        }
        
        # Fallback to standard Layer 4 prompts if enhanced not found
        layer4_fallback = {
            'json_standard': base_path / 'VERSION_A_JSON_LAYER4.md',
            'json_vanilla': base_path / 'VERSION_A_JSON_LAYER4_VANILLA.md',
            'sql_standard': base_path / 'VERSION_B_SQL_LAYER4.md',
            'sql_vanilla': base_path / 'VERSION_B_SQL_LAYER4_VANILLA.md',
            'sql_system': base_path / 'VERSION_B_SQL_LAYER4.md'  # Add mapping for SQL_SYSTEM
        }
        
        # Fallback to Layer 2 prompts if Layer 4 not found
        layer2_prompts = {
            'json_standard': base_path / 'VERSION_A_JSON_SYSTEM.md',
            'json_vanilla': base_path / 'VERSION_A_JSON_VANILLA.md',
            'sql_standard': base_path / 'VERSION_B_SQL_SYSTEM.md',
            'sql_vanilla': base_path / 'VERSION_B_SQL_VANILLA.md',
            'sql_system': base_path / 'VERSION_B_SQL_SYSTEM.md'  # Add mapping for SQL_SYSTEM
        }
        
        mode_lower = mode.lower()
        if mode_lower not in prompt_files:
            return self._get_fallback_prompt()
        
        prompt_path = prompt_files[mode_lower]
        
        # Try Enhanced Layer 4 first, fall back to standard Layer 4, then Layer 2
        if not prompt_path.exists() and mode_lower in layer4_fallback:
            prompt_path = layer4_fallback[mode_lower]
        
        if not prompt_path.exists() and mode_lower in layer2_prompts:
            prompt_path = layer2_prompts[mode_lower]
        
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Extrahiere System-Prompt aus Markdown
                if '```' in content:
                    start = content.find('```') + 3
                    end = content.find('```', start)
                    base_content = content[start:end].strip()
                else:
                    base_content = content
                
                # Add knowledge base context (skip for SQL modes to avoid confusion)
                if not mode.lower().startswith('sql_'):
                    knowledge_context = self._get_knowledge_base_context()
                    if knowledge_context:
                        base_content += f"\n\n{knowledge_context}"
                
                # Schema information is now provided by knowledge base context
                
                return base_content
                    
        except Exception as e:
            raise Exception(f"Fehler beim Laden des System-Prompts für {mode}: {e}") from e
    
    def _get_knowledge_base_context(self) -> str:
        """Get relevant context from knowledge base"""
        try:
            from wincasa.knowledge.knowledge_base_loader import get_knowledge_base
            kb = get_knowledge_base()
            
            # Get most important mappings with detailed explanations
            context = "\n## KRITISCHE FELD-MAPPINGS FÜR SQL-QUERIES:\n"
            context += "WARNUNG: Nutze IMMER diese Mappings für korrekte SQL-Queries!\n\n"
            
            # Critical mappings
            context += "### MIETEN UND KOSTEN:\n"
            context += "- KALTMIETE = BEWOHNER.Z1 (NICHT KONTEN.KBETRAG!)\n"
            context += "- NEBENKOSTEN = BEWOHNER.Z3\n"
            context += "- HEIZKOSTEN = BEWOHNER.Z4\n"
            context += "- WARMMIETE = BEWOHNER.Z1 + Z2 + Z3 + Z4\n\n"
            
            context += "### EIGENTÜMER:\n"
            context += "- EIGENTUEMERKUERZEL = EIGADR.ENOTIZ (für Suche nach Code)\n"
            context += "- EIGENTUEMER_NAME = EIGADR.ENAME (für Suche nach Name)\n"
            context += "- EIGENTÜMER-ID = EIGADR.EIGNR\n\n"
            
            context += "### MIETER:\n"
            context += "- MIETER_NAME = BEWOHNER.BNAME (Vertragsdaten) oder BEWADR.BNAME (Adressdaten)\n"
            context += "- MIETER_VORNAME = BEWOHNER.BVNAME (Vertragsdaten) oder BEWADR.BVNAME (Adressdaten)\n"
            context += "- MIETER-ID = BEWOHNER.BEWNR\n"
            context += "- WICHTIG: BEWOHNER hat KEIN EIGNR Feld! Primary Key ist (ONR, KNR)\n\n"
            
            context += "### WICHTIGE JOINS:\n"
            context += "- Eigentümer zu Objekten: EIGADR.EIGNR = OBJEKTE.EIGNR\n"
            context += "- Objekte zu Mietern: OBJEKTE.ONR = BEWOHNER.ONR\n"
            context += "- Mieter-Adressen: BEWOHNER.BEWNR = BEWADR.BEWNR\n"
                    
            return context
        except Exception as e:
            logger.warning(f"Could not load knowledge base context: {str(e)}")
            return ""
    
    def _is_tenant_search_query(self, query: str) -> bool:
        """Prüft ob es sich um eine Mieter-Suchanfrage handelt"""
        query_lower = query.lower()
        
        # Erkenne Mieter-Suchanfragen
        tenant_keywords = ['mieter', 'bewohner', 'wohnt', 'wer wohnt', 'alle mieter']
        address_keywords = ['straße', 'str.', 'plz', 'adresse', 'marienstr', 'essen']
        
        has_tenant_keyword = any(keyword in query_lower for keyword in tenant_keywords)
        has_address_keyword = any(keyword in query_lower for keyword in address_keywords)
        
        return has_tenant_keyword and has_address_keyword
    
    def _extract_address_from_query(self, query: str) -> Dict[str, str]:
        """Extrahiert Adressinformationen aus der Anfrage"""
        import re

        # Einfache Regex-Patterns für deutsche Adressen
        street_pattern = r'(\w+(?:str\.|straße)\.?\s*\d+)'
        plz_pattern = r'(\d{5})'
        city_pattern = r'(\d{5}\s+([A-Za-züöäß\s]+))'
        
        street = None
        plz = None
        city = None
        
        # Straße extrahieren
        street_match = re.search(street_pattern, query, re.IGNORECASE)
        if street_match:
            street = street_match.group(1).strip()
            # Normalize street abbreviations for better matching
            street = street.replace('str.', 'straße').replace('Str.', 'straße')
        
        # PLZ extrahieren
        plz_match = re.search(plz_pattern, query)
        if plz_match:
            plz = plz_match.group(1)
        
        # Stadt extrahieren
        city_match = re.search(city_pattern, query, re.IGNORECASE)
        if city_match:
            city = city_match.group(2).strip()
        
        return {
            'street': street,
            'postal_code': plz,
            'city': city
        }
    
    def _handle_tenant_search(self, query: str, mode: str, query_id: str) -> str:
        """Führt direkte Mieter-Suche mit Unified Data Access Layer durch"""
        try:
            # Adresse aus Query extrahieren
            address_info = self._extract_address_from_query(query)
            logger.info(f"[{query_id}] Extrahierte Adresse: {address_info}")
            
            if not address_info['street']:
                return "Ich konnte keine gültige Straßenadresse in Ihrer Anfrage finden. Bitte geben Sie eine Adresse im Format 'Straßenname Nummer' an."
            
            # Use Unified Data Access Layer
            from wincasa.data.data_access_layer import get_data_access

            # Determine data source based on mode
            source = "sql" if mode and 'sql' in mode else "json"
            data_access = get_data_access(source=source)
            
            logger.info(f"[{query_id}] Using unified data access with source: {source}")
            
            # Search using unified interface
            result = data_access.search_tenants_by_address(
                street=address_info['street'],
                postal_code=address_info.get('postal_code'),
                city=address_info.get('city')
            )
            
            if result['success']:
                return self._format_unified_tenant_results(result, address_info, query_id)
            else:
                return f"Keine Mieter gefunden für die angegebene Adresse: {result['message']}"
                
        except Exception as e:
            logger.error(f"[{query_id}] Fehler bei direkter Mieter-Suche: {str(e)}")
            return f"Fehler bei der Mieter-Suche: {str(e)}"
    
    def _build_tenant_search_sql(self, address_info: Dict[str, str]) -> str:
        """Baut SQL-Query für Mietersuche basierend auf bewährtem Layer 1 Template"""
        # Use validated Layer 1 Mieter template as base - NO HARDCODED COLUMNS
        sql = """
        SELECT 
          BEWADR.BEWNR,
          BEWADR.BVNAME,
          BEWADR.BNAME,
          BEWADR.BSTR,
          BEWADR.BPLZORT,
          BEWADR.BTEL,
          BEWADR.BEMAIL,
          BEWOHNER.ONR,
          BEWOHNER.ENR,
          BEWOHNER.VBEGINN,
          BEWOHNER.VENDE,
          WOHNUNG.EBEZ AS Lage,
          OBJEKTE.OBEZ AS Liegenschaftskuerzel
        FROM
          BEWADR
          RIGHT OUTER JOIN BEWOHNER ON (BEWADR.BEWNR = BEWOHNER.BEWNR)
          LEFT OUTER JOIN WOHNUNG ON (BEWOHNER.ONR = WOHNUNG.ONR)
          AND (BEWOHNER.ENR = WOHNUNG.ENR)
          LEFT OUTER JOIN OBJEKTE ON (BEWOHNER.ONR = OBJEKTE.ONR)
        WHERE
          BEWADR.BEWNR >= 0 AND 
          (BEWOHNER.VENDE >= CURRENT_DATE OR 
          BEWOHNER.VENDE IS NULL)
          AND OBJEKTE.ONR < 890
        """
        
        # Adress-Filter hinzufügen (use validated column names from Layer 1)
        conditions = []
        
        if address_info['street']:
            street = address_info['street'].replace("'", "''")  # SQL-Escape
            conditions.append(f"OBJEKTE.OBEZ LIKE '%{street}%' OR BEWADR.BSTR LIKE '%{street}%'")
        
        if address_info['postal_code']:
            conditions.append(f"BEWADR.BPLZORT LIKE '%{address_info['postal_code']}%'")
        
        if address_info['city']:
            city = address_info['city'].replace("'", "''")  # SQL-Escape
            conditions.append(f"BEWADR.BPLZORT LIKE '%{city}%'")
        
        if conditions:
            sql += " AND (" + " OR ".join(conditions) + ")"
        
        sql += " ORDER BY BEWADR.BEWNR"
        
        return sql
    
    def _format_json_tenant_results(self, result: Dict, address_info: Dict) -> str:
        """Formatiert JSON-Mieter-Suchergebnisse"""
        if not result['data']:
            return f"Keine aktiven Mieter gefunden für {address_info['street']}"
        
        tenants = result['data']
        
        # Group by unique tenant (same names might have multiple billing records)
        unique_tenants = {}
        for tenant in tenants:
            key = (
                tenant.get('ONR', ''), 
                tenant.get('ENR', ''), 
                tenant.get('NACHNAME', ''), 
                tenant.get('VORNAME', '')
            )
            if key not in unique_tenants:
                unique_tenants[key] = tenant
        
        unique_list = list(unique_tenants.values())
        response = f"**Mieter-Suche für {address_info['street']}**\n\n"
        response += f"**Gefunden: {len(unique_list)} aktive Mieter**\n\n"
        
        for i, tenant in enumerate(unique_list, 1):
            apartment = f"ONR {tenant.get('ONR', 'unbekannt')}, ENR {tenant.get('ENR', 'unbekannt')}"
            response += f"**{i}. Mieter in {apartment}**\n"
            
            # Show tenant name
            nachname = tenant.get('NACHNAME', '').strip()
            vorname = tenant.get('VORNAME', '').strip()
            if nachname or vorname:
                response += f"   • Name: {vorname} {nachname}\n"
            else:
                response += f"   • Name: Nicht angegeben\n"
            
            # Show contact info if available
            telefon = tenant.get('TELEFON', '')
            if telefon:
                response += f"   • Telefon: {telefon}\n"
            
            response += "\n"
        
        return response
    
    def _format_unified_tenant_results(self, result: Dict, address_info: Dict, query_id: str) -> str:
        """Formatiert Ergebnisse aus Unified Data Access Layer"""
        tenants = result['data']
        source = result.get('source', 'unknown')
        
        logger.info(f"[{query_id}] Formatting {len(tenants)} unified tenant results from {source}")
        
        response = f"**Mieter-Suche für {address_info['street']}**\n\n"
        response += f"**Gefunden: {len(tenants)} aktive Mieter** (Quelle: {source})\n"
        
        if result.get('total_records') != result.get('unique_records'):
            response += f"*({result.get('total_records', 0)} Datensätze dedupliziert zu {len(tenants)} Mietern)*\n"
        
        response += "\n"
        
        for i, tenant in enumerate(tenants, 1):
            # Use standardized field names
            object_nr = tenant.get('object_number', 'unbekannt')
            unit_nr = tenant.get('unit_number', 'unbekannt') 
            apartment_desc = tenant.get('apartment_description', '') or tenant.get('unit_description', '')
            
            response += f"**{i}. Mieter in Objekt {object_nr}, Einheit {unit_nr}**\n"
            if apartment_desc:
                response += f"   • Lage: {apartment_desc}\n"
            
            # Show tenant name using standardized fields
            first_name = tenant.get('first_name', '').strip()
            last_name = tenant.get('last_name', '').strip()
            if first_name or last_name:
                response += f"   • Name: {first_name} {last_name}\n"
            else:
                response += f"   • Name: Nicht angegeben\n"
            
            # Show contact info if available
            phone = tenant.get('phone', '')
            email = tenant.get('email', '')
            if phone:
                response += f"   • Telefon: {phone}\n"
            if email:
                response += f"   • Email: {email}\n"
            
            # Show lease dates if available
            lease_start = tenant.get('lease_start', '')
            lease_end = tenant.get('lease_end', '')
            if lease_start:
                response += f"   • Mietbeginn: {lease_start}\n"
            if lease_end:
                response += f"   • Mietende: {lease_end}\n"
            
            response += "\n"
        
        return response
    
    
    def query_llm(self, user_query: str, mode: str = None) -> Dict[str, Any]:
        """Führt echte LLM-Abfrage aus"""
        query_id = f"{int(time.time()*1000)}"  # Unique query ID
        logger.info(f"[{query_id}] LLM Query gestartet - Mode: {mode}, Query: {user_query[:100]}...")
        
        old_mode = None
        if mode:
            # Temporär Mode ändern
            old_mode = os.environ.get('SYSTEM_MODE')
            os.environ['SYSTEM_MODE'] = mode
            logger.debug(f"[{query_id}] Mode temporär geändert: {old_mode} -> {mode}")
            # Lade nur System-Prompt neu, nicht ganze Config
            self.system_prompt = self._load_system_prompt_for_mode(mode)
            logger.debug(f"[{query_id}] System-Prompt geladen für Mode: {mode}")
        
        start_time = time.time()
        
        try:
            llm_config = self.config.get_llm_config()
            
            # Comprehensive logging
            logger.info(f"[{query_id}] LLM Config - Provider: {llm_config.get('provider')}, Model: {llm_config.get('model')}")
            logger.debug(f"[{query_id}] API Key present: {bool(llm_config.get('api_key'))}")
            logger.debug(f"[{query_id}] Temperature: {llm_config.get('temperature')}, Max Tokens: {llm_config.get('max_tokens')}")
            logger.debug(f"[{query_id}] System Prompt Length: {len(self.system_prompt)} chars")
            
            # Enhance query with knowledge base context (skip for SQL modes to avoid confusion)
            enhanced_context = ""
            current_mode = mode or os.environ.get('SYSTEM_MODE', 'json_standard')
            if 'sql' not in current_mode.lower():
                try:
                    from wincasa.knowledge.knowledge_base_loader import get_knowledge_base
                    kb = get_knowledge_base()
                    enhanced_context = kb.enhance_prompt_with_knowledge(user_query)
                    if enhanced_context:
                        logger.info(f"[{query_id}] Added knowledge base context to query")
                except Exception as e:
                    logger.debug(f"Could not enhance with knowledge base: {str(e)}")
            else:
                logger.debug(f"[{query_id}] Skipping knowledge base context for SQL mode")
            
            # Check if this is a tenant search query that we can handle directly
            if self._is_tenant_search_query(user_query):
                logger.info(f"[{query_id}] Erkenne Mieter-Suchanfrage - führe direkte Datenbankabfrage aus")
                response = self._handle_tenant_search(user_query, mode, query_id)
            else:
                # Regular LLM query - OpenAI only
                logger.info(f"[{query_id}] Sende Anfrage an OpenAI API...")
                
                # Add enhanced context to user query if available
                if enhanced_context:
                    enhanced_query = f"{user_query}\n\n[KONTEXT AUS DATENBANK-ANALYSE]:\n{enhanced_context}"
                else:
                    enhanced_query = user_query
                    
                response = self._query_openai(enhanced_query, llm_config, query_id)
            
            response_time = time.time() - start_time
            
            # Performance logging
            perf_logger.info(f"Query {query_id} | Mode: {mode} | Response Time: {response_time:.2f}s | Success: True | Model: {llm_config.get('model')}")
            logger.info(f"[{query_id}] LLM Query erfolgreich abgeschlossen in {response_time:.2f}s")
            
            return {
                'answer': response,
                'source': f"OpenAI - {llm_config.get('model', 'unknown')}",
                'response_time': response_time,
                'mode': mode or self.config.get('system_mode'),
                'success': True
            }
            
        except Exception as e:
            response_time = time.time() - start_time
            logger.error(f"[{query_id}] LLM Query fehlgeschlagen nach {response_time:.2f}s: {str(e)}")
            perf_logger.info(f"Query {query_id} | Mode: {mode} | Response Time: {response_time:.2f}s | Success: False | Error: {str(e)[:100]}")
            
            # NO FALLBACKS - Propagate the error
            raise Exception(f"LLM API Fehler: {str(e)}") from e
        
        finally:
            # Mode zurücksetzen
            if mode and old_mode:
                os.environ['SYSTEM_MODE'] = old_mode
                self.system_prompt = self._load_system_prompt()
                logger.debug(f"[{query_id}] Mode zurückgesetzt: {mode} -> {old_mode}")
    
    def _query_openai(self, user_query: str, config: Dict, query_id: str = "unknown") -> str:
        """OpenAI API Abfrage mit Function Calling Support"""
        if not openai:
            logger.error(f"[{query_id}] OpenAI package nicht installiert")
            raise ImportError("OpenAI package nicht installiert: pip install openai")
        
        if not config.get('api_key'):
            logger.error(f"[{query_id}] OpenAI API Key fehlt")
            raise ValueError("OpenAI API Key fehlt")
        
        # Determine current mode
        current_mode = os.environ.get('SYSTEM_MODE', 'json_standard')
        is_json_mode = 'json' in current_mode
        
        # Define available functions based on mode
        if is_json_mode:
            # JSON mode - search in pre-exported JSON files
            functions = [
                {
                    "name": "search_json_data",
                    "description": "Search in pre-exported JSON files from Layer 4 queries",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query_name": {
                                "type": "string", 
                                "description": "Name of the JSON file to search (e.g., '01_eigentuemer', '03_aktuelle_mieter')"
                            },
                            "search_term": {
                                "type": "string", 
                                "description": "Optional search term to filter results"
                            },
                            "limit": {
                                "type": "integer", 
                                "description": "Maximum number of results to return",
                                "default": 500
                            }
                        },
                        "required": ["query_name"]
                    }
                },
                {
                    "name": "search_all_json_files",
                    "description": "Search across all JSON export files for a specific term",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "search_term": {"type": "string", "description": "Term to search for across all JSON files"},
                            "max_results": {"type": "integer", "description": "Maximum results to return", "default": 50}
                        },
                        "required": ["search_term"]
                    }
                },
                {
                    "name": "list_available_json_queries",
                    "description": "List all available JSON export files with their descriptions and row counts",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "category": {
                                "type": "string", 
                                "description": "Optional category filter: stammdaten, finanzen, governance, analysen, spezial"
                            }
                        }
                    }
                }
            ]
        else:
            # SQL mode - direct database queries
            functions = [
            {
                "name": "search_tenants_by_address",
                "description": "Searches for tenants at a specific address in the WINCASA database",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "street": {"type": "string", "description": "Street name with number (e.g., 'Marienstr. 26')"},
                        "postal_code": {"type": "string", "description": "5-digit postal code (optional)"},
                        "city": {"type": "string", "description": "City name (optional)"}
                    },
                    "required": ["street"]
                }
            },
            {
                "name": "search_owners_by_address",
                "description": "Searches for property owners at a specific address in the WINCASA database",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "street": {"type": "string", "description": "Street name with number (e.g., 'Neusser str. 49')"},
                        "postal_code": {"type": "string", "description": "5-digit postal code (optional)"},
                        "city": {"type": "string", "description": "City name (optional)"}
                    },
                    "required": ["street"]
                }
            },
            {
                "name": "execute_sql_query",
                "description": "Executes a SQL query against the WINCASA Firebird database",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "sql": {"type": "string", "description": "SQL SELECT query to execute"},
                        "query_type": {"type": "string", "description": "Type of query for result formatting"}
                    },
                    "required": ["sql"]
                }
            }
        ]
        
        # Initialize OpenAI client
        client = openai.OpenAI(api_key=config['api_key'])
        
        logger.debug(f"[{query_id}] OpenAI Request - Model: {config['model']}")
        logger.debug(f"[{query_id}] User Query Length: {len(user_query)} chars")
        
        api_start_time = time.time()
        
        try:
            response = client.chat.completions.create(
                model=config['model'],
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_query}
                ],
                functions=functions,
                function_call="auto",
                temperature=config['temperature'],
                max_tokens=config['max_tokens']
            )
            
            api_time = time.time() - api_start_time
            logger.debug(f"[{query_id}] OpenAI API Response Time: {api_time:.2f}s")
            
            choice = response.choices[0]
            message = choice.message
            
            # Check if LLM wants to call a function
            if message.function_call:
                function_name = message.function_call.name
                function_args = json.loads(message.function_call.arguments)
                
                logger.info(f"[{query_id}] LLM called function: {function_name} with args: {function_args}")
                
                # Execute the function
                function_result = self._execute_function(function_name, function_args, query_id)
                
                # Return function result as response
                return function_result
            
            # Regular text response
            elif message.content:
                response_content = message.content.strip()
                logger.debug(f"[{query_id}] Response Length: {len(response_content)} chars")
                
                # Usage logging
                if response.usage:
                    usage = response.usage
                    logger.info(f"[{query_id}] Token Usage - Prompt: {usage.prompt_tokens}, Completion: {usage.completion_tokens}, Total: {usage.total_tokens}")
                
                return response_content
            
            else:
                logger.error(f"[{query_id}] Unexpected message format: {message}")
                raise Exception("Unexpected message format")
        
        except Exception as e:
            logger.error(f"[{query_id}] OpenAI API Unbekannter Fehler: {str(e)}")
            raise
    
    
    def _execute_function(self, function_name: str, function_args: Dict[str, Any], query_id: str) -> str:
        """
        Execute LLM-called function and return formatted results.
        This gives the LLM tool execution capabilities like Claude Code.
        """
        logger.info(f"[{query_id}] Executing function: {function_name} with args: {function_args}")
        
        try:
            # JSON mode functions
            if function_name == "search_json_data":
                return self._execute_json_search_function(function_args, query_id)
            
            elif function_name == "search_all_json_files":
                return self._execute_json_search_all_function(function_args, query_id)
            
            elif function_name == "list_available_json_queries":
                return self._execute_list_json_queries_function(function_args, query_id)
            
            # SQL mode functions
            elif function_name == "search_tenants_by_address":
                return self._execute_tenant_search_function(function_args, query_id)
            
            elif function_name == "search_owners_by_address":
                return self._execute_owner_search_function(function_args, query_id)
            
            elif function_name == "execute_sql_query":
                return self._execute_sql_function(function_args, query_id)
            
            else:
                error_msg = f"Unknown function: {function_name}"
                logger.error(f"[{query_id}] {error_msg}")
                
                # List available functions for debugging
                available_functions = [
                    "search_json_data", "search_all_json_files", "list_available_json_queries",
                    "search_tenants_by_address", "search_owners_by_address", "execute_sql_query"
                ]
                logger.info(f"[{query_id}] Available functions: {', '.join(available_functions)}")
                
                return f"Fehler: Unbekannte Funktion '{function_name}'. Verfügbare Funktionen: {', '.join(available_functions)}"
                
        except Exception as e:
            error_msg = f"Function execution failed: {str(e)}"
            logger.error(f"[{query_id}] {error_msg}")
            return f"Fehler bei der Funktionsausführung: {str(e)}"
    
    def _execute_tenant_search_function(self, args: Dict[str, Any], query_id: str) -> str:
        """Execute tenant search function using sophisticated SQL engine"""
        try:
            # Convert function arguments to format expected by _build_tenant_search_sql
            address_info = {
                'street': args.get('street'),
                'postal_code': args.get('postal_code'),
                'city': args.get('city')
            }
            
            # Build SQL query for tenant search
            sql_query = self._build_tenant_search_sql(address_info)
            logger.info(f"[{query_id}] Function calling tenant search SQL: {sql_query}")
            
            # Execute with sophisticated SQL engine
            # Execute SQL query directly
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(sql_query)
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            result = {'columns': columns, 'data': rows, 'success': True, 'error': None}
            cursor.close()
            conn.close()
            
            if result['success']:
                # Format result for function calling context
                formatted_answer = self._format_sql_result(result)
                formatted_result = f"**Mieter-Suche Ergebnis:**\n\n{formatted_answer}"
                logger.info(f"[{query_id}] Function call successful - found {len(result['data'])} results")
                return formatted_result
            else:
                error_msg = result.get('error', 'Unknown error')
                return f"Fehler bei der Mieter-Suche: {error_msg}"
                
        except Exception as e:
            logger.error(f"[{query_id}] Tenant search function failed: {str(e)}")
            return f"Fehler bei der Mieter-Suche: {str(e)}"
    
    def _execute_owner_search_function(self, args: Dict[str, Any], query_id: str) -> str:
        """Execute owner search function using unified data access layer"""
        try:
            from wincasa.data.data_access_layer import get_data_access

            # Use unified data access with SQL source
            data_access = get_data_access(source="sql")
            
            result = data_access.search_owners_by_address(
                street=args.get('street'),
                postal_code=args.get('postal_code'),
                city=args.get('city')
            )
            
            if result['success']:
                owners = result['data']
                source = result.get('source', 'sql')
                
                response = f"**Eigentümer-Suche Ergebnis:**\n\n"
                response += f"**Gefunden: {len(owners)} Eigentümer** (Quelle: {source})\n\n"
                
                for i, owner in enumerate(owners, 1):
                    # Use standardized field names from unified layer
                    first_name = owner.get('owner_first_name', '').strip()
                    last_name = owner.get('owner_last_name', '').strip()
                    street = owner.get('owner_street', '')
                    postal_city = owner.get('owner_postal_city', '')
                    email = owner.get('owner_email', '')
                    phone = owner.get('owner_phone', '')
                    
                    response += f"**{i}. Eigentümer**\n"
                    if first_name or last_name:
                        response += f"   • Name: {first_name} {last_name}\n"
                    if street:
                        response += f"   • Adresse: {street}\n"
                    if postal_city:
                        response += f"   • Ort: {postal_city}\n"
                    if email:
                        response += f"   • Email: {email}\n"
                    if phone:
                        response += f"   • Telefon: {phone}\n"
                    response += "\n"
                
                logger.info(f"[{query_id}] Owner search function successful - found {len(owners)} results")
                return response
            else:
                error_msg = result.get('message', 'Unknown error')
                return f"Fehler bei der Eigentümer-Suche: {error_msg}"
                
        except Exception as e:
            logger.error(f"[{query_id}] Owner search function failed: {str(e)}")
            return f"Fehler bei der Eigentümer-Suche: {str(e)}"
    
    def _execute_sql_function(self, args: Dict[str, Any], query_id: str) -> str:
        """Execute arbitrary SQL query function with validation"""
        try:
            sql_query = args.get('sql', '')
            query_type = args.get('query_type', 'general')
            
            if not sql_query:
                return "Fehler: Keine SQL-Abfrage angegeben"
            
            # Validate SQL against knowledge base
            try:
                from wincasa.knowledge.knowledge_base_loader import get_knowledge_base
                kb = get_knowledge_base()
                validation_issues = kb.validate_sql_fields(sql_query)
                if validation_issues:
                    logger.warning(f"[{query_id}] SQL validation issues: {validation_issues}")
            except Exception as e:
                logger.debug(f"Could not validate SQL: {str(e)}")
            
            logger.info(f"[{query_id}] Function calling SQL execution: {sql_query[:100]}...")
            
            # SQL validation is now handled by knowledge base above
            
            # Execute SQL query
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(sql_query)
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            result = {'columns': columns, 'data': rows, 'success': True, 'error': None}
            cursor.close()
            conn.close()
            
            if result['success']:
                # Format result for function calling context
                formatted_answer = self._format_sql_result(result)
                formatted_result = f"**SQL-Abfrage Ergebnis:**\n\n{formatted_answer}\n\n*Gefundene Datensätze: {len(result['data'])}*"
                logger.info(f"[{query_id}] SQL function call successful - {len(result['data'])} rows")
                return formatted_result
            else:
                error_msg = result.get('error', 'Unknown error')
                return f"Fehler bei der SQL-Ausführung: {error_msg}"
                
        except Exception as e:
            logger.error(f"[{query_id}] SQL function execution failed: {str(e)}")
            return f"Fehler bei der SQL-Ausführung: {str(e)}"
    
    def _format_sql_result(self, result: dict) -> str:
        """Format SQL result for display"""
        if not result['data']:
            return "Keine Daten gefunden."
        
        # Format as simple table
        lines = []
        if result['columns']:
            # Header
            lines.append(" | ".join(result['columns']))
            lines.append("-" * len(lines[0]))
            
            # Data rows (limit to first 10)
            for i, row in enumerate(result['data'][:10]):
                row_str = " | ".join(str(val) if val is not None else "" for val in row)
                lines.append(row_str)
            
            if len(result['data']) > 10:
                lines.append(f"... und {len(result['data']) - 10} weitere Zeilen")
        
        return "\n".join(lines)
    
    def _execute_json_search_function(self, args: Dict[str, Any], query_id: str) -> str:
        """Execute JSON file search function"""
        try:
            query_name = args.get('query_name', '')
            search_term = args.get('search_term', '')
            limit = args.get('limit', 500)
            
            if not query_name:
                return "Fehler: Kein Query-Name angegeben"
            
            logger.info(f"[{query_id}] Searching JSON file: {query_name} for term: {search_term}")
            
            # Load JSON data
            data = self.layer4_json_loader.load_json_data(query_name)
            if not data:
                return f"Fehler: JSON-Datei '{query_name}.json' nicht gefunden"
            
            # Extract data and filter if search term provided
            json_data = data.get('data', [])
            query_info = data.get('query_info', {})
            
            if search_term:
                # Filter results
                filtered_data = []
                search_lower = search_term.lower()
                for row in json_data:
                    if any(search_lower in str(value).lower() for value in row.values()):
                        filtered_data.append(row)
                        if len(filtered_data) >= limit:
                            break
                json_data = filtered_data
            else:
                # Limit results
                json_data = json_data[:limit]
            
            # Format result
            result_text = f"**JSON-Daten aus {query_name}:**\n\n"
            result_text += f"*Business Purpose: {query_info.get('business_purpose', 'N/A')}*\n"
            result_text += f"*Gesamt-Datensätze: {len(data.get('data', []))}*\n"
            result_text += f"*Angezeigt: {len(json_data)}*\n\n"
            
            if json_data:
                # Show sample data
                columns = data.get('columns', [])
                if columns:
                    result_text += "**Spalten:** " + ", ".join(columns[:10])
                    if len(columns) > 10:
                        result_text += f" ... (+{len(columns)-10} weitere)"
                    result_text += "\n\n"
                
                # Show more results for better user experience
                display_limit = min(100, len(json_data))  # Show up to 100 results
                result_text += f"**Datensätze (erste {display_limit} von {len(json_data)}):**\n"
                for i, row in enumerate(json_data[:display_limit], 1):
                    result_text += f"\n{i}. "
                    # Show key fields (dynamic based on available data)
                    key_fields = []
                    # Get first 5 non-null fields for this row
                    for key, value in row.items():
                        if value and str(value).strip():  # Only show non-empty values
                            key_fields.append(f"{key}: {value}")
                            if len(key_fields) >= 5:
                                break
                    result_text += " | ".join(key_fields)
                
                if len(json_data) > display_limit:
                    result_text += f"\n\n... und {len(json_data)-display_limit} weitere Datensätze verfügbar"
            else:
                result_text += "\nKeine Datensätze gefunden."
            
            return result_text
            
        except Exception as e:
            logger.error(f"[{query_id}] JSON search function failed: {str(e)}")
            return f"Fehler bei der JSON-Suche: {str(e)}"
    
    def _execute_json_search_all_function(self, args: Dict[str, Any], query_id: str) -> str:
        """Search across all JSON files"""
        try:
            search_term = args.get('search_term', '')
            max_results = args.get('max_results', 50)
            
            if not search_term:
                return "Fehler: Kein Suchbegriff angegeben"
            
            logger.info(f"[{query_id}] Searching all JSON files for: {search_term}")
            
            # Search across all files
            results = self.layer4_json_loader.search_in_json(search_term, max_results)
            
            # Format results
            result_text = f"**Suchergebnisse für '{search_term}':**\n\n"
            result_text += f"*Gefunden: {len(results)} Treffer*\n\n"
            
            if results:
                # Group by query
                by_query = {}
                for result in results:
                    query = result['query']
                    if query not in by_query:
                        by_query[query] = []
                    by_query[query].append(result['data'])
                
                # Show results grouped by query
                for query, items in list(by_query.items())[:10]:
                    result_text += f"\n**{query}** ({len(items)} Treffer):\n"
                    for i, item in enumerate(items[:3], 1):
                        # Show key fields
                        key_fields = []
                        for key, value in list(item.items())[:5]:
                            if value:
                                key_fields.append(f"{key}: {str(value)[:50]}")
                        result_text += f"  {i}. " + " | ".join(key_fields) + "\n"
                    if len(items) > 3:
                        result_text += f"  ... und {len(items)-3} weitere\n"
            else:
                result_text += "\nKeine Treffer gefunden."
            
            return result_text
            
        except Exception as e:
            logger.error(f"[{query_id}] Search all JSON function failed: {str(e)}")
            return f"Fehler bei der übergreifenden Suche: {str(e)}"
    
    def _execute_list_json_queries_function(self, args: Dict[str, Any], query_id: str) -> str:
        """List available JSON queries"""
        try:
            category = args.get('category', '')
            
            logger.info(f"[{query_id}] Listing available JSON queries, category: {category}")
            
            # Get all available queries
            queries = self.layer4_json_loader.list_available_queries()
            
            # Filter by category if specified
            if category:
                queries = [q for q in queries if q['category'] == category]
            
            # Get summary statistics
            stats = self.layer4_json_loader.get_summary_statistics()
            
            # Format result
            result_text = "**Verfügbare Layer 4 JSON-Exporte:**\n\n"
            result_text += f"*Gesamt: {stats['total_queries']} Queries mit {stats['total_rows']:,} Datensätzen*\n\n"
            
            # Group by category
            by_category = {}
            for query in queries:
                if query['exists']:
                    cat = query['category']
                    if cat not in by_category:
                        by_category[cat] = []
                    by_category[cat].append(query)
            
            # Show queries by category
            category_names = {
                'stammdaten': '🏢 Stammdaten',
                'finanzen': '💰 Finanzen',
                'governance': '🏛️ Governance',
                'analysen': '📊 Analysen',
                'spezial': '📨 Spezialabfragen'
            }
            
            for cat, cat_queries in by_category.items():
                result_text += f"\n**{category_names.get(cat, cat)}:**\n"
                for q in sorted(cat_queries, key=lambda x: x['rows'], reverse=True):
                    result_text += f"- {q['name']}: {q['rows']:,} Zeilen - {q['description']}\n"
            
            return result_text
            
        except Exception as e:
            logger.error(f"[{query_id}] List JSON queries function failed: {str(e)}")
            return f"Fehler beim Auflisten der JSON-Queries: {str(e)}"
    
    
    def test_connection(self) -> Dict[str, Any]:
        """Testet LLM-Verbindung"""
        test_query = "Hallo, bist du bereit für WINCASA WEG-Verwaltung?"
        
        try:
            result = self.query_llm(test_query)
            return {
                'success': True,
                'provider': self.config.get_llm_config()['provider'],
                'model': self.config.get_llm_config().get('model', 'unknown'),
                'response_time': result['response_time'],
                'test_response': result['answer'][:100] + "..." if len(result['answer']) > 100 else result['answer']
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'provider': self.config.get('llm_provider', 'unknown')
            }


def test_llm_handler():
    """Test-Funktion für LLM Handler"""
    print("=== WINCASA LLM Handler Test ===")
    
    handler = WincasaLLMHandler()
    
    # Connection Test
    print("\n1. Verbindungstest...")
    connection_test = handler.test_connection()
    if connection_test['success']:
        print(f"✅ Verbindung erfolgreich:")
        print(f"   Provider: {connection_test['provider']}")
        print(f"   Model: {connection_test['model']}")
        print(f"   Antwortzeit: {connection_test['response_time']:.1f}s")
        print(f"   Test-Antwort: {connection_test['test_response']}")
    else:
        print(f"❌ Verbindung fehlgeschlagen: {connection_test['error']}")
        return
    
    # Real Query Test
    print("\n2. Echte Abfrage...")
    test_query = "Zeige mir alle Mieter der Marienstr. 26, 45307 Essen"
    result = handler.query_llm(test_query)
    
    if result['success']:
        print(f"✅ Abfrage erfolgreich:")
        print(f"   Modus: {result['mode']}")
        print(f"   Quelle: {result['source']}")
        print(f"   Antwortzeit: {result['response_time']:.1f}s")
        print(f"   Antwort: {result['answer'][:200]}...")
    else:
        print(f"❌ Abfrage fehlgeschlagen: {result.get('error', 'Unbekannter Fehler')}")


if __name__ == "__main__":
    test_llm_handler()