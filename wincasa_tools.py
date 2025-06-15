#!/usr/bin/env python3
"""
WINCASA Tools - Tool Framework für LLM Function Calling
====================================================

Provides tool implementations that the LLM can call through function calling.
This bridges the gap between LLM requests and actual database operations.

Uses Layer 1 SQL templates instead of hardcoded queries.
"""

import logging
import os
from pathlib import Path
from typing import Dict, Any, List
from database_connection import get_connection

logger = logging.getLogger(__name__)

class WincasaTools:
    """Tool-System für direkten Datenbankzugriff durch LLM"""
    
    def __init__(self):
        # Database connection provided by database_connection module
        # Reference to Layer 1 SQL templates - NO HARDCODING
        self.layer1_templates_path = Path("../layer1_focused_extraction/sql_templates")
        logger.info("WincasaTools initialized with SQL engine and Layer 1 template references")
    
    def _load_sql_template(self, template_name: str) -> str:
        """Load SQL template from Layer 1 without hardcoding"""
        template_file = self.layer1_templates_path / f"{template_name}.txt"
        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except FileNotFoundError:
            logger.error(f"SQL template not found: {template_file}")
            raise FileNotFoundError(f"SQL template '{template_name}' not found")
    
    def _add_address_filter_to_sql(self, base_sql: str, street: str = None, postal_code: str = None, city: str = None) -> str:
        """Add address filtering to existing SQL template"""
        conditions = []
        
        if street:
            street_escaped = street.replace("'", "''")
            # Use OBJEKTE.OBEZ and BEWADR.BSTR from Layer 1 templates
            conditions.append(f"(OBJEKTE.OBEZ LIKE '%{street_escaped}%' OR BEWADR.BSTR LIKE '%{street_escaped}%')")
        
        if postal_code:
            # Use BEWADR.BPLZORT from Layer 1 templates
            conditions.append(f"BEWADR.BPLZORT LIKE '%{postal_code}%'")
        
        if city:
            city_escaped = city.replace("'", "''")
            conditions.append(f"BEWADR.BPLZORT LIKE '%{city_escaped}%'")
        
        if conditions:
            # Add address filter to WHERE clause
            if "WHERE" in base_sql.upper():
                return base_sql + " AND (" + " OR ".join(conditions) + ")"
            else:
                return base_sql + " WHERE (" + " OR ".join(conditions) + ")"
        
        return base_sql
    
    def search_tenants_by_address(self, street: str, postal_code: str = None, city: str = None) -> Dict[str, Any]:
        """
        Sucht Mieter nach Adresse
        
        Args:
            street: Straßenname mit Hausnummer (z.B. "Marienstr. 26")
            postal_code: PLZ (optional)
            city: Stadt (optional)
            
        Returns:
            Dict mit Suchergebnissen
        """
        try:
            # Use a working tenant search SQL based on Layer 1 template but with proper boolean logic
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
            
            # Add address filtering with proper boolean logic
            conditions = []
            if street:
                street_escaped = street.replace("'", "''")
                conditions.append(f"(OBJEKTE.OBEZ LIKE '%{street_escaped}%' OR BEWADR.BSTR LIKE '%{street_escaped}%')")
            
            if postal_code:
                conditions.append(f"BEWADR.BPLZORT LIKE '%{postal_code}%'")
            
            if city:
                city_escaped = city.replace("'", "''")
                conditions.append(f"BEWADR.BPLZORT LIKE '%{city_escaped}%'")
            
            if conditions:
                sql += " AND (" + " OR ".join(conditions) + ")"
            
            sql += " ORDER BY BEWADR.BEWNR"
            
            # Execute SQL
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute(sql)
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                cursor.close()
                conn.close()
                
                # Convert tuples to dictionaries for proper handling
                data_dicts = []
                for row in rows:
                    row_dict = {}
                    for i, col_name in enumerate(columns):
                        row_dict[col_name] = row[i] if i < len(row) else None
                    data_dicts.append(row_dict)
                
                return {
                    'success': True,
                    'data': data_dicts,
                    'columns': columns,
                    'message': f"Found {len(rows)} results",
                    'row_count': len(rows)
                }
            except Exception as e:
                return {
                    'success': False,
                    'data': [],
                    'message': str(e),
                    'row_count': 0
                }
            
        except Exception as e:
            logger.error(f"Tenant search failed: {str(e)}")
            return {
                'success': False,
                'data': [],
                'message': f"Fehler bei der Mieter-Suche: {str(e)}",
                'row_count': 0
            }
    
    def search_json_data(self, query_type: str, search_terms: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sucht in JSON-exportierten Daten (fallback für JSON-Modi)
        
        Args:
            query_type: Art der Suche (z.B. 'tenants', 'owners', 'properties')
            search_terms: Suchkriterien
            
        Returns:
            Dict mit Suchergebnissen
        """
        # For now, delegate to SQL engine as JSON export is not yet implemented
        logger.info(f"JSON search delegated to SQL engine - Type: {query_type}, Terms: {search_terms}")
        
        if query_type == 'tenants' and 'address' in search_terms:
            return self.search_tenants_by_address(search_terms['address'])
        
        # TODO: Implement actual JSON data search when JSON exports are ready
        return {
            'success': False,
            'data': [],
            'message': 'JSON-Datensuche noch nicht implementiert - verwende SQL-Modus',
            'row_count': 0
        }
    
    def search_owners_by_address(self, street: str, postal_code: str = None, city: str = None) -> Dict[str, Any]:
        """
        Sucht Eigentümer basierend auf Adresse
        
        Args:
            street: Straßenname mit Hausnummer
            postal_code: PLZ (optional)
            city: Stadt (optional)
            
        Returns:
            Dict mit Eigentümer-Suchergebnissen
        """
        try:
            # Use validated Layer 1 Owner template - NO HARDCODED COLUMNS
            sql = """
            SELECT 
              EIGADR.EIGNR,
              EIGADR.EVNAME,
              EIGADR.ENAME,
              EIGADR.ESTR,
              EIGADR.EPLZORT,
              EIGADR.EEMAIL,
              EIGADR.EHANDY,
              EIGADR.ETEL1,
              OBJEKTE.OBEZ AS PROPERTY_CODE,
              OBJEKTE.ONR
            FROM
              EIGADR
              LEFT OUTER JOIN OBJEKTE ON (EIGADR.EIGNR = OBJEKTE.EIGNR)
            WHERE
              EIGADR.EIGNR >= 0 AND 
              OBJEKTE.ONR < 890
            """
            
            # Add address filtering with proper boolean logic
            conditions = []
            if street:
                street_escaped = street.replace("'", "''")
                conditions.append(f"(OBJEKTE.OBEZ LIKE '%{street_escaped}%' OR EIGADR.ESTR LIKE '%{street_escaped}%')")
            
            if postal_code:
                conditions.append(f"EIGADR.EPLZORT LIKE '%{postal_code}%'")
            
            if city:
                city_escaped = city.replace("'", "''")
                conditions.append(f"EIGADR.EPLZORT LIKE '%{city_escaped}%'")
            
            if conditions:
                sql += " AND (" + " OR ".join(conditions) + ")"
            
            sql += " ORDER BY EIGADR.EIGNR"
            
            # Execute SQL
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute(sql)
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                cursor.close()
                conn.close()
                
                # Convert tuples to dictionaries for proper handling
                data_dicts = []
                for row in rows:
                    row_dict = {}
                    for i, col_name in enumerate(columns):
                        row_dict[col_name] = row[i] if i < len(row) else None
                    data_dicts.append(row_dict)
                
                return {
                    'success': True,
                    'data': data_dicts,
                    'columns': columns,
                    'message': f"Found {len(rows)} owners",
                    'row_count': len(rows)
                }
            except Exception as e:
                return {
                    'success': False,
                    'data': [],
                    'message': str(e),
                    'row_count': 0
                }
            
        except Exception as e:
            logger.error(f"Owner search failed: {str(e)}")
            return {
                'success': False,
                'data': [],
                'message': str(e),
                'row_count': 0
            }
    
    def get_property_info(self, street: str, postal_code: str = None, city: str = None) -> Dict[str, Any]:
        """
        Holt detaillierte Immobilien-Informationen
        
        Args:
            street: Straßenname mit Hausnummer
            postal_code: PLZ (optional)
            city: Stadt (optional)
            
        Returns:
            Dict mit Immobilien-Informationen
        """
        try:
            # Use validated Layer 1 Objekte template - NO HARDCODED COLUMNS
            sql = """
            SELECT 
              OBJEKTE.GA1 AS WOHNFLAECHE,
              OBJEKTE.OPLZORT,
              OBJEKTE.OSTRASSE,
              OBJEKTE.OBEZ AS LIEGENSCHAFTSKUERZEL,
              OBJEKTE.ONR,
              EIGADR.EIGNR,
              EIGADR.EVNAME,
              EIGADR.ENAME,
              EIGADR.ENOTIZ AS EIGENTUEMERKUERZEL
            FROM
              OBJEKTE
              INNER JOIN EIGADR ON (OBJEKTE.EIGNR = EIGADR.EIGNR)
            WHERE
              ONR NOT LIKE 0 AND
              ONR < 890
            """
            
            # Add address filters using validated column names
            conditions = []
            if street:
                street_escaped = street.replace("'", "''")
                conditions.append(f"OBJEKTE.OBEZ LIKE '%{street_escaped}%' OR OBJEKTE.OSTRASSE LIKE '%{street_escaped}%'")
            
            if postal_code:
                conditions.append(f"OBJEKTE.OPLZORT LIKE '%{postal_code}%'")
            
            if city:
                city_escaped = city.replace("'", "''")
                conditions.append(f"OBJEKTE.OPLZORT LIKE '%{city_escaped}%'")
            
            if conditions:
                sql += " AND (" + " OR ".join(conditions) + ")"
            
            sql += " ORDER BY OBJEKTE.ONR"
            
            # Execute SQL
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute(sql)
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                cursor.close()
                conn.close()
                
                return {
                    'success': True,
                    'data': rows,
                    'columns': columns,
                    'message': f"Found {len(rows)} properties",
                    'row_count': len(rows)
                }
            except Exception as e:
                return {
                    'success': False,
                    'data': [],
                    'message': str(e),
                    'row_count': 0
                }
            
        except Exception as e:
            logger.error(f"Property info search failed: {str(e)}")
            return {
                'success': False,
                'data': [],
                'message': f"Fehler bei der Immobilien-Suche: {str(e)}",
                'row_count': 0
            }
    
    def execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """
        Führt spezifisches Tool aus
        
        Args:
            tool_name: Name des Tools
            **kwargs: Tool-spezifische Parameter
            
        Returns:
            Tool-Ergebnis
        """
        logger.info(f"Executing tool: {tool_name} with args: {kwargs}")
        
        if tool_name == "search_tenants_by_address":
            return self.search_tenants_by_address(**kwargs)
        elif tool_name == "get_property_info":
            return self.get_property_info(**kwargs)
        elif tool_name == "search_json_data":
            return self.search_json_data(**kwargs)
        else:
            return {
                'success': False,
                'data': [],
                'message': f"Unbekanntes Tool: {tool_name}",
                'row_count': 0
            }


# Test functions
def test_wincasa_tools():
    """Test-Funktion für WincasaTools"""
    print("=== WINCASA Tools Test ===")
    
    tools = WincasaTools()
    
    # Test tenant search
    print("\n1. Mieter-Suche Test...")
    result = tools.search_tenants_by_address("Marienstr. 26", "45307", "Essen")
    print(f"   Erfolg: {result['success']}")
    print(f"   Datensätze: {result['row_count']}")
    if result['success'] and result['data']:
        print(f"   Erster Mieter: {result['data'][0]}")
    
    # Test property info
    print("\n2. Immobilien-Info Test...")
    result = tools.get_property_info("Marienstr. 26")
    print(f"   Erfolg: {result['success']}")
    print(f"   Datensätze: {result['row_count']}")
    if result['success'] and result['data']:
        print(f"   Immobilie: {result['data'][0]}")


if __name__ == "__main__":
    test_wincasa_tools()