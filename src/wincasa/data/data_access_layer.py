#!/usr/bin/env python3
"""
WINCASA Unified Data Access Layer
=================================

Provides standardized data access interface that normalizes results
from both SQL and JSON sources into consistent dictionary format.

Architecture Decision: Option A - Standardize Data Access Layer
- Always returns standardized dictionaries
- Consistent field mapping regardless of source
- Unified interface for all data operations
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)

class WincasaDataAccess:
    """
    Unified data access interface for WINCASA system.
    
    Handles both SQL direct access and JSON export data sources,
    normalizing all results to standardized dictionary format.
    """
    
    # Standardized field mappings - covers all known variations
    STANDARD_FIELD_MAP = {
        # Tenant Names
        'BEWNAME': 'last_name',
        'NACHNAME': 'last_name', 
        'BNAME': 'last_name',
        'BEWVNAME': 'first_name',
        'VORNAME': 'first_name',
        'BVNAME': 'first_name',
        
        # Tenant IDs and References
        'BEWNR': 'tenant_id',
        'KNR': 'account_id',
        
        # Apartment/Unit Information
        'ENR': 'unit_number',
        'ONR': 'object_number', 
        'WHGNR': 'apartment_number',
        'WOHNUNGSBEZ': 'apartment_description',
        'EBEZ': 'unit_description',
        'LAGE': 'location',
        
        # Address Information  
        'BSTR': 'street',
        'STRASSE': 'street',
        'BPLZORT': 'postal_city',
        'PLZ_ORT': 'postal_city',
        
        # Contact Information
        'BTEL': 'phone',
        'TELEFON': 'phone',
        'BEMAIL': 'email',
        'EMAIL': 'email',
        
        # Property Information
        'OBEZ': 'property_code',
        'LIEGENSCHAFTSKUERZEL': 'property_code',
        
        # Dates
        'VBEGINN': 'lease_start',
        'VENDE': 'lease_end',
        
        # Owner Information
        'EIGNR': 'owner_id',
        'ENAME': 'owner_last_name',
        'EVNAME': 'owner_first_name',
        'ESTR': 'owner_street',
        'EPLZORT': 'owner_postal_city',
        'EEMAIL': 'owner_email',
        'EHANDY': 'owner_phone',
        'ETEL1': 'owner_phone',
    }
    
    def __init__(self, source: str = "auto"):
        """
        Initialize data access layer.
        
        Args:
            source: Data source type ("sql", "json", or "auto")
        """
        self.source = source.lower()
        self._sql_tools = None
        self._json_loader = None
        
    def _get_sql_tools(self):
        """Lazy load SQL tools to avoid circular imports"""
        if self._sql_tools is None:
            # WincasaTools functionality now integrated into sql_executor
            from wincasa.data.sql_executor import WincasaSQLExecutor
            self._sql_tools = WincasaSQLExecutor()
        return self._sql_tools
    
    def _get_json_loader(self):
        """Lazy load JSON loader to avoid circular imports"""
        if self._json_loader is None:
            from wincasa.data.layer4_json_loader import Layer4JSONLoader
            self._json_loader = Layer4JSONLoader()
        return self._json_loader
    
    def search_owners_by_address(self, street: str, postal_code: str = None,
                               city: str = None) -> Dict[str, Any]:
        """
        Search for owners by address using unified interface.
        
        Returns standardized format regardless of data source.
        """
        logger.info(f"Searching owners for: {street}, {postal_code}, {city}")
        
        try:
            if self.source in ["sql", "auto"]:
                # Try SQL first for real-time data
                result = self._search_owners_sql(street, postal_code, city)
                if result['success'] and result['data']:
                    return self._normalize_result(result)
            
            if self.source in ["json", "auto"]:
                # Fallback to JSON or use JSON if explicitly requested
                result = self._search_owners_json(street, postal_code, city)
                return self._normalize_result(result)
                
        except Exception as e:
            logger.error(f"Owner search failed: {e}")
            return {
                'success': False,
                'data': [],
                'message': f"Search error: {str(e)}",
                'source': self.source
            }

    def search_tenants_by_address(self, street: str, postal_code: str = None, 
                                city: str = None) -> Dict[str, Any]:
        """
        Search for tenants by address using unified interface.
        
        Returns standardized format regardless of data source.
        """
        logger.info(f"Searching tenants for: {street}, {postal_code}, {city}")
        
        try:
            if self.source in ["sql", "auto"]:
                # Try SQL first for real-time data
                result = self._search_tenants_sql(street, postal_code, city)
                if result['success'] and result['data']:
                    return self._normalize_result(result)
            
            if self.source in ["json", "auto"]:
                # Fallback to JSON or use JSON if explicitly requested
                result = self._search_tenants_json(street, postal_code, city)
                return self._normalize_result(result)
                
        except Exception as e:
            logger.error(f"Tenant search failed: {e}")
            return {
                'success': False,
                'data': [],
                'message': f"Search error: {str(e)}",
                'source': self.source
            }
    
    def _search_owners_sql(self, street: str, postal_code: str = None, 
                         city: str = None) -> Dict[str, Any]:
        """Execute SQL-based owner search"""
        tools = self._get_sql_tools()
        # Check if tools has owner search method, otherwise use generic property search
        if hasattr(tools, 'search_owners_by_address'):
            return tools.search_owners_by_address(street, postal_code, city)
        else:
            return tools.get_property_info(street, postal_code, city)
    
    def _search_owners_json(self, street: str, postal_code: str = None,
                          city: str = None) -> Dict[str, Any]:
        """Execute JSON-based owner search"""
        loader = self._get_json_loader()
        
        # Load owner data from JSON export
        data = loader.load_json_data('01_eigentuemer')
        if not data:
            return {'success': False, 'data': [], 'message': 'Owner JSON data not available'}
        
        # Parse street and house number
        import re
        street_parts = re.match(r'^(.+?)\s+(\d+\w*)$', street.strip())
        if street_parts:
            search_street_name = street_parts.group(1).lower()
            search_house_num = street_parts.group(2).lower()
        else:
            # No house number found, use whole string
            search_street_name = street.lower()
            search_house_num = None
        
        # Filter by address
        filtered_owners = []
        
        for owner in data.get('data', []):
            # Check different address fields for owners
            owner_street_full = str(owner.get('ESTR', '')).lower()
            
            # Parse owner address
            owner_parts = re.match(r'^(.+?)\s+(\d+\w*)$', owner_street_full.strip())
            if owner_parts:
                owner_street_name = owner_parts.group(1).lower()
                owner_house_num = owner_parts.group(2).lower()
            else:
                owner_street_name = owner_street_full
                owner_house_num = None
            
            # Check street name match
            street_name_match = (
                self._normalize_street_name(search_street_name) == 
                self._normalize_street_name(owner_street_name)
            )
            
            if not street_name_match:
                continue
                
            # Check house number match if provided
            if search_house_num and owner_house_num:
                if search_house_num != owner_house_num:
                    continue
            elif search_house_num and not owner_house_num:
                # We're looking for a specific number but owner has none
                continue
            
            # Additional filters
            if postal_code and str(postal_code) not in str(owner.get('EPLZORT', '')):
                continue
            if city and city.lower() not in str(owner.get('EPLZORT', '')).lower():
                continue
                
            filtered_owners.append(owner)
        
        return {
            'success': True,
            'data': filtered_owners,
            'message': f"Found {len(filtered_owners)} owners",
            'source': 'json'
        }
    
    def _search_tenants_sql(self, street: str, postal_code: str = None, 
                          city: str = None) -> Dict[str, Any]:
        """Execute SQL-based tenant search"""
        tools = self._get_sql_tools()
        return tools.search_tenants_by_address(street, postal_code, city)
    
    def _search_tenants_json(self, street: str, postal_code: str = None,
                           city: str = None) -> Dict[str, Any]:
        """Execute JSON-based tenant search"""
        loader = self._get_json_loader()
        
        # Load tenant data from JSON export
        data = loader.load_json_data('03_aktuelle_mieter')
        if not data:
            return {'success': False, 'data': [], 'message': 'JSON data not available'}
        
        # Parse street and house number
        import re
        street_parts = re.match(r'^(.+?)\s+(\d+\w*)$', street.strip())
        if street_parts:
            search_street_name = street_parts.group(1).lower()
            search_house_num = street_parts.group(2).lower()
        else:
            # No house number found, use whole string
            search_street_name = street.lower()
            search_house_num = None
        
        # Filter by address
        filtered_tenants = []
        
        for tenant in data.get('data', []):
            tenant_street_full = str(tenant.get('STRASSE', '')).lower()
            
            # Parse tenant address
            tenant_parts = re.match(r'^(.+?)\s+(\d+\w*)$', tenant_street_full.strip())
            if tenant_parts:
                tenant_street_name = tenant_parts.group(1).lower()
                tenant_house_num = tenant_parts.group(2).lower()
            else:
                tenant_street_name = tenant_street_full
                tenant_house_num = None
            
            # Check street name match
            street_name_match = (
                self._normalize_street_name(search_street_name) == 
                self._normalize_street_name(tenant_street_name)
            )
            
            if not street_name_match:
                continue
                
            # Check house number match if provided
            if search_house_num and tenant_house_num:
                if search_house_num != tenant_house_num:
                    continue
            elif search_house_num and not tenant_house_num:
                # We're looking for a specific number but tenant has none
                continue
            
            # Additional filters
            if postal_code and str(postal_code) not in str(tenant.get('PLZ_ORT', '')):
                continue
            if city and city.lower() not in str(tenant.get('PLZ_ORT', '')).lower():
                continue
                
            filtered_tenants.append(tenant)
        
        return {
            'success': True,
            'data': filtered_tenants,
            'message': f"Found {len(filtered_tenants)} tenants",
            'source': 'json'
        }
    
    def _normalize_street_name(self, street: str) -> str:
        """Normalize street names for better matching"""
        normalized = street.lower().strip()
        # Handle common abbreviations
        normalized = normalized.replace('str.', 'straße')
        normalized = normalized.replace('str ', 'straße ')
        normalized = normalized.replace('strasse', 'straße')
        # Remove trailing punctuation
        normalized = normalized.rstrip('.,;:')
        return normalized
    
    def _normalize_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize result format and field names to standard format.
        
        Converts tuples to dicts and standardizes field names.
        """
        if not result.get('success') or not result.get('data'):
            return result
        
        normalized_data = []
        
        for record in result['data']:
            normalized_record = self._normalize_record(record, result.get('columns', []))
            normalized_data.append(normalized_record)
        
        # Deduplicate based on standardized keys
        unique_tenants = self._deduplicate_tenants(normalized_data)
        
        return {
            'success': True,
            'data': unique_tenants,
            'message': f"Found {len(unique_tenants)} unique tenants",
            'source': result.get('source', self.source),
            'total_records': len(result['data']),
            'unique_records': len(unique_tenants)
        }
    
    def _normalize_record(self, record: Union[tuple, dict], columns: List[str] = None) -> Dict[str, Any]:
        """
        Convert record to standardized dictionary format.
        
        Handles both tuple (SQL) and dict (JSON) inputs.
        """
        # Convert tuple to dict using column names
        if isinstance(record, tuple):
            if not columns:
                raise ValueError("Column names required for tuple conversion")
            record = dict(zip(columns, record))
        
        # Apply field name standardization
        standardized = {}
        for key, value in record.items():
            # Map to standard field name, keep original if no mapping exists
            std_key = self.STANDARD_FIELD_MAP.get(key, key.lower())
            standardized[std_key] = value
            
            # Also keep original key for backward compatibility during transition
            if key not in standardized:
                standardized[key] = value
        
        return standardized
    
    def _deduplicate_tenants(self, tenants: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicate tenant records based on key identifying fields.
        
        Handles cases where same tenant has multiple billing records.
        """
        unique_tenants = {}
        
        for tenant in tenants:
            # Create unique key based on identifying information
            key = (
                tenant.get('object_number', ''),
                tenant.get('unit_number', ''), 
                tenant.get('last_name', '').strip(),
                tenant.get('first_name', '').strip(),
                tenant.get('tenant_id', '')
            )
            
            # Keep first occurrence or one with more complete data
            if key not in unique_tenants or self._is_more_complete(tenant, unique_tenants[key]):
                unique_tenants[key] = tenant
        
        return list(unique_tenants.values())
    
    def _is_more_complete(self, tenant1: Dict[str, Any], tenant2: Dict[str, Any]) -> bool:
        """Check if tenant1 has more complete information than tenant2"""
        # Count non-empty fields
        count1 = sum(1 for v in tenant1.values() if v and str(v).strip())
        count2 = sum(1 for v in tenant2.values() if v and str(v).strip())
        return count1 > count2


# Convenience function for easy integration
def get_data_access(source: str = "auto") -> WincasaDataAccess:
    """Get configured data access instance"""
    return WincasaDataAccess(source=source)