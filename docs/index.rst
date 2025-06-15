.. WINCASA documentation master file

WINCASA Property Management System
==================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   overview
   architecture
   modules/index
   development
   api
   changelog

Welcome to WINCASA
==================

WINCASA is a production-ready AI-powered property management query system featuring:

- **Dual-Engine Architecture**: Legacy modes (1-4) + Unified Engine (Mode 5)
- **1-5ms Performance**: 1000x improvement through optimized search
- **Knowledge-Based SQL**: 226 auto-extracted field mappings
- **100% Test Coverage**: Comprehensive test suite

Key Features
------------

* Multi-layered query engine with intelligent routing
* In-memory search index for 588 entities
* Template-based SQL generation
* Real-time performance monitoring
* Production-ready with feature flags

Performance Metrics
-------------------

.. list-table::
   :header-rows: 1

   * - Mode
     - Description
     - Performance
   * - Optimized Search
     - In-memory entity lookup
     - 1-5ms
   * - Template Engine
     - Parametrized SQL queries
     - ~100ms
   * - Legacy Modes
     - LLM-based generation
     - 500-2000ms

Quick Start
-----------

.. code-block:: bash

   # Activate environment
   source venv/bin/activate
   
   # Sync project
   ./sync-project.sh
   
   # Run tests
   ./run-tests.sh
   
   # Start application
   ./run_streamlit.sh

Critical Business Rules
-----------------------

.. warning::
   **KALTMIETE** = BEWOHNER.Z1 (not KBETRAG!)

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

