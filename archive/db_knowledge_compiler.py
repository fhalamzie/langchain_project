#!/usr/bin/env python3
"""
Database Knowledge Compiler

This module compiles all database documentation into a structured knowledge base
for enhanced LLM understanding of the database structure.
"""

import json
import logging
import os
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import yaml

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseKnowledgeCompiler:
    """Compiles database documentation into structured knowledge for LLM consumption."""

    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        self.schema_dir = os.path.join(output_dir, "schema")
        self.yaml_dir = os.path.join(output_dir, "yamls")
        self.ddl_dir = os.path.join(output_dir, "ddl")

        # Knowledge containers
        self.tables: Dict[str, Dict[str, Any]] = {}
        self.procedures: Dict[str, Dict[str, Any]] = {}
        self.relationships: List[Dict[str, str]] = []
        self.table_priorities: Dict[str, str] = {}
        self.business_glossary: Dict[str, str] = {}
        self.query_patterns: Dict[str, List[str]] = defaultdict(list)
        self.database_metadata: Dict[str, str] = {}

    def compile_knowledge(self) -> Dict[str, Any]:
        """Main method to compile all knowledge sources."""
        logger.info("Starting database knowledge compilation...")

        # Load all data sources
        self._load_schema_documentation()
        self._load_yaml_metadata()
        self._load_relationships()
        self._extract_business_glossary()
        self._analyze_table_importance()

        # Create compiled knowledge base
        knowledge_base = self._create_knowledge_base()

        # Save compiled knowledge
        self._save_compiled_knowledge(knowledge_base)

        logger.info("Knowledge compilation completed.")
        return knowledge_base

    def _load_schema_documentation(self):
        """Load and parse schema documentation from markdown files."""
        logger.info("Loading schema documentation...")

        # First, process index.md to get the complete overview and priorities
        index_path = os.path.join(self.schema_dir, "index.md")
        if os.path.exists(index_path):
            logger.info("Processing index.md - the master documentation file")
            self._parse_index_file(index_path)

        # Then process individual files
        for file in os.listdir(self.schema_dir):
            if (
                file.endswith(".md")
                and file != "index.md"
                and not file.startswith("relationship")
            ):
                filepath = os.path.join(self.schema_dir, file)
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()

                # Extract table or procedure information
                if "_proc.md" in file:
                    proc_name = file.replace("_proc.md", "")
                    self.procedures[proc_name] = self._parse_procedure_doc(
                        content, proc_name
                    )
                elif file != "index.md":  # Skip index.md as it's already processed
                    table_name = file.replace(".md", "")
                    if (
                        table_name not in self.tables
                    ):  # Only add if not already from index
                        self.tables[table_name] = self._parse_table_doc(
                            content, table_name
                        )

    def _parse_table_doc(self, content: str, table_name: str) -> Dict[str, Any]:
        """Parse table documentation from markdown."""
        table_info = {
            "name": table_name,
            "description": "",
            "business_context": "",
            "columns": [],
            "examples": [],
            "conventions": [],
        }

        # Extract priority from emoji
        if "🔴" in content:
            self.table_priorities[table_name] = "high"
        elif "🟠" in content:
            self.table_priorities[table_name] = "medium"
        elif "🟢" in content:
            self.table_priorities[table_name] = "low"

        # Extract sections using regex
        desc_match = re.search(
            r"## Beschreibung\s*\n(.*?)(?=\n##|\Z)", content, re.DOTALL
        )
        if desc_match:
            table_info["description"] = desc_match.group(1).strip()

        context_match = re.search(
            r"### Geschäftskontext\s*\n(.*?)(?=\n###|\n##|\Z)", content, re.DOTALL
        )
        if context_match:
            table_info["business_context"] = context_match.group(1).strip()

        # Extract columns
        columns_match = re.search(
            r"## Spalten\s*\n(.*?)(?=\n##|\Z)", content, re.DOTALL
        )
        if columns_match:
            column_lines = columns_match.group(1).strip().split("\n")
            for line in column_lines:
                if "|" in line and not line.startswith("|---"):
                    parts = [p.strip() for p in line.split("|")[1:-1]]
                    if len(parts) >= 3 and parts[0] != "Spalte":
                        table_info["columns"].append(
                            {
                                "name": parts[0],
                                "type": parts[1],
                                "nullable": (
                                    parts[2] == "YES" if len(parts) > 2 else True
                                ),
                            }
                        )

        return table_info

    def _parse_index_file(self, index_path: str):
        """Parse the master index.md file to extract table/procedure overviews and priorities."""
        with open(index_path, "r", encoding="utf-8") as f:
            content = f.read()

        logger.info("Parsing index.md for complete database overview...")

        # Extract table entries with priorities
        # Pattern: - 🔴 [TABLE_NAME](TABLE_NAME.md) - Description...
        table_pattern = r"- ([🔴🟠🟢])\s+\[([A-Z_]+)\]\([^)]+\)(?:\s+\([^)]*\))?\s*-\s*(.*?)(?=\n|$)"
        table_matches = re.findall(table_pattern, content, re.MULTILINE)

        for emoji, table_name, description in table_matches:
            # Determine priority from emoji
            if emoji == "🔴":
                priority = "high"
            elif emoji == "🟠":
                priority = "medium"
            elif emoji == "🟢":
                priority = "low"
            else:
                priority = "unknown"

            self.table_priorities[table_name] = priority

            # Create table entry if not exists
            if table_name not in self.tables:
                self.tables[table_name] = {
                    "name": table_name,
                    "description": description.strip(),
                    "business_context": "",
                    "columns": [],
                    "examples": [],
                    "conventions": [],
                    "source": "index.md",
                }
            else:
                # Update description if empty
                if not self.tables[table_name].get("description"):
                    self.tables[table_name]["description"] = description.strip()

        # Extract procedure entries
        # Pattern: - [PROC_NAME](PROC_NAME_proc.md) - Description...
        proc_pattern = r"- \[([A-Z_]+)\]\([^)]+_proc\.md\)\s*-\s*(.*?)(?=\n|$)"
        proc_matches = re.findall(proc_pattern, content, re.MULTILINE)

        for proc_name, description in proc_matches:
            if proc_name not in self.procedures:
                self.procedures[proc_name] = {
                    "name": proc_name,
                    "description": description.strip(),
                    "parameters": [],
                    "use_cases": [],
                    "source": "index.md",
                }

        logger.info(
            f"Extracted from index.md: {len(table_matches)} tables, {len(proc_matches)} procedures"
        )

        # Extract high-level database context
        # Look for introductory sections
        intro_match = re.search(r"# ([^#\n]+)\n+(.*?)(?=\n## |$)", content, re.DOTALL)
        if intro_match:
            db_title = intro_match.group(1).strip()
            db_intro = intro_match.group(2).strip()

            # Store as metadata for later use
            self.database_metadata = {
                "title": db_title,
                "introduction": db_intro,
                "source": "index.md",
            }

    def _parse_procedure_doc(self, content: str, proc_name: str) -> Dict[str, Any]:
        """Parse stored procedure documentation."""
        proc_info = {
            "name": proc_name,
            "description": "",
            "parameters": [],
            "use_cases": [],
        }

        # Extract description
        desc_match = re.search(
            r"## Beschreibung\s*\n(.*?)(?=\n##|\Z)", content, re.DOTALL
        )
        if desc_match:
            proc_info["description"] = desc_match.group(1).strip()

        # Extract parameters
        params_match = re.search(
            r"### Parameter\s*\n(.*?)(?=\n###|\n##|\Z)", content, re.DOTALL
        )
        if params_match:
            param_content = params_match.group(1).strip()
            param_lines = param_content.split("\n")
            for line in param_lines:
                if line.strip().startswith("-"):
                    proc_info["parameters"].append(line.strip()[1:].strip())

        return proc_info

    def _load_yaml_metadata(self):
        """Load enhanced metadata from YAML files."""
        logger.info("Loading YAML metadata...")

        for file in os.listdir(self.yaml_dir):
            if file.endswith(".yaml"):
                filepath = os.path.join(self.yaml_dir, file)
                with open(filepath, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)

                if not data:
                    continue

                table_name = data.get("table_name", file.replace(".yaml", ""))

                # Extract common queries
                if "columns" in data and data["columns"]:
                    for col in data["columns"]:
                        if col and isinstance(col, dict) and "common_queries" in col:
                            for query in col["common_queries"]:
                                self.query_patterns[table_name].append(query)

                # Merge with existing table info
                if table_name in self.tables:
                    if "business_examples" in data:
                        self.tables[table_name]["examples"] = data["business_examples"]
                    if "internal_conventions" in data:
                        self.tables[table_name]["conventions"] = data[
                            "internal_conventions"
                        ]

    def _load_relationships(self):
        """Load relationship information from compact schema JSON."""
        logger.info("Loading relationship data...")

        # Try to load from compact_schema.json first
        compact_schema_file = os.path.join(self.schema_dir, "compact_schema.json")
        if os.path.exists(compact_schema_file):
            with open(compact_schema_file, "r", encoding="utf-8") as f:
                schema_data = json.load(f)

            # Extract relationships from foreign keys
            for table_name, table_info in schema_data.get("tables", {}).items():
                for fk in table_info.get("foreign_keys", []):
                    if (
                        fk.get("column")
                        and fk.get("references_table")
                        and fk.get("references_column")
                    ):
                        self.relationships.append(
                            {
                                "from_table": table_name,
                                "from_column": fk["column"],
                                "to_table": fk["references_table"],
                                "to_column": fk["references_column"],
                            }
                        )

            logger.info(
                f"Loaded {len(self.relationships)} relationships from compact_schema.json"
            )
        else:
            # Fallback to relationship report
            rel_file = os.path.join(self.schema_dir, "relationship_report.md")
            if os.path.exists(rel_file):
                with open(rel_file, "r", encoding="utf-8") as f:
                    content = f.read()

                # Extract relationships using regex
                rel_pattern = r"(\w+)\.(\w+)\s*→\s*(\w+)\.(\w+)"
                matches = re.findall(rel_pattern, content)

                for match in matches:
                    self.relationships.append(
                        {
                            "from_table": match[0],
                            "from_column": match[1],
                            "to_table": match[2],
                            "to_column": match[3],
                        }
                    )

    def _extract_business_glossary(self):
        """Extract business terms and their meanings."""
        logger.info("Extracting business glossary...")

        # Common German property management terms
        self.business_glossary = {
            "EIGENTUEMER": "Owner of properties",
            "BEWOHNER": "Resident/Tenant",
            "OBJEKTE": "Properties/Buildings",
            "KONTEN": "Accounts",
            "VERTRAEGE": "Contracts",
            "SOLLSTELLUNG": "Debit position/Invoice",
            "ZAHLUNG": "Payment",
            "SALDO": "Balance",
            "MIETE": "Rent",
            "NEBENKOSTEN": "Ancillary costs",
            "ABRECHNUNG": "Settlement/Billing",
            "VERWALTUNG": "Management/Administration",
            "EINHEIT": "Unit (apartment/office)",
            "ZAEHLER": "Meter (utilities)",
            "WARTUNG": "Maintenance",
        }

    def _analyze_table_importance(self):
        """Analyze and rank tables by importance based on relationships and priority."""
        logger.info("Analyzing table importance...")

        # Count incoming relationships
        relationship_count = defaultdict(int)
        for rel in self.relationships:
            relationship_count[rel["to_table"]] += 1

        # Create importance scores
        importance_scores = {}
        for table in self.tables:
            score = 0

            # Priority score
            if self.table_priorities.get(table) == "high":
                score += 100
            elif self.table_priorities.get(table) == "medium":
                score += 50
            elif self.table_priorities.get(table) == "low":
                score += 10

            # Relationship score
            score += relationship_count[table] * 5

            # Core entity bonus
            core_entities = [
                "KONTEN",
                "OBJEKTE",
                "EIGENTUEMER",
                "BEWOHNER",
                "VERTRAEGE",
            ]
            if table in core_entities:
                score += 200

            importance_scores[table] = score

        # Store top 20 tables
        self.top_tables = sorted(
            importance_scores.items(), key=lambda x: x[1], reverse=True
        )[:20]

    def _create_knowledge_base(self) -> Dict[str, Any]:
        """Create the final compiled knowledge base."""
        logger.info("Creating compiled knowledge base...")

        # Create table clusters
        clusters = self._identify_table_clusters()

        # Create compact summaries
        database_overview = self._create_database_overview()
        relationship_matrix = self._create_relationship_matrix()

        knowledge_base = {
            "database_metadata": self.database_metadata,
            "database_overview": database_overview,
            "total_tables": len(self.tables),
            "total_procedures": len(self.procedures),
            "total_relationships": len(self.relationships),
            "table_priorities": {
                "high": [t for t, p in self.table_priorities.items() if p == "high"],
                "medium": [
                    t for t, p in self.table_priorities.items() if p == "medium"
                ],
                "low": [t for t, p in self.table_priorities.items() if p == "low"],
            },
            "top_20_tables": [
                {"table": t[0], "importance_score": t[1]} for t in self.top_tables
            ],
            "core_entities": {
                "KONTEN": self.tables.get("KONTEN", {}),
                "OBJEKTE": self.tables.get("OBJEKTE", {}),
                "EIGENTUEMER": self.tables.get("EIGENTUEMER", {}),
                "BEWOHNER": self.tables.get("BEWOHNER", {}),
                "VERTRAEGE": self.tables.get("VERTRAEGE", {}),
            },
            "table_clusters": clusters,
            "relationship_matrix": relationship_matrix,
            "business_glossary": self.business_glossary,
            "common_query_patterns": dict(self.query_patterns),
            "key_stored_procedures": self._get_key_procedures(),
            "all_tables": self.tables,
            "all_procedures": self.procedures,
        }

        return knowledge_base

    def _identify_table_clusters(self) -> Dict[str, List[str]]:
        """Identify logical clusters of related tables."""
        clusters = {
            "financial": [],
            "property": [],
            "person": [],
            "contract": [],
            "utility": [],
            "configuration": [],
        }

        # Simple keyword-based clustering
        for table in self.tables:
            table_upper = table.upper()

            if any(
                kw in table_upper
                for kw in ["KONTO", "SALDO", "ZAHLUNG", "SOLLSTELLUNG", "ABRECHNUNG"]
            ):
                clusters["financial"].append(table)
            elif any(
                kw in table_upper for kw in ["OBJEKT", "EINHEIT", "GEBAEUDE", "WOHNUNG"]
            ):
                clusters["property"].append(table)
            elif any(
                kw in table_upper
                for kw in ["EIGENTUEMER", "BEWOHNER", "PERSON", "KUNDE"]
            ):
                clusters["person"].append(table)
            elif any(kw in table_upper for kw in ["VERTRAG", "MIET"]):
                clusters["contract"].append(table)
            elif any(
                kw in table_upper for kw in ["ZAEHLER", "WASSER", "STROM", "HEIZUNG"]
            ):
                clusters["utility"].append(table)
            else:
                clusters["configuration"].append(table)

        # Remove empty clusters
        return {k: v for k, v in clusters.items() if v}

    def _create_database_overview(self) -> str:
        """Create a compact database overview for system prompts."""
        overview = f"""
WINCASA Property Management Database Overview:
- Total Tables: {len(self.tables)} (High Priority: {len([t for t, p in self.table_priorities.items() if p == 'high'])})
- Total Stored Procedures: {len(self.procedures)}
- Total Relationships: {len(self.relationships)}

Core Business Entities:
1. KONTEN - Central accounting system ({len([r for r in self.relationships if r['to_table'] == 'KONTEN'])} incoming relationships)
2. OBJEKTE - Properties and buildings ({len([r for r in self.relationships if r['to_table'] == 'OBJEKTE'])} incoming relationships)
3. EIGENTUEMER - Property owners
4. BEWOHNER - Residents/Tenants
5. VERTRAEGE - Contracts linking properties and people

Key Business Domains:
- Financial Management: Accounts, payments, invoices, balances
- Property Management: Buildings, units, maintenance
- People Management: Owners, tenants, contacts
- Contract Management: Leases, services, utilities
- Utility Management: Meters, consumption, billing

Common Query Patterns:
- Financial queries often join KONTEN, SOLLSTELLUNG, and ZAHLUNG tables
- Property queries typically involve OBJEKTE, EINHEITEN, and related entities
- Person queries link through EIGENTUEMER or BEWOHNER to contracts and properties

IMPORTANT ADDRESS QUERY GUIDANCE:
For BEWOHNER table address queries:
- BSTR column contains: "Straßenname Hausnummer" (e.g., "Marienstraße 26")
- BPLZORT column contains: "PLZ Ort" (e.g., "45307 Essen")
- For address searches, use LIKE patterns or exact matches
- Example: WHERE BSTR LIKE '%Marienstraße%' AND BPLZORT LIKE '%45307%'
- Always include postal code in BPLZORT search for better accuracy
"""
        return overview.strip()

    def _create_relationship_matrix(self) -> Dict[str, List[str]]:
        """Create a simplified relationship matrix for quick lookups."""
        matrix = defaultdict(list)

        for rel in self.relationships:
            key = f"{rel['from_table']}->{rel['to_table']}"
            matrix[rel["from_table"]].append(rel["to_table"])

        return dict(matrix)

    def _get_key_procedures(self) -> List[Dict[str, str]]:
        """Get the most important stored procedures."""
        key_procs = []

        # Financial procedures
        financial_procs = [
            "SALDENLISTE",
            "KONTOSALDO",
            "OFFENE_SOLLSTELLUNGEN",
            "JOURNAL",
            "OFFENE_POSTEN_LISTE",
        ]

        for proc_name in financial_procs:
            if proc_name in self.procedures:
                key_procs.append(
                    {
                        "name": proc_name,
                        "description": (
                            self.procedures[proc_name].get("description", "")[:200]
                        ),
                    }
                )

        return key_procs

    def _save_compiled_knowledge(self, knowledge_base: Dict[str, Any]):
        """Save the compiled knowledge base to files."""
        # Save as JSON
        json_path = os.path.join(self.output_dir, "compiled_knowledge_base.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(knowledge_base, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved compiled knowledge to {json_path}")

        # Save compact version for prompts
        prompt_path = os.path.join(self.output_dir, "database_context_prompt.txt")
        with open(prompt_path, "w", encoding="utf-8") as f:
            f.write(knowledge_base["database_overview"])
            f.write("\n\nTop 10 Most Important Tables:\n")
            for i, table_info in enumerate(knowledge_base["top_20_tables"][:10], 1):
                table_name = table_info["table"]
                if table_name in self.tables:
                    f.write(
                        f"{i}. {table_name}: {self.tables[table_name].get('description', 'No description')[:100]}...\n"
                    )
        logger.info(f"Saved prompt context to {prompt_path}")

    def get_compact_context(self, max_tokens: int = 2000) -> str:
        """Get a compact context string for LLM prompts."""
        # This would need token counting logic in production
        # For now, return the database overview
        return self._create_database_overview()


if __name__ == "__main__":
    compiler = DatabaseKnowledgeCompiler()
    knowledge_base = compiler.compile_knowledge()

    print(f"\nKnowledge compilation complete!")
    print(f"Total tables processed: {knowledge_base['total_tables']}")
    print(f"Total procedures processed: {knowledge_base['total_procedures']}")
    print(f"Total relationships found: {knowledge_base['total_relationships']}")
    print(f"\nTop 5 most important tables:")
    for table_info in knowledge_base["top_20_tables"][:5]:
        print(f"- {table_info['table']} (score: {table_info['importance_score']})")
