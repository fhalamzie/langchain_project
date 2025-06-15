API Reference
=============

This section provides detailed API documentation for WINCASA modules.

Web Interface
-------------

Streamlit Endpoint
~~~~~~~~~~~~~~~~~~

- **URL**: http://localhost:8667
- **Module**: streamlit_app.py
- **Entry**: WincasaStreamlitApp.execute_query()

Request Format
~~~~~~~~~~~~~~

.. code-block:: python

   {
     "query": "Zeige alle Mieter",
     "modes": ["JSON_VANILLA", "UNIFIED"],
     "session_id": "sess_abc123"
   }

Response Format
~~~~~~~~~~~~~~~

.. code-block:: python

   {
     "results": {
       "mode_name": {
         "data": [...],
         "response_time_ms": 3.1,
         "success": true,
         "source": "optimized_search"
       }
     },
     "query_metadata": {
       "timestamp": "2025-06-15T10:30:45Z"
     }
   }

Core APIs
---------

Unified Engine
~~~~~~~~~~~~~~

.. automodule:: wincasa_query_engine
   :members:
   :undoc-members:
   :show-inheritance:

Legacy Handler
~~~~~~~~~~~~~~

.. automodule:: llm_handler
   :members:
   :undoc-members:
   :show-inheritance:

Optimized Search
~~~~~~~~~~~~~~~~

.. automodule:: wincasa_optimized_search
   :members:
   :undoc-members:
   :show-inheritance:

Knowledge APIs
--------------

Knowledge Extractor
~~~~~~~~~~~~~~~~~~~

.. automodule:: knowledge_extractor
   :members:
   :undoc-members:
   :show-inheritance:

Knowledge Loader
~~~~~~~~~~~~~~~~

.. automodule:: knowledge_base_loader
   :members:
   :undoc-members:
   :show-inheritance:

Data Access APIs
----------------

Data Access Layer
~~~~~~~~~~~~~~~~~

.. automodule:: data_access_layer
   :members:
   :undoc-members:
   :show-inheritance:

SQL Executor
~~~~~~~~~~~~

.. automodule:: sql_executor
   :members:
   :undoc-members:
   :show-inheritance:

Error Handling
--------------

Error Codes
~~~~~~~~~~~

.. code-block:: python

   ERROR_CODES = {
     "QUERY_EMPTY": "Empty query",
     "MODE_INVALID": "Invalid mode",
     "DB_CONNECTION_FAILED": "DB error",
     "TEMPLATE_NOT_FOUND": "No template",
     "SEARCH_INDEX_ERROR": "Index error",
     "KNOWLEDGE_BASE_ERROR": "KB error",
     "LLM_API_ERROR": "LLM error",
     "TIMEOUT_ERROR": "Timeout"
   }

Response Structure
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   {
     "success": bool,
     "data": {...} | None,
     "error": {
       "code": "ERROR_CODE",
       "message": "Description"
     } | None,
     "metadata": {
       "response_time_ms": float,
       "timestamp": str
     }
   }

Performance Targets
-------------------

Response Times
~~~~~~~~~~~~~~

- **optimized_search**: 1-5ms
- **template_engine**: ~100ms
- **json_vanilla**: ~300ms
- **sql_vanilla**: ~500ms
- **json_system**: ~1500ms
- **sql_system**: ~2000ms
- **legacy_fallback**: 500-2000ms

Concurrent Limits
~~~~~~~~~~~~~~~~~

- **Max Users**: 10-50 (Streamlit limitation)
- **Memory**: ~200MB (index + knowledge base)
- **Database**: Single embedded Firebird instance