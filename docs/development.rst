Development Guide
=================

This guide covers the development workflow, conventions, and best practices for WINCASA.

Development Rules
-----------------

1. **Test First**
   
   - Write tests before implementation
   - Test against real system (no mocks)
   - Maintain 100% branch coverage
   - Minimum: one happy path + one edge case

2. **Log Everything**
   
   - Use logging module with JSON format
   - No print() in production code
   - Log all critical paths (network, DB, decisions)

3. **Commit Clean**
   
   - Only conventional commits
   - Format: ``type(scope): message``
   - Keep commits atomic and descriptive

4. **Keep Documentation Updated**
   
   - Update docstrings
   - Ensure Sphinx build runs clean
   - Document all API changes

5. **Module Size Limit**
   
   - Each .py file max ~1500 tokens
   - Modularize when approaching limit
   - Document module relationships

Development Workflow
--------------------

Session Start
~~~~~~~~~~~~~

.. code-block:: bash

   # 1. Activate environment
   source venv/bin/activate
   
   # 2. Sync project state
   ./sync-project.sh
   
   # 3. Check current tasks
   cat TASKS.md

Development Cycle
~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # 1. Select task from TASKS.md
   
   # 2. Write tests first
   python test_new_feature.py  # Should fail
   
   # 3. Implement feature
   # ... code ...
   
   # 4. Run tests
   ./run-tests.sh
   
   # 5. Update docs
   ./update-docs.sh
   
   # 6. Commit
   git add -A
   git commit -m "feat(module): implement new feature"

Session End
~~~~~~~~~~~

.. code-block:: bash

   # 1. Ensure tests pass
   ./run-tests.sh
   
   # 2. Check Sphinx build
   ./update-docs.sh
   
   # 3. Update CHANGELOG.md
   
   # 4. Push changes
   git push

Project Structure
-----------------

.. code-block:: text

   wincasa_llm/
   ├── venv/                # Virtual environment
   ├── docs/                # Sphinx documentation
   │   ├── _build/          # Generated docs
   │   ├── conf.py          # Sphinx config
   │   └── *.rst            # Documentation sources
   ├── config/              # Configuration files
   ├── knowledge_base/      # Auto-extracted mappings
   ├── logs/                # Application logs
   ├── SQL_QUERIES/         # Business SQL templates
   ├── exports/             # JSON data exports
   ├── test_data/           # Test fixtures
   └── *.py                 # Python modules

Configuration Management
------------------------

The system uses a flexible configuration cascade:

1. **ENV** (Runtime override)
2. **config.yaml** (Default config)
3. **DB-based config** (Optional via app_config table)

Example configuration loading:

.. code-block:: python

   from pydantic import BaseSettings
   
   class Settings(BaseSettings):
       db_url: str
       api_key: str
       
       class Config:
           env_prefix = ""
           env_file = ".env"
   
   settings = Settings()  # Validates required values

Testing Strategy
----------------

Test Categories
~~~~~~~~~~~~~~~

- **Unit Tests**: Individual component testing
- **Integration Tests**: Module interaction testing
- **Business Tests**: Real-world scenario validation
- **Performance Tests**: Response time benchmarks

Test Patterns
~~~~~~~~~~~~~

.. code-block:: python

   # Unit Test Pattern
   def test_optimized_search_performance():
       search = WincasaOptimizedSearch()
       result = search.search("Müller")
       assert result.response_time_ms < 5
   
   # Business Test Pattern
   def test_kaltmiete_field_mapping():
       handler = WincasaLLMHandler()
       result = handler.query_llm("Summe Kaltmiete", mode="JSON_SYSTEM")
       assert "BEWOHNER.Z1" in result.get("sql", "")

Running Tests
~~~~~~~~~~~~~

.. code-block:: bash

   # Quick tests (no LLM)
   python test_suite_quick.py
   
   # Full test suite
   python test_suite_phase2.py
   
   # Specific module
   python test_layer4.py
   
   # Performance benchmark
   python benchmark_current_modes.py

Live Documentation
------------------

For development with live documentation updates:

.. code-block:: bash

   # Start live documentation server
   ./docs-live.sh

This starts sphinx-autobuild on http://localhost:8000 with:

- Auto-reload on file changes
- Watches all .rst and .md files
- Browser refresh on updates
- Ignores temporary files

Debugging
---------

Interactive debugging tool:

.. code-block:: bash

   python debug_single_query.py

This allows you to:

- Test individual queries
- Step through routing decisions
- Inspect intermediate results
- Profile performance bottlenecks