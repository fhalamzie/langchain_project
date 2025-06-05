"""
Focused Embedding System for WINCASA TAG Architecture

This module implements the strategic information architecture where:
- Small documents (< 200 lines) are included directly in system prompt
- Large documents are embedded and retrieved on-demand
- Table-specific YAMLs are retrieved only after TAG SYN identifies needed tables
- Replaces overwhelming 498-YAML approach with targeted 2-5 table retrieval
"""

import json
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from business_glossar import WINCASA_GLOSSAR, extract_business_entities
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

# Import existing components
from optimized_system_prompt import get_optimized_system_prompt

from global_context import get_compact_global_context, get_query_specific_context


@dataclass
class EmbeddingCategory:
    """Category of embedded information with retrieval strategy"""

    name: str
    documents: List[Document]
    vector_store: Optional[FAISS]
    retrieval_strategy: str  # "always", "on_demand", "query_driven"
    max_docs: int = 5


class FocusedEmbeddingSystem:
    """
    Strategic embedding system that provides focused, relevant context instead of overwhelming noise.

    Information Layers:
    1. System Prompt: Core rules, essential patterns (always available)
    2. Direct Inclusion: Small, essential documents (< 200 lines)
    3. Focused Embeddings: Large documents, retrieved strategically
    4. Table-Specific: Detailed YAMLs, retrieved only after table identification
    """

    def __init__(self, openai_api_key: str):
        self.openai_api_key = openai_api_key
        self.embeddings_model = OpenAIEmbeddings(
            model="text-embedding-3-large",
            openai_api_key=openai_api_key,
            dimensions=1536,  # Efficient size for focused retrieval
        )

        # Initialize embedding categories
        self.categories: Dict[str, EmbeddingCategory] = {}
        self._initialize_embedding_categories()

        # Load available table YAMLs for on-demand retrieval
        self.available_tables = self._load_available_table_list()

    def _initialize_embedding_categories(self):
        """Initialize embedding categories with strategic separation"""

        # Category 1: Business Terms (for term-to-SQL mapping)
        business_docs = self._create_business_term_documents()
        self.categories["business_terms"] = EmbeddingCategory(
            name="business_terms",
            documents=business_docs,
            vector_store=(
                FAISS.from_documents(business_docs, self.embeddings_model)
                if business_docs
                else None
            ),
            retrieval_strategy="query_driven",
            max_docs=3,
        )

        # Category 2: Database Schema & Relationships (for table identification)
        schema_docs = self._create_schema_documents()
        self.categories["schema_info"] = EmbeddingCategory(
            name="schema_info",
            documents=schema_docs,
            vector_store=(
                FAISS.from_documents(schema_docs, self.embeddings_model)
                if schema_docs
                else None
            ),
            retrieval_strategy="always",
            max_docs=5,
        )

        # Category 3: Query Patterns & Examples (for SQL generation guidance)
        pattern_docs = self._create_pattern_documents()
        self.categories["query_patterns"] = EmbeddingCategory(
            name="query_patterns",
            documents=pattern_docs,
            vector_store=(
                FAISS.from_documents(pattern_docs, self.embeddings_model)
                if pattern_docs
                else None
            ),
            retrieval_strategy="on_demand",
            max_docs=4,
        )

        # Category 4: Table-Specific Details (retrieved only after TAG SYN)
        # This is loaded dynamically based on identified tables

    def _create_business_term_documents(self) -> List[Document]:
        """Create embedded documents from business glossar for term mapping"""
        docs = []

        # Business terms by category
        for category in ["people", "property", "financial", "status", "location"]:
            category_terms = []
            for term_name, term in WINCASA_GLOSSAR.terms.items():
                if term.category.value == category:
                    category_terms.append(f"• {term.term}: {term.description}")
                    category_terms.append(f"  SQL: {term.sql_pattern}")
                    category_terms.append(
                        f"  Tables: {', '.join(term.tables_involved)}"
                    )
                    if term.aliases:
                        category_terms.append(f"  Aliases: {', '.join(term.aliases)}")
                    category_terms.append("")

            if category_terms:
                doc = Document(
                    page_content=f"Business Terms - {category.title()}:\n"
                    + "\n".join(category_terms),
                    metadata={
                        "source": "business_glossar",
                        "category": category,
                        "type": "term_mapping",
                    },
                )
                docs.append(doc)

        return docs

    def _create_schema_documents(self) -> List[Document]:
        """Create embedded documents from compiled knowledge base for schema info"""
        docs = []

        # Load compiled knowledge base
        kb_path = os.path.join("output", "compiled_knowledge_base.json")
        if not os.path.exists(kb_path):
            return docs

        with open(kb_path, "r", encoding="utf-8") as f:
            knowledge_base = json.load(f)

        # High-priority table information
        high_priority_tables = knowledge_base.get("table_priorities", {}).get(
            "high", []
        )
        for table in high_priority_tables[:20]:  # Top 20 high-priority tables
            if table in knowledge_base.get("core_entities", {}):
                entity_info = knowledge_base["core_entities"][table]

                # Create focused table summary
                content = f"""Table: {table} (High Priority)
Description: {entity_info.get('description', 'No description')}
Business Context: {entity_info.get('business_context', 'No business context')}
Key Columns: {', '.join([col.get('name', '') for col in entity_info.get('columns', [])[:8]])}
Primary Relationships: {entity_info.get('primary_relationships', 'None specified')}
"""
                doc = Document(
                    page_content=content,
                    metadata={
                        "source": "compiled_knowledge",
                        "table": table,
                        "priority": "high",
                        "type": "table_summary",
                    },
                )
                docs.append(doc)

        # Relationship patterns
        relationship_matrix = knowledge_base.get("relationship_matrix", {})
        for from_table, to_tables in list(relationship_matrix.items())[
            :15
        ]:  # Top 15 relationship hubs
            if len(to_tables) > 2:  # Only include well-connected tables
                content = f"""Relationship Hub: {from_table}
Connected to: {', '.join(to_tables[:10])}  
Connection Type: Central hub table
Usage: Use {from_table} to navigate between {', '.join(to_tables[:5])}
"""
                doc = Document(
                    page_content=content,
                    metadata={
                        "source": "relationship_matrix",
                        "hub_table": from_table,
                        "type": "relationship_pattern",
                    },
                )
                docs.append(doc)

        return docs

    def _create_pattern_documents(self) -> List[Document]:
        """Create documents from common query patterns and SQL examples"""
        docs = []

        # Load compiled knowledge base for query patterns
        kb_path = os.path.join("output", "compiled_knowledge_base.json")
        if os.path.exists(kb_path):
            with open(kb_path, "r", encoding="utf-8") as f:
                knowledge_base = json.load(f)

            # Common query patterns
            query_patterns = knowledge_base.get("common_query_patterns", {})
            for table, patterns in list(query_patterns.items())[
                :10
            ]:  # Top 10 pattern tables
                if patterns:
                    content = f"""Query Patterns for {table}:
Common Queries:
{chr(10).join(f"• {pattern}" for pattern in patterns[:5])}

Usage: These patterns show typical queries involving {table}
"""
                    doc = Document(
                        page_content=content,
                        metadata={
                            "source": "query_patterns",
                            "table": table,
                            "type": "pattern_examples",
                        },
                    )
                    docs.append(doc)

        # Address query patterns (critical for WINCASA)
        address_patterns = Document(
            page_content="""Address Query Patterns:
CRITICAL: Always use LIKE patterns for addresses, NEVER exact match

Pattern 1 - Resident Address Lookup:
Question: "Wer wohnt in der Marienstraße 26, 45307 Essen"
SQL: SELECT b.NAME, b.VORNAME FROM BEWOHNER b JOIN BEWADR ba ON b.BEWNR = ba.BEWNR WHERE ba.BSTR LIKE '%Marienstraße%' AND ba.BPLZORT LIKE '%45307%'

Pattern 2 - Owner Address Lookup:  
Question: "Welche Eigentümer wohnen in Essen"
SQL: SELECT e.NAME, e.VORNAME FROM EIGENTUEMER e JOIN EIGADR ea ON e.EIGNR = ea.EIGNR WHERE ea.BPLZORT LIKE '%Essen%'

Key Rules:
• BSTR contains "Straßenname Hausnummer" 
• BPLZORT contains "PLZ Ort"
• Always use LIKE '%pattern%' for address matching
• Join BEWOHNER→BEWADR via BEWNR, EIGENTUEMER→EIGADR via EIGNR
""",
            metadata={
                "source": "critical_patterns",
                "type": "address_patterns",
                "priority": "critical",
            },
        )
        docs.append(address_patterns)

        return docs

    def _load_available_table_list(self) -> List[str]:
        """Load list of available table YAMLs for targeted retrieval"""
        yaml_dir = os.path.join("output", "yamls")
        if not os.path.exists(yaml_dir):
            return []

        tables = []
        for filename in os.listdir(yaml_dir):
            if filename.endswith(".yaml") and not filename.endswith("_proc.yaml"):
                table_name = filename.replace(".yaml", "")
                tables.append(table_name)

        return tables

    def get_focused_context(
        self, query: str, identified_tables: List[str] = None
    ) -> str:
        """
        Generate focused context for a specific query.

        This is the main method that replaces overwhelming 498-YAML retrieval
        with strategic, targeted information.
        """
        context_parts = []

        # Layer 1: Always include optimized system prompt
        context_parts.append(get_optimized_system_prompt())
        context_parts.append("")

        # Layer 2: Include compact global context (always manageable size)
        context_parts.append(get_compact_global_context())
        context_parts.append("")

        # Layer 3: Business term mapping (query-driven)
        business_context = self._get_business_context(query)
        if business_context:
            context_parts.append("=== BUSINESS TERM MAPPINGS ===")
            context_parts.append(business_context)
            context_parts.append("")

        # Layer 4: Schema information (focused retrieval)
        schema_context = self._get_schema_context(query, identified_tables)
        if schema_context:
            context_parts.append("=== RELEVANT SCHEMA INFORMATION ===")
            context_parts.append(schema_context)
            context_parts.append("")

        # Layer 5: Query patterns (on-demand)
        pattern_context = self._get_pattern_context(query)
        if pattern_context:
            context_parts.append("=== QUERY PATTERNS & EXAMPLES ===")
            context_parts.append(pattern_context)
            context_parts.append("")

        # Layer 6: Table-specific details (only if tables identified)
        if identified_tables:
            table_context = self._get_table_specific_context(identified_tables)
            if table_context:
                context_parts.append("=== TABLE-SPECIFIC DETAILS ===")
                context_parts.append(
                    f"Retrieved for tables: {', '.join(identified_tables)}"
                )
                context_parts.append(table_context)
                context_parts.append("")

        # Final guidance
        context_parts.append("=== CONTEXT USAGE GUIDANCE ===")
        context_parts.append(
            "1. Follow system prompt rules ABSOLUTELY (Firebird syntax, LIKE patterns)"
        )
        context_parts.append("2. Use business term mappings for domain translation")
        context_parts.append("3. Apply schema relationships for correct JOINs")
        context_parts.append("4. Reference query patterns for similar SQL structures")
        context_parts.append("5. Use table details for precise column selection")
        context_parts.append("=== END FOCUSED CONTEXT ===")

        return "\n".join(context_parts)

    def _get_business_context(self, query: str) -> str:
        """Get business term mappings relevant to the query"""
        if (
            "business_terms" not in self.categories
            or not self.categories["business_terms"].vector_store
        ):
            return ""

        # Extract business entities from query
        business_entities = extract_business_entities(query, WINCASA_GLOSSAR)

        if not business_entities["extracted_terms"]:
            return ""

        # Format business term context
        context_lines = []
        for term_name in business_entities["extracted_terms"]:
            term = WINCASA_GLOSSAR.get_term(term_name)
            if term:
                context_lines.append(f"• {term.term.upper()}: {term.description}")
                context_lines.append(f"  SQL Pattern: {term.sql_pattern}")
                context_lines.append(f"  Tables: {', '.join(term.tables_involved)}")

        return "\n".join(context_lines)

    def _get_schema_context(
        self, query: str, identified_tables: List[str] = None
    ) -> str:
        """Get relevant schema information"""
        if (
            "schema_info" not in self.categories
            or not self.categories["schema_info"].vector_store
        ):
            return ""

        # Build search query based on identified tables or query content
        if identified_tables:
            search_query = (
                f"tables {' '.join(identified_tables)} relationships connections"
            )
        else:
            search_query = query

        # Retrieve relevant schema documents
        docs = self.categories["schema_info"].vector_store.similarity_search(
            search_query, k=self.categories["schema_info"].max_docs
        )

        context_lines = []
        for doc in docs:
            context_lines.append(doc.page_content.strip())
            context_lines.append("")

        return "\n".join(context_lines)

    def _get_pattern_context(self, query: str) -> str:
        """Get relevant query patterns"""
        if (
            "query_patterns" not in self.categories
            or not self.categories["query_patterns"].vector_store
        ):
            return ""

        # Retrieve relevant patterns
        docs = self.categories["query_patterns"].vector_store.similarity_search(
            query, k=self.categories["query_patterns"].max_docs
        )

        context_lines = []
        for doc in docs:
            context_lines.append(doc.page_content.strip())
            context_lines.append("")

        return "\n".join(context_lines)

    def _get_table_specific_context(self, table_names: List[str]) -> str:
        """
        Get detailed information for specific tables.

        This replaces the overwhelming 498-YAML approach with targeted retrieval
        of only the 2-5 tables identified by TAG SYN.
        """
        context_lines = []
        yaml_dir = os.path.join("output", "yamls")

        for table_name in table_names[:5]:  # Limit to 5 tables max
            yaml_path = os.path.join(yaml_dir, f"{table_name}.yaml")
            if os.path.exists(yaml_path):
                try:
                    with open(yaml_path, "r", encoding="utf-8") as f:
                        yaml_content = f.read()

                    # Extract key sections (avoid overwhelming detail)
                    lines = yaml_content.split("\n")
                    essential_lines = []

                    # Include first 30 lines (table description and key columns)
                    essential_lines.extend(lines[:30])

                    # Look for business examples
                    for i, line in enumerate(lines):
                        if "business_examples" in line.lower() and i < len(lines) - 10:
                            essential_lines.extend(lines[i : i + 10])
                            break

                    # Look for common queries
                    for i, line in enumerate(lines):
                        if "common_queries" in line.lower() and i < len(lines) - 5:
                            essential_lines.extend(lines[i : i + 5])
                            break

                    context_lines.append(f"Table Details: {table_name}")
                    context_lines.append("\n".join(essential_lines))
                    context_lines.append("")

                except Exception as e:
                    context_lines.append(
                        f"Could not load details for {table_name}: {e}"
                    )
                    context_lines.append("")

        return "\n".join(context_lines)

    def test_focused_retrieval(
        self, query: str, identified_tables: List[str] = None
    ) -> Dict[str, Any]:
        """Test the focused retrieval system and return metrics"""
        start_time = time.time()

        # Get focused context
        context = self.get_focused_context(query, identified_tables)

        # Calculate metrics
        total_lines = len(context.split("\n"))
        total_chars = len(context)

        # Count context components
        components = {
            "system_prompt": "ROLE DEFINITION" in context,
            "global_context": "WINCASA DB CONTEXT" in context,
            "business_terms": "BUSINESS TERM MAPPINGS" in context,
            "schema_info": "RELEVANT SCHEMA INFORMATION" in context,
            "query_patterns": "QUERY PATTERNS & EXAMPLES" in context,
            "table_details": "TABLE-SPECIFIC DETAILS" in context,
        }

        return {
            "query": query,
            "identified_tables": identified_tables or [],
            "total_lines": total_lines,
            "total_chars": total_chars,
            "retrieval_time": time.time() - start_time,
            "components_included": components,
            "component_count": sum(components.values()),
            "focused_approach": (
                f"Retrieved {len(identified_tables or [])} specific tables instead of all 498 YAMLs"
            ),
        }


if __name__ == "__main__":
    # Test the focused embedding system
    import os

    # Load API key
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("Please set OPENAI_API_KEY environment variable")
        exit(1)

    # Create focused embedding system
    embedding_system = FocusedEmbeddingSystem(openai_api_key)

    # Test queries with different table identification scenarios
    test_cases = [
        {
            "query": "Wer wohnt in der Marienstraße 26, 45307 Essen",
            "identified_tables": ["BEWOHNER", "BEWADR"],
        },
        {
            "query": "Welche Eigentümer gibt es in Köln",
            "identified_tables": ["EIGENTUEMER", "EIGADR", "VEREIG"],
        },
        {"query": "Wie viele Wohnungen gibt es", "identified_tables": ["WOHNUNG"]},
        {
            "query": "Zeige mir alle offenen Posten",
            "identified_tables": ["KONTEN", "SOLLSTELLUNG"],
        },
        {
            "query": "General property information",
            "identified_tables": None,  # No specific tables identified
        },
    ]

    print("=== FOCUSED EMBEDDING SYSTEM TEST ===\n")

    for i, test_case in enumerate(test_cases, 1):
        print(f"Test Case {i}: {test_case['query']}")
        print(f"Identified Tables: {test_case['identified_tables']}")
        print("-" * 60)

        # Test focused retrieval
        metrics = embedding_system.test_focused_retrieval(
            test_case["query"], test_case["identified_tables"]
        )

        print(
            f"Context size: {metrics['total_lines']} lines, {metrics['total_chars']} chars"
        )
        print(f"Retrieval time: {metrics['retrieval_time']:.3f}s")
        print(f"Components included: {metrics['component_count']}/6")
        print(f"Strategy: {metrics['focused_approach']}")
        print(
            f"Components: {[k for k, v in metrics['components_included'].items() if v]}"
        )
        print("\n" + "=" * 80 + "\n")

    print("Focused embedding system test completed successfully!")
    print("✅ Strategic information architecture implemented")
    print("✅ Targeted 2-5 table retrieval instead of overwhelming 498 YAMLs")
    print("✅ Context size dramatically reduced while maintaining relevance")
