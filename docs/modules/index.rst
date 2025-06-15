Code Modules
============

.. toctree::
   :maxdepth: 2

   core
   intelligence
   data
   knowledge
   monitoring
   testing

Module Overview
---------------

The WINCASA codebase is organized into several key modules:

Core Modules
~~~~~~~~~~~~

- **streamlit_app**: Main UI application
- **wincasa_query_engine**: Unified query routing
- **llm_handler**: Legacy LLM integration

Intelligence Layer
~~~~~~~~~~~~~~~~~~

- **wincasa_optimized_search**: 1-5ms entity search
- **unified_template_system**: SQL template management
- **sql_template_engine**: Secure SQL generation

Data Layer
~~~~~~~~~~

- **layer4_json_loader**: JSON export handling
- **data_access_layer**: Unified data interface
- **sql_executor**: Firebird database execution

Knowledge Base
~~~~~~~~~~~~~~

- **knowledge_base_loader**: Runtime field mappings
- **knowledge_extractor**: SQL analysis tools

Monitoring & Analytics
~~~~~~~~~~~~~~~~~~~~~~

- **wincasa_unified_logger**: Central logging
- **wincasa_query_logger**: Query history
- **wincasa_analytics_system**: Business metrics

Testing
~~~~~~~

- **test_suite_phase2**: Comprehensive test suite
- **test_golden_queries_kb**: Business scenario tests
- **benchmark_current_modes**: Performance benchmarks