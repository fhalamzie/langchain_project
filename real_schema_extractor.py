#!/usr/bin/env python3
"""
Real Schema Extractor for WINCASA Database
=========================================

Extracts actual schema and sample data from WINCASA2022.FDB database
to replace all mock documents with real data.

This eliminates hardcoded mock data and ensures all retrievers work
with actual database schema and content.
"""

import logging
from typing import Dict, List, Any, Optional
from langchain_core.documents import Document
import fdb

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RealSchemaExtractor:
    """Extracts real schema and data from WINCASA database."""
    
    def __init__(self, db_connection_string: str = None):
        """Initialize with database connection."""
        self.db_connection = db_connection_string or "firebird+fdb://sysdba:masterkey@localhost:3050//home/projects/langchain_project/WINCASA2022.FDB"
        self.connection = None
        
    def connect(self):
        """Establish database connection."""
        try:
            self.connection = fdb.connect(
                host='localhost',
                port=3050,
                database='/home/projects/langchain_project/WINCASA2022.FDB',
                user='SYSDBA',
                password='masterkey'
            )
            logger.info("✅ Connected to WINCASA database")
            return True
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False
    
    def disconnect(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """Extract real schema for a specific table."""
        if not self.connection:
            return {}
            
        try:
            cursor = self.connection.cursor()
            
            # Get column information
            cursor.execute("""
                SELECT 
                    r.RDB$FIELD_NAME as column_name,
                    f.RDB$FIELD_TYPE as field_type,
                    f.RDB$FIELD_LENGTH as field_length,
                    r.RDB$NULL_FLAG as nullable
                FROM RDB$RELATION_FIELDS r
                LEFT JOIN RDB$FIELDS f ON r.RDB$FIELD_SOURCE = f.RDB$FIELD_NAME
                WHERE r.RDB$RELATION_NAME = ?
                ORDER BY r.RDB$FIELD_POSITION
            """, (table_name.upper(),))
            
            columns = []
            for row in cursor.fetchall():
                col_name = row[0].strip() if row[0] else ""
                field_type = row[1] if row[1] else 0
                field_length = row[2] if row[2] else 0
                nullable = row[3] if row[3] else 1
                
                # Map Firebird types to readable names
                type_map = {
                    7: "SMALLINT",
                    8: "INTEGER", 
                    9: "QUAD",
                    10: "FLOAT",
                    11: "D_FLOAT",
                    12: "DATE",
                    13: "TIME",
                    14: "CHAR",
                    16: "BIGINT",
                    27: "DOUBLE",
                    35: "TIMESTAMP",
                    37: "VARCHAR",
                    261: "BLOB"
                }
                
                type_name = type_map.get(field_type, f"TYPE_{field_type}")
                if type_name in ["CHAR", "VARCHAR"] and field_length:
                    type_name += f"({field_length})"
                    
                columns.append({
                    "name": col_name,
                    "type": type_name,
                    "nullable": nullable != 1
                })
            
            cursor.close()
            return {"columns": columns}
            
        except Exception as e:
            logger.error(f"❌ Schema extraction failed for {table_name}: {e}")
            return {}
    
    def get_sample_data(self, table_name: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Extract real sample data from table."""
        if not self.connection:
            return []
            
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"SELECT FIRST {limit} * FROM {table_name}")
            
            # Get column names
            columns = [desc[0].strip() for desc in cursor.description]
            
            # Get sample rows
            rows = cursor.fetchall()
            samples = []
            
            for row in rows:
                sample = {}
                for i, value in enumerate(row):
                    col_name = columns[i]
                    # Clean up string values
                    if isinstance(value, str):
                        value = value.strip()
                    sample[col_name] = value
                samples.append(sample)
            
            cursor.close()
            return samples
            
        except Exception as e:
            logger.error(f"❌ Sample data extraction failed for {table_name}: {e}")
            return []
    
    def get_table_count(self, table_name: str) -> int:
        """Get actual row count for table."""
        if not self.connection:
            return 0
            
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            cursor.close()
            return count
        except Exception as e:
            logger.error(f"❌ Count failed for {table_name}: {e}")
            return 0
    
    def create_real_document(self, table_name: str, business_purpose: str = "") -> Document:
        """Create a Document with real schema and sample data."""
        schema = self.get_table_schema(table_name)
        samples = self.get_sample_data(table_name, 3)
        count = self.get_table_count(table_name)
        
        # Build content with real data
        content_parts = [f"table_name: {table_name}"]
        
        if business_purpose:
            content_parts.append(f"business_purpose: {business_purpose}")
        
        # Add column information
        if schema.get("columns"):
            content_parts.append("columns:")
            for col in schema["columns"]:
                nullable = " (nullable)" if col["nullable"] else ""
                content_parts.append(f"  - {col['name']}: {col['type']}{nullable}")
        
        # Add real sample data
        if samples:
            content_parts.append("real_sample_data:")
            for i, sample in enumerate(samples, 1):
                sample_line = f"  sample_{i}: "
                sample_values = []
                for key, value in sample.items():
                    if value is not None and str(value).strip():
                        sample_values.append(f"{key}='{value}'")
                if sample_values:
                    sample_line += ", ".join(sample_values[:3])  # First 3 fields
                    content_parts.append(sample_line)
        
        # Add real count
        content_parts.append(f"real_record_count: {count}")
        
        # Create metadata
        metadata = {
            "table_name": table_name.upper(),
            "real_data": True,
            "record_count": count,
            "source": "WINCASA2022.FDB"
        }
        
        # Classify query type based on table name
        table_lower = table_name.lower()
        if "wohnung" in table_lower:
            metadata["query_type"] = "property_count"
        elif "bewohner" in table_lower:
            metadata["query_type"] = "address_lookup"
        elif "eigentuemer" in table_lower:
            metadata["query_type"] = "owner_lookup"
        elif "konto" in table_lower:
            metadata["query_type"] = "financial_query"
        else:
            metadata["query_type"] = "general_property"
        
        content = "\n".join(content_parts)
        
        return Document(page_content=content, metadata=metadata)
    
    def extract_all_core_documents(self) -> List[Document]:
        """Extract Documents for all core WINCASA tables."""
        if not self.connect():
            return []
        
        try:
            # Core WINCASA tables with business purposes
            tables = [
                ("WOHNUNG", "Individual apartment/housing units within objects"),
                ("BEWOHNER", "Residents and tenants database with contact information"),
                ("EIGENTUEMER", "Property owners database with contact details"),
                ("OBJEKTE", "Property objects and buildings"),
                ("KONTEN", "Financial accounts for properties")
            ]
            
            documents = []
            for table_name, business_purpose in tables:
                logger.info(f"Extracting real data for {table_name}...")
                doc = self.create_real_document(table_name, business_purpose)
                if doc.page_content:
                    documents.append(doc)
                    logger.info(f"✅ {table_name}: {doc.metadata.get('record_count', 0)} records")
            
            logger.info(f"✅ Extracted {len(documents)} real documents")
            return documents
            
        finally:
            self.disconnect()

def create_real_documents() -> List[Document]:
    """
    Public function to replace create_mock_documents().
    
    Returns real Documents extracted from WINCASA2022.FDB database.
    """
    extractor = RealSchemaExtractor()
    return extractor.extract_all_core_documents()

# For backwards compatibility and testing
def get_real_apartment_count() -> int:
    """Get real apartment count from database."""
    extractor = RealSchemaExtractor()
    if extractor.connect():
        try:
            count = extractor.get_table_count("WOHNUNG")
            return count
        finally:
            extractor.disconnect()
    return 0

if __name__ == "__main__":
    # Test the extractor
    print("🔍 Testing Real Schema Extractor")
    print("=" * 50)
    
    documents = create_real_documents()
    
    for doc in documents:
        print(f"\n📄 {doc.metadata['table_name']}")
        print(f"   Records: {doc.metadata['record_count']}")
        print(f"   Query type: {doc.metadata['query_type']}")
        print(f"   Content preview: {doc.page_content[:100]}...")
    
    print(f"\n✅ Real Documents Created: {len(documents)}")
    print(f"🎯 Real apartment count: {get_real_apartment_count()}")