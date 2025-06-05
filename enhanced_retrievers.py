#!/usr/bin/env python3
"""
Enhanced Multi-Stage Retrieval System

This module implements a multi-stage retrieval system that prioritizes
database schema information, relationships, and query-specific documentation.
"""

import json
import logging
import os
import re
import time
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_openai import OpenAI, OpenAIEmbeddings

from db_knowledge_compiler import DatabaseKnowledgeCompiler

# Phoenix monitoring import
from phoenix_monitoring import get_monitor
from retrievers import BaseDocumentationRetriever, FaissDocumentationRetriever

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimpleQueryMemory:
    """Simple query memory to store and retrieve historical queries."""

    def __init__(self, memory_path: str = "query_history.json"):
        self.memory_path = memory_path
        self.history = []
        self._load_history()

    def _load_history(self):
        """Load query history from file."""
        if os.path.exists(self.memory_path):
            try:
                with open(self.memory_path, "r", encoding="utf-8") as f:
                    self.history = json.load(f)
            except:
                self.history = []

    def get_similar_queries(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Get similar queries from history."""
        # Simple implementation - just return recent successful queries
        successful = [h for h in self.history if h.get("success", False)]
        return successful[-limit:] if successful else []

    def add_query(self, query_info: Dict[str, Any]):
        """Add a query to history."""
        self.history.append(query_info)
        # Keep only last 100 queries
        self.history = self.history[-100:]
        # Save to file
        try:
            with open(self.memory_path, "w", encoding="utf-8") as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except:
            pass


class EnhancedMultiStageRetriever(BaseDocumentationRetriever):
    """
    Enhanced retriever that implements multi-stage retrieval with knowledge compilation.

    Stages:
    1. Schema & Relationship Retrieval
    2. Query-Specific Documentation
    3. Historical Query Patterns
    """

    # Pydantic field definitions
    parsed_docs: List[Document] = []
    openai_api_key: str = ""
    model_name: str = "gpt-3.5-turbo"
    query_memory_path: str = "query_history.json"
    embeddings_model: Optional[OpenAIEmbeddings] = None
    base_retriever: Optional[FaissDocumentationRetriever] = None
    knowledge_base: Dict[str, Any] = {}
    query_memory: Optional[SimpleQueryMemory] = None
    schema_retriever: Optional[Any] = None
    relationship_retriever: Optional[Any] = None
    pattern_retriever: Optional[Any] = None
    schema_docs: List[Document] = []
    relationship_docs: List[Document] = []
    procedure_docs: List[Document] = []
    example_docs: List[Document] = []
    schema_store: Optional[FAISS] = None
    relationship_store: Optional[FAISS] = None
    pattern_store: Optional[FAISS] = None
    procedure_store: Optional[FAISS] = None
    example_store: Optional[FAISS] = None

    def __init__(
        self,
        parsed_docs: List[Document],
        openai_api_key: str,
        model_name: str = "gpt-3.5-turbo",
        query_memory_path: str = "query_history.json",
        **kwargs,
    ):
        """Initialize the enhanced multi-stage retriever."""
        super().__init__(**kwargs)

        # Store the parsed documents
        self.parsed_docs = parsed_docs

        self.openai_api_key = openai_api_key
        self.model_name = model_name

        # Initialize embeddings model
        self.embeddings_model = OpenAIEmbeddings(
            model="text-embedding-3-large",
            openai_api_key=openai_api_key,
            dimensions=3072,  # Maximale Dimensionen für bessere Leistung
        )

        # Initialize base retriever
        self.base_retriever = FaissDocumentationRetriever(
            documents=self.parsed_docs, embeddings_model=self.embeddings_model
        )

        # Load compiled knowledge base
        self.knowledge_base = self._load_knowledge_base()

        # Initialize query memory
        self.query_memory = SimpleQueryMemory(query_memory_path)

        # Create specialized retrievers for each stage
        self._initialize_specialized_retrievers()

    def _load_knowledge_base(self) -> Dict[str, Any]:
        """Load the compiled knowledge base."""
        kb_path = os.path.join("output", "compiled_knowledge_base.json")
        if os.path.exists(kb_path):
            with open(kb_path, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            logger.warning("Compiled knowledge base not found. Running compiler...")
            compiler = DatabaseKnowledgeCompiler()
            return compiler.compile_knowledge()

    def _initialize_specialized_retrievers(self):
        """Initialize specialized retrievers for different document types."""
        # Create separate document collections by type
        self.schema_docs = []
        self.relationship_docs = []
        self.procedure_docs = []
        self.example_docs = []

        # Categorize documents
        for doc in self.parsed_docs:
            content_lower = doc.page_content.lower()
            metadata = doc.metadata

            # Detect document type
            if "foreign key" in content_lower or "references" in content_lower:
                self.relationship_docs.append(doc)
            elif "_proc" in metadata.get("source", ""):
                self.procedure_docs.append(doc)
            elif "business_examples" in content_lower or "beispiel" in content_lower:
                self.example_docs.append(doc)
            else:
                self.schema_docs.append(doc)

        # Create enhanced schema documents from knowledge base
        self._create_enhanced_schema_docs()

        # Initialize FAISS stores for each category
        embeddings = OpenAIEmbeddings(openai_api_key=self.openai_api_key)

        if self.schema_docs:
            self.schema_store = FAISS.from_documents(self.schema_docs, embeddings)
        if self.relationship_docs:
            self.relationship_store = FAISS.from_documents(
                self.relationship_docs, embeddings
            )
        if self.procedure_docs:
            self.procedure_store = FAISS.from_documents(self.procedure_docs, embeddings)
        if self.example_docs:
            self.example_store = FAISS.from_documents(self.example_docs, embeddings)

    def _create_enhanced_schema_docs(self):
        """Create enhanced schema documents from the compiled knowledge base."""
        # Add database overview as a high-priority document
        overview_doc = Document(
            page_content=self.knowledge_base.get("database_overview", ""),
            metadata={
                "source": "compiled_knowledge",
                "type": "overview",
                "priority": 10,
            },
        )
        self.schema_docs.insert(0, overview_doc)

        # Add relationship matrix as searchable documents
        rel_matrix = self.knowledge_base.get("relationship_matrix", {})
        for from_table, to_tables in rel_matrix.items():
            rel_content = (
                f"Table {from_table} has relationships to: {', '.join(to_tables)}"
            )
            rel_doc = Document(
                page_content=rel_content,
                metadata={
                    "source": "relationship_matrix",
                    "type": "relationship",
                    "priority": 8,
                },
            )
            self.relationship_docs.append(rel_doc)

        # Add top tables with their importance
        for table_info in self.knowledge_base.get("top_20_tables", [])[:10]:
            table_name = table_info["table"]
            if table_name in self.knowledge_base.get("core_entities", {}):
                entity_info = self.knowledge_base["core_entities"][table_name]
                enhanced_content = f"""
Table: {table_name} (Importance Score: {table_info['importance_score']})
Description: {entity_info.get('description', '')}
Business Context: {entity_info.get('business_context', '')}
Key Columns: {', '.join([col['name'] for col in entity_info.get('columns', [])[:5]])}
"""
                enhanced_doc = Document(
                    page_content=enhanced_content,
                    metadata={
                        "source": "enhanced_schema",
                        "table": table_name,
                        "priority": 9,
                    },
                )
                self.schema_docs.insert(1, enhanced_doc)

    def get_relevant_documents(self, query: str) -> List[Document]:
        """
        Retrieve relevant documents using multi-stage approach.

        Args:
            query: The natural language query

        Returns:
            List of relevant documents prioritized by stage
        """
        logger.info(f"Enhanced multi-stage retrieval for query: {query}")

        # Initialize Phoenix monitoring
        monitor = get_monitor(enable_ui=False)
        start_time = time.time()

        all_docs = []
        relevance_scores = []

        try:
            # Stage 1: Schema & Relationship Retrieval
            stage1_start = time.time()
            stage1_docs = self._stage1_schema_retrieval(query)
            all_docs.extend(stage1_docs)
            logger.info(
                f"Stage 1 retrieved {len(stage1_docs)} docs in {time.time() - stage1_start:.2f}s"
            )

            # Stage 2: Query-Specific Documentation
            stage2_start = time.time()
            stage2_docs = self._stage2_query_specific(query)
            all_docs.extend(stage2_docs)
            logger.info(
                f"Stage 2 retrieved {len(stage2_docs)} docs in {time.time() - stage2_start:.2f}s"
            )

            # Stage 3: Historical Query Patterns
            stage3_start = time.time()
            stage3_docs = self._stage3_historical_patterns(query)
            all_docs.extend(stage3_docs)
            logger.info(
                f"Stage 3 retrieved {len(stage3_docs)} docs in {time.time() - stage3_start:.2f}s"
            )

            # Remove duplicates while preserving order
            seen = set()
            unique_docs = []
            for doc in all_docs:
                doc_id = f"{doc.metadata.get('source', '')}:{doc.page_content[:100]}"
                if doc_id not in seen:
                    seen.add(doc_id)
                    unique_docs.append(doc)
                    # Collect relevance scores
                    score = doc.metadata.get(
                        "score", 0.8
                    )  # Default score if not available
                    relevance_scores.append(float(score))

            # Limit total documents
            final_docs = unique_docs[:15]

            # Track successful retrieval
            duration = time.time() - start_time
            if monitor:  # Check if monitor exists
                monitor.track_retrieval(
                    retrieval_mode="enhanced",
                    query=query,
                    documents_retrieved=len(final_docs),
                    relevance_scores=relevance_scores[
                        :15
                    ],  # Match the number of returned docs
                    duration=duration,
                    success=True,
                )

            logger.info(
                f"Enhanced retrieval completed: {len(final_docs)} docs in {duration:.2f}s"
            )
            return final_docs

        except Exception as e:
            # Track failed retrieval
            duration = time.time() - start_time
            if monitor:  # Check if monitor exists
                monitor.track_retrieval(
                    retrieval_mode="enhanced",
                    query=query,
                    documents_retrieved=0,
                    relevance_scores=[],
                    duration=duration,
                    success=False,
                )
            logger.error(f"Enhanced retrieval failed: {e}")
            raise

    def _stage1_schema_retrieval(self, query: str) -> List[Document]:
        """Stage 1: Prioritize schema and relationship information."""
        docs = []

        # Always include database overview
        overview_doc = Document(
            page_content=self.knowledge_base.get("database_overview", ""),
            metadata={"source": "overview", "stage": 1, "priority": 10},
        )
        docs.append(overview_doc)

        # Identify mentioned tables
        mentioned_tables = self._extract_table_names(query)

        # Get schema for mentioned tables
        if mentioned_tables and self.schema_store:
            for table in mentioned_tables:
                table_query = f"table {table} columns description"
                schema_results = self.schema_store.similarity_search(table_query, k=2)
                docs.extend(schema_results)

        # Get relationships for mentioned tables
        if mentioned_tables and self.relationship_store:
            for table in mentioned_tables:
                rel_query = f"{table} foreign key references relationship"
                rel_results = self.relationship_store.similarity_search(rel_query, k=2)
                docs.extend(rel_results)

        # If no specific tables mentioned, get general schema info
        if not mentioned_tables and self.schema_store:
            general_results = self.schema_store.similarity_search(query, k=3)
            docs.extend(general_results)

        return docs[:5]  # Limit stage 1 results

    def _stage2_query_specific(self, query: str) -> List[Document]:
        """Stage 2: Get query-specific documentation."""
        docs = []

        # Detect query intent
        query_lower = query.lower()

        # Financial queries
        if any(
            term in query_lower
            for term in ["zahlung", "payment", "saldo", "balance", "konto", "account"]
        ):
            if self.procedure_docs:
                proc_store = FAISS.from_documents(
                    self.procedure_docs,
                    OpenAIEmbeddings(openai_api_key=self.openai_api_key),
                )
                financial_procs = proc_store.similarity_search(
                    "SALDO ZAHLUNG KONTO financial", k=3
                )
                docs.extend(financial_procs)

        # Property queries
        elif any(
            term in query_lower
            for term in [
                "objekt",
                "property",
                "wohnung",
                "apartment",
                "gebäude",
                "building",
            ]
        ):
            if self.schema_store:
                property_docs = self.schema_store.similarity_search(
                    "OBJEKTE WOHNUNG property management", k=3
                )
                docs.extend(property_docs)

        # Person queries
        elif any(
            term in query_lower
            for term in ["eigentümer", "owner", "bewohner", "tenant", "mieter"]
        ):
            if self.schema_store:
                person_docs = self.schema_store.similarity_search(
                    "EIGENTUEMER BEWOHNER person contact", k=3
                )
                docs.extend(person_docs)

        # Get examples if available
        if self.example_docs:
            example_store = FAISS.from_documents(
                self.example_docs, OpenAIEmbeddings(openai_api_key=self.openai_api_key)
            )
            examples = example_store.similarity_search(query, k=2)
            docs.extend(examples)

        return docs[:5]  # Limit stage 2 results

    def _stage3_historical_patterns(self, query: str) -> List[Document]:
        """Stage 3: Retrieve similar historical queries and their patterns."""
        docs = []

        # Get similar queries from history
        similar_queries = self.query_memory.get_similar_queries(query, limit=3)

        for hist_query in similar_queries:
            if hist_query.get("sql_query") and hist_query.get("success"):
                # Create a document from successful historical query
                pattern_content = f"""
Historical Query Pattern:
Question: {hist_query.get('natural_language_query', '')}
SQL: {hist_query.get('sql_query', '')}
Tables Used: {', '.join(hist_query.get('tables_used', []))}
"""
                pattern_doc = Document(
                    page_content=pattern_content,
                    metadata={"source": "query_history", "stage": 3, "priority": 5},
                )
                docs.append(pattern_doc)

        # Add common query patterns from knowledge base
        query_patterns = self.knowledge_base.get("common_query_patterns", {})
        relevant_patterns = []

        for table, patterns in query_patterns.items():
            if any(table.lower() in query.lower() for _ in [table]):
                for pattern in patterns[:2]:  # Limit patterns per table
                    pattern_doc = Document(
                        page_content=f"Common query pattern for {table}: {pattern}",
                        metadata={
                            "source": "query_patterns",
                            "table": table,
                            "stage": 3,
                        },
                    )
                    relevant_patterns.append(pattern_doc)

        docs.extend(relevant_patterns[:3])

        return docs[:5]  # Limit stage 3 results

    def _get_relevant_documents(self, query: str) -> List[Document]:
        """Required method for BaseRetriever interface."""
        return self.get_relevant_documents(query)

    def _extract_table_names(self, query: str) -> List[str]:
        """Extract potential table names from the query."""
        mentioned_tables = []
        query_upper = query.upper()

        # Check against all known tables
        all_tables = list(self.knowledge_base.get("core_entities", {}).keys())
        all_tables.extend(
            [t["table"] for t in self.knowledge_base.get("top_20_tables", [])]
        )

        for table in all_tables:
            if table.upper() in query_upper:
                mentioned_tables.append(table)

        # Also check for German business terms that map to tables
        term_mapping = {
            "EIGENTÜMER": "EIGENTUEMER",
            "MIETER": "BEWOHNER",
            "WOHNUNG": "WOHNUNG",
            "OBJEKT": "OBJEKTE",
            "KONTO": "KONTEN",
            "ZAHLUNG": "ZAHLUNG",
            "VERTRAG": "VERTRAEGE",
        }

        for term, table in term_mapping.items():
            if term in query_upper:
                mentioned_tables.append(table)

        return list(set(mentioned_tables))

    def get_context_with_compression(
        self, query: str, llm: Optional[Any] = None
    ) -> List[Document]:
        """
        Get relevant documents with LLM-based compression.

        This method uses an LLM to extract only the most relevant parts
        of the retrieved documents.
        """
        if not llm:
            llm = OpenAI(temperature=0, openai_api_key=self.openai_api_key)

        # Get base documents
        docs = self.get_relevant_documents(query)

        # Create compression retriever
        compressor = LLMChainExtractor.from_llm(llm)
        compression_retriever = ContextualCompressionRetriever(
            base_compressor=compressor, base_retriever=self
        )

        # Return compressed documents
        return compression_retriever.get_relevant_documents(query)


class EnhancedFaissRetriever(FaissDocumentationRetriever):
    """Enhanced FAISS retriever with knowledge base integration."""

    def __init__(self, parsed_docs: List[Document], openai_api_key: str):
        """Initialize enhanced FAISS retriever."""
        # Work with a copy to avoid modifying the original
        enhanced_docs = parsed_docs.copy()

        # Load knowledge base and enhance documents
        kb_path = os.path.join("output", "compiled_knowledge_base.json")
        if os.path.exists(kb_path):
            with open(kb_path, "r", encoding="utf-8") as f:
                knowledge_base = json.load(f)

            # Add overview document at the beginning
            overview_doc = Document(
                page_content=knowledge_base.get("database_overview", ""),
                metadata={"source": "database_overview", "priority": 10},
            )
            enhanced_docs.insert(0, overview_doc)

            # Add business glossary as a document
            glossary_content = "Business Terms Glossary:\n"
            for term, meaning in knowledge_base.get("business_glossary", {}).items():
                glossary_content += f"{term}: {meaning}\n"

            glossary_doc = Document(
                page_content=glossary_content,
                metadata={"source": "business_glossary", "priority": 9},
            )
            enhanced_docs.insert(1, glossary_doc)

        # Store the enhanced documents for later use
        self._enhanced_docs = enhanced_docs

        # Initialize parent class with enhanced documents
        embeddings_model = OpenAIEmbeddings(openai_api_key=openai_api_key)
        super().__init__(documents=enhanced_docs, embeddings_model=embeddings_model)

    def _get_relevant_documents(self, query: str) -> List[Document]:
        """Override to always include database overview."""
        # Initialize Phoenix monitoring
        monitor = get_monitor(enable_ui=False)
        start_time = time.time()

        try:
            # Get base results
            docs = super()._get_relevant_documents(query)

            # Ensure overview is included if not already
            has_overview = any(
                d.metadata.get("source") == "database_overview" for d in docs
            )
            if not has_overview and hasattr(self, "_enhanced_docs"):
                overview_doc = next(
                    (
                        d
                        for d in self._enhanced_docs
                        if d.metadata.get("source") == "database_overview"
                    ),
                    None,
                )
                if overview_doc:
                    docs.insert(0, overview_doc)

            # Collect relevance scores
            relevance_scores = []
            for doc in docs:
                score = doc.metadata.get("score", 0.8)
                relevance_scores.append(float(score))

            # Track successful retrieval
            duration = time.time() - start_time
            if monitor:  # Check if monitor exists
                monitor.track_retrieval(
                    retrieval_mode="faiss",
                    query=query,
                    documents_retrieved=len(docs),
                    relevance_scores=relevance_scores,
                    duration=duration,
                    success=True,
                )

            logger.info(
                f"FAISS retrieval completed: {len(docs)} docs in {duration:.2f}s"
            )
            return docs

        except Exception as e:
            # Track failed retrieval
            duration = time.time() - start_time
            if monitor:  # Check if monitor exists
                monitor.track_retrieval(
                    retrieval_mode="faiss",
                    query=query,
                    documents_retrieved=0,
                    relevance_scores=[],
                    duration=duration,
                    success=False,
                )
            logger.error(f"FAISS retrieval failed: {e}")
            raise


if __name__ == "__main__":
    # Test the enhanced retriever
    import sys

    sys.path.append(os.path.dirname(os.path.abspath(__file__)))

    # Load sample documents
    from firebird_sql_agent import FirebirdDocumentedSQLAgent

    agent = FirebirdDocumentedSQLAgent(
        db_connection_string="firebird+fdb://sysdba:masterkey@localhost:3050//home/projects/langchain_project/WINCASA2022.FDB",
        llm_provider="openai",
        retrieval_mode="faiss",
    )

    # Create enhanced retriever
    enhanced_retriever = EnhancedMultiStageRetriever(
        parsed_docs=agent.parsed_docs, openai_api_key=agent.openai_api_key
    )

    # Test queries
    test_queries = [
        "Show me all properties with their owners",
        "What is the current balance for account 1000?",
        "List all tenants who haven't paid rent",
    ]

    for query in test_queries:
        print(f"\nQuery: {query}")
        print("-" * 50)
        docs = enhanced_retriever.get_relevant_documents(query)
        print(f"Retrieved {len(docs)} documents")
        for i, doc in enumerate(docs[:3]):
            print(f"\nDoc {i+1} (Stage: {doc.metadata.get('stage', 'base')}):")
            print(doc.page_content[:200] + "...")
