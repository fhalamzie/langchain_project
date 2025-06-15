Architecture
============

System Architecture
-------------------

WINCASA implements a multi-layered query engine with intelligent routing:

.. code-block:: text

   WINCASA QUERY SYSTEM
   ├── Streamlit Web Interface (5 Modi)
   ├── Dual Engine Routing
   │   ├── Unified Engine (Modus 5)
   │   │   ├── Template Engine (~100ms)
   │   │   ├── Optimized Search (1-5ms)
   │   │   └── Legacy Fallback
   │   └── Legacy Handler (Modi 1-4)
   ├── Knowledge Base System
   │   └── 226 Field Mappings
   ├── Data Layer
   │   ├── Firebird Database
   │   ├── JSON Exports
   │   └── In-Memory Index
   └── Logging & Analytics

Component Details
-----------------

Query Engine
~~~~~~~~~~~~

The heart of the system is ``wincasa_query_engine.py`` which implements:

.. code-block:: python

   def route_query(query: str) -> ExecutionPath:
       """Intelligente 3-Pfad Routing Logic"""
       if simple_lookup_pattern(query):
           return OptimizedSearchPath()  # 1-5ms
       elif templatable_query(query):
           return TemplateEnginePath()   # ~100ms
       else:
           return LegacyFallbackPath()   # 500-2000ms

Intent Classification
~~~~~~~~~~~~~~~~~~~~~

Three-level classification system:

1. **Regex Patterns** (95% Confidence)
   
   - "alle mieter" → TENANT_SEARCH
   - "portfolio" → OWNER_PORTFOLIO
   - "leerstand" → VACANCY_ANALYSIS

2. **LLM Classification** (GPT-4o-mini)
   
   - Business context understanding
   - Entity extraction
   - Template availability check

3. **Intelligent Fallback**
   
   - Structured search for entity lookups
   - Legacy SQL for complex analytics

Knowledge Base
~~~~~~~~~~~~~~

Zero-hardcoding architecture:

- **Extractor**: Parses 35 SQL files automatically
- **Loader**: Runtime context injection for LLM prompts
- **Critical Mappings**: KALTMIETE = BEWOHNER.Z1

Performance Tiers
-----------------

.. list-table:: Performance Architecture
   :header-rows: 1

   * - Tier
     - Technology
     - Response Time
     - Use Case
   * - 1
     - In-Memory Index
     - 1-5ms
     - Entity lookups
   * - 2
     - SQL Templates
     - ~100ms
     - Common queries
   * - 3
     - LLM Generation
     - 500-2000ms
     - Complex analytics

Data Flow
---------

.. code-block:: text

   User Query
       ↓
   Streamlit UI
       ↓
   Mode Selection
       ↓
   ┌─────────────┐
   │ Mode 5?     │
   └─────┬───────┘
         │ Yes
         ↓
   Intent Router → Execution Path → Result
         │ No
         ↓
   Legacy Handler → LLM → SQL/JSON → Result

Security Architecture
---------------------

- **API Keys**: Separate ENV files (/home/envs/)
- **Database**: Firebird embedded mode (no server)
- **SQL Injection**: Parameter substitution
- **Query Limits**: 100k row maximum

Feature Flag System
-------------------

Gradual rollout control:

.. code-block:: python

   def should_use_unified_engine(user_id: str) -> bool:
       if not config["unified_system_enabled"]:
           return False
       
       if user_id in config["override_users"]:
           return True
       
       # Hash-based percentage assignment
       hash_value = md5(f"{user_id}{salt}").hexdigest()
       percentage = int(hash_value[:2], 16) / 255 * 100
       return percentage < config["rollout_percentage"]