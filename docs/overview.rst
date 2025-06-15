Overview
========

WINCASA is an advanced property management query system that combines traditional database queries with modern AI capabilities.

System Philosophy
-----------------

The system follows several key principles:

1. **Self-Updating Stack**: Automatic synchronization between database schema, code generation, and documentation
2. **Zero-Mock Testing**: All tests run against the real system, ensuring production reliability
3. **Performance First**: 1000x improvement through intelligent query routing
4. **Knowledge-Based**: Automatic extraction of business rules from existing SQL queries

Architecture Highlights
-----------------------

Dual-Engine System
~~~~~~~~~~~~~~~~~~

The system operates with two distinct engines:

- **Legacy Engine (Modes 1-4)**: Direct LLM-based query generation
- **Unified Engine (Mode 5)**: Intelligent routing between three execution paths

3-Path Routing
~~~~~~~~~~~~~~

The Unified Engine intelligently routes queries through:

1. **Optimized Search** (1-5ms): In-memory index for entity lookups
2. **Template Engine** (~100ms): Parametrized SQL for common queries
3. **Legacy Fallback** (500-2000ms): Full LLM generation for complex queries

Knowledge Base System
---------------------

The Knowledge Base automatically extracts and maintains:

- 226 field mappings from existing SQL queries
- Join relationships between 30 tables
- Business vocabulary translations (German → SQL)
- Critical mappings like KALTMIETE = BEWOHNER.Z1

Data Sources
------------

The system works with multiple data sources:

- **Firebird Database**: 126 tables with production data
- **JSON Exports**: 35 pre-computed query results (229k rows)
- **In-Memory Index**: 588 entities for ultra-fast search

Development Workflow
--------------------

.. code-block:: bash

   # 1. Update database schema
   alembic upgrade head
   
   # 2. Sync all artifacts
   ./sync-project.sh
   
   # 3. Run tests
   ./run-tests.sh
   
   # 4. Start development server
   ./run_streamlit.sh

The sync-project.sh script ensures all layers stay synchronized:

- Database schema → schema.json
- schema.json → TypeScript types, SQLAlchemy models, Test factories
- All changes validated through 100% test coverage