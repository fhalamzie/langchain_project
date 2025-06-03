import os
# Setzen der Umgebungsvariable für den Firebird-Client-Pfad
# Dies sollte vor dem Import von fdb oder sqlalchemy erfolgen, falls diese den Pfad beim Import prüfen.
# Da fdb wahrscheinlich erst bei der Initialisierung von SQLDatabase geladen wird, ist es hier sicher.
lib_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lib'))
os.environ['FIREBIRD_LIBRARY_PATH'] = os.path.join(lib_path, 'libfbclient.so')
print(f"FIREBIRD_LIBRARY_PATH set to: {os.environ['FIREBIRD_LIBRARY_PATH']}")

# import fdb # FDB früh importieren - Wird jetzt später importiert, nach Setzen der Env-Vars

# Die manuelle Registrierung wird entfernt, da sqlalchemy-firebird installiert ist
# und seine Entry Points automatisch von SQLAlchemy erkannt werden sollten.
# try:
#     from sqlalchemy.dialects import registry
#     registry.register("firebird.fdb", "fdb.sqlalchemy_dialect", "FBDialect")
#     print("fdb dialect registered successfully for SQLAlchemy.")
# except Exception as e:
#     print(f"Warning: Could not register fdb dialect: {e}")
import glob
import yaml
from typing import List, Dict, Any, Optional, Union # Added Optional and Union
from pathlib import Path # Hinzufügen für Pfadoperationen
from unittest.mock import MagicMock # Moved import to top level
from langchain_core.documents import Document
from langchain_core.callbacks.base import BaseCallbackHandler
from langchain_core.agents import AgentAction, AgentFinish
from langchain_openai import OpenAIEmbeddings
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits.sql.base import create_sql_agent # Updated import
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit # Updated import
import sqlite3
# import fdb # Wird jetzt innerhalb der Creator-Funktion oder bei Bedarf importiert
from sqlalchemy import create_engine, event, text # event für Ping, text für SQLAlchemy 2.0
from sqlalchemy.engine.url import make_url # Zum Parsen des Connection Strings
from sqlalchemy.pool import StaticPool, NullPool # NullPool importieren

# --- Globale Datenbankinitialisierung (Experiment) ---
DB_CONNECTION_STRING_GLOBAL = "firebird+fdb://sysdba:masterkey@//home/projects/langchain_project/WINCASA2022.FDB"
GLOBAL_ENGINE = None
GLOBAL_DB = None

def create_global_fdb_connection():
    import fdb # Import hier, um sicherzustellen, dass es nach den Env-Vars geschieht
    url_info = make_url(DB_CONNECTION_STRING_GLOBAL)
    db_path_for_creator = str(url_info.database)
    if db_path_for_creator.startswith("//"):
        db_path_for_creator = db_path_for_creator[1:]
    
    print(f"Global Creator: Connecting to DSN: {db_path_for_creator}, User: {url_info.username or 'SYSDBA'}")
    # Umgebungsvariablen hier explizit setzen, um sicherzugehen, dass sie vor fdb.connect aktiv sind
    # Dies ist redundant, wenn sie bereits global gesetzt wurden, schadet aber nicht.
    fb_temp_dir_g = Path("./fb_temp_global_init").absolute()
    if not fb_temp_dir_g.exists():
        fb_temp_dir_g.mkdir(exist_ok=True, parents=True)
    os.environ["FIREBIRD_TMP"] = str(fb_temp_dir_g)
    os.environ["FIREBIRD_TEMP"] = str(fb_temp_dir_g)
    os.environ["FB_TMPDIR"] = str(fb_temp_dir_g)
    os.environ["FIREBIRD_LOCK"] = str(fb_temp_dir_g)
    os.environ["FB_HOME"] = str(fb_temp_dir_g)
    os.environ["FIREBIRD_HOME"] = str(fb_temp_dir_g)
    print(f"Global Creator: FIREBIRD_TMP set to {fb_temp_dir_g}")

    return fdb.connect(
        dsn=db_path_for_creator,
        user=url_info.username or "SYSDBA",
        password=url_info.password or "masterkey",
        charset="WIN1252"
    )

try:
    print("Attempting global engine and SQLDatabase initialization...")
    GLOBAL_ENGINE = create_engine(
        "firebird+fdb://",
        creator=create_global_fdb_connection,
        poolclass=NullPool, # Weiterhin NullPool verwenden
        echo=False # True für Debugging des Engine-Verhaltens
    )
    # Der explizite Test mit GLOBAL_ENGINE.connect() wird entfernt,
    # da die SQLDatabase-Initialisierung die Verbindung testen wird.
    # with GLOBAL_ENGINE.connect() as conn_g_test:
    #     print("✓ Global engine connection test successful.")
    #     res_g = conn_g_test.execute(text("SELECT rdb$relation_id FROM rdb$database"))
    #     print(f"✓ Global engine query successful: {res_g.fetchone()}")

    GLOBAL_DB = SQLDatabase(GLOBAL_ENGINE)
    print(f"✓ Global SQLDatabase initialized. Usable tables: {GLOBAL_DB.get_usable_table_names()}")
except Exception as e_global_init:
    print(f"✗ Error during global database initialization: {e_global_init}")
    import traceback
    traceback.print_exc()
    GLOBAL_ENGINE = None
    GLOBAL_DB = None
# --- Ende Globale Datenbankinitialisierung ---


# Assuming retrievers.py is in the same directory or accessible in PYTHONPATH
from retrievers import FaissDocumentationRetriever, BaseDocumentationRetriever, Neo4jDocumentationRetriever

# Monkey-Patch für sqlalchemy-firebird Dialekt
# Dieses Patch behebt ein Problem, bei dem der Dialekt versucht, 'WIN1252' (eine Kollation)
# als Länge für VARCHAR-Felder zu interpretieren, was zu einem ValueError führt.
try:
    from sqlalchemy_firebird.base import FBTypeCompiler # Importiere den spezifischen Typ-Compiler
    import sqlalchemy.sql.sqltypes as sqltypes

    _original_render_string_type = FBTypeCompiler._render_string_type

    def _patched_render_string_type(self, type_, *args, **kwargs): # Akzeptiere *args und **kwargs
        # Diese gepatchte Methode wird anstelle der Originalmethode im FBTypeCompiler aufgerufen.
        
        if not isinstance(type_, (sqltypes.VARCHAR, sqltypes.CHAR)):
            # Für andere Typen das Originalverhalten aufrufen und alle Argumente weitergeben
            return _original_render_string_type(self, type_, *args, **kwargs)

        # Behandlung für VARCHAR und CHAR
        base_rendering = "VARCHAR" if isinstance(type_, sqltypes.VARCHAR) else "CHAR"
        
        length_suffix = ""
        if getattr(type_, 'length', None) is not None:
            try:
                length_val = int(type_.length)
                if length_val > 0: # Nur positive Längen hinzufügen
                    length_suffix = f"({length_val})"
            except ValueError:
                # Ignoriere 'WIN1252' oder andere nicht-numerische Längen für den Suffix
                print(f"MonkeyPatch (FBTypeCompiler._render_string_type): Konnte Länge '{type_.length}' für Typ {type_} nicht in int umwandeln. Lasse Suffix weg.")
                pass # length_suffix bleibt ""
        
        # Kollationsteil (falls vorhanden und relevant, hier nicht direkt behandelt,
        # da das Problem die Längenkonvertierung ist)
        # collation = getattr(type_, 'collation', None)
        # if collation:
        #     ...

        return base_rendering + length_suffix

    FBTypeCompiler._render_string_type = _patched_render_string_type
    print("MonkeyPatch für FBTypeCompiler._render_string_type angewendet.")

except ImportError:
    print("Konnte sqlalchemy_firebird.base.FBTypeCompiler nicht für Monkey-Patch importieren.")
except AttributeError:
    print("Konnte FBTypeCompiler._render_string_type nicht für Monkey-Patch finden/überschreiben.")
except Exception as e_patch:
    print(f"Fehler beim Anwenden des Monkey-Patches: {e_patch}")


class SQLCaptureCallbackHandler(BaseCallbackHandler):
    """A callback handler to capture SQL queries and other agent actions."""
    def __init__(self):
        super().__init__()
        self.sql_query: Optional[str] = None
        self.full_log: List[Dict[str, Any]] = [] # To store actions and observations
        self._current_action: Optional[AgentAction] = None

    def on_agent_action(self, action: AgentAction, **kwargs: Any) -> Any:
        """Called when the agent is about to perform an action."""
        print(f"Callback: Agent action: {action.tool}, Input: {action.tool_input}")
        self._current_action = action # Store action to associate with observation later
        
        # Capture SQL query specifically if it's a sql_db_query action
        if action.tool == "sql_db_query":
            if isinstance(action.tool_input, str):
                self.sql_query = action.tool_input
            elif isinstance(action.tool_input, dict) and 'query' in action.tool_input:
                self.sql_query = action.tool_input['query']
            else:
                # Handle cases where tool_input might be a different dict structure
                # For example, some agents might pass {'sql_query': 'SELECT ...'}
                # This part might need adjustment based on actual tool_input format if not str or {'query': ...}
                print(f"Callback: sql_db_query tool_input is not a string or a dict with 'query' key: {action.tool_input}")
                self.sql_query = str(action.tool_input) # Fallback to string representation

            print(f"Callback captured SQL: {self.sql_query}")

    def on_tool_end(self, output: str, name: str, **kwargs: Any) -> Any:
        """Called when a tool has finished running."""
        print(f"Callback: Tool '{name}' ended. Output: {str(output)[:200]}...")
        if self._current_action:
            self.full_log.append({
                "action": self._current_action.dict(), # Convert AgentAction to dict for easier storage/access
                "observation": output
            })
            self._current_action = None # Reset for the next action

    def on_tool_error(self, error: Union[Exception, KeyboardInterrupt], name: str, **kwargs: Any) -> Any:
        """Called when a tool errors."""
        print(f"Callback: Tool '{name}' errored: {error}")
        if self._current_action:
            self.full_log.append({
                "action": self._current_action.dict(),
                "error": str(error)
            })
            self._current_action = None

    def clear_log(self):
        """Clears all captured data for the next run."""
        self.sql_query = None
        self.full_log = []
        self._current_action = None

class FirebirdDocumentedSQLAgent:
    """
    A SQL agent for Firebird databases, augmented with documentation retrieval
    capabilities using either FAISS or Neo4j.
    """

    def __init__(self, db_connection_string: str, llm: Any, retrieval_mode: str = 'faiss', neo4j_config: Dict = None):
        """
        Initializes the FirebirdDocumentedSQLAgent.

        Args:
            db_connection_string: SQLAlchemy connection string for Firebird.
            llm: The language model instance (e.g., from Langchain).
            retrieval_mode: 'faiss' or 'neo4j'. Defaults to 'faiss'.
            neo4j_config: Configuration dictionary for Neo4j if mode is 'neo4j'.
        """
        self.db_connection_string = db_connection_string
        self.llm = llm
        self.retrieval_mode = retrieval_mode
        self.neo4j_config = neo4j_config

        # Firebird Umgebungsvariablen setzen (adaptiert von generate_yaml_ui.py)
        # Dies sollte vor jeglicher fdb-Initialisierung geschehen.
        fb_temp_dir = Path("./fb_temp").absolute()
        if not fb_temp_dir.exists():
            fb_temp_dir.mkdir(exist_ok=True, parents=True) # parents=True hinzugefügt
        
        print(f"FirebirdDocumentedSQLAgent: Setting Firebird environment variables. Temp dir: {fb_temp_dir}")
        os.environ["FIREBIRD_TMP"] = str(fb_temp_dir)
        os.environ["FIREBIRD_TEMP"] = str(fb_temp_dir)
        os.environ["FIREBIRD_TMPDIR"] = str(fb_temp_dir)
        os.environ["FB_TMPDIR"] = str(fb_temp_dir)
        os.environ["TMPDIR"] = str(fb_temp_dir) # Kann Konflikte verursachen, wenn andere Tools TMPDIR erwarten
        os.environ["TMP"] = str(fb_temp_dir)
        os.environ["TEMP"] = str(fb_temp_dir)
        # FB_HOME und FIREBIRD_HOME könnten kritisch sein, wenn die Client-Bibliothek relativ dazu sucht
        # oder Konfigurationsdateien erwartet.
        # Wir setzen sie auf das Projektverzeichnis, da dort ./lib/libfbclient.so liegt.
        # Wenn Firebird Server-Komponenten erwartet, ist dies ggf. nicht korrekt.
        # Für den reinen Client-Zugriff sollte es aber eher helfen als schaden.
        # Anpassung an generate_yaml_ui.py: FB_HOME und FIREBIRD_HOME auch auf fb_temp_dir setzen.
        os.environ["FB_HOME"] = str(fb_temp_dir)
        os.environ["FIREBIRD_HOME"] = str(fb_temp_dir)
        os.environ["FIREBIRD_LOCK"] = str(fb_temp_dir)


        self.parsed_docs: List[Document] = self._load_and_parse_documentation()

        # --- LLM and Embeddings Configuration ---
        from dotenv import load_dotenv
        # MagicMock import moved to top level

        # Load OpenRouter specific .env file if it exists
        openrouter_env_path = '/home/envs/openrouter.env'
        if os.path.exists(openrouter_env_path):
            load_dotenv(dotenv_path=openrouter_env_path, override=True) # override needed if other .env files exist
            print(f"Loaded environment variables from {openrouter_env_path}")
        
        # Load direct OpenAI specific .env file if it exists
        openai_env_path = '/home/envs/openai.env'
        if os.path.exists(openai_env_path):
            load_dotenv(dotenv_path=openai_env_path, override=True) # override ensures this takes precedence if OPENAI_API_KEY is in both
            print(f"Loaded environment variables from {openai_env_path}")

        # Get API keys
        openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        direct_openai_api_key = os.getenv("OPENAI_API_KEY")

        # --- Initialize Embeddings Model (Prioritize direct OpenAI key) ---
        embeddings_initialized_successfully = False
        if direct_openai_api_key:
            try:
                self.embeddings_model = OpenAIEmbeddings(
                    api_key=direct_openai_api_key,
                    model="text-embedding-3-large" # As requested
                )
                print("OpenAIEmbeddings initialized using direct OPENAI_API_KEY for text-embedding-3-large.")
                embeddings_initialized_successfully = True
            except Exception as e:
                print(f"Error initializing OpenAIEmbeddings with direct key: {e}. Trying OpenRouter key for embeddings if available.")
        
        if not embeddings_initialized_successfully and openrouter_api_key:
            # Fallback to OpenRouter for embeddings if direct OpenAI failed or key wasn't present
            try:
                self.embeddings_model = OpenAIEmbeddings(
                    api_key=openrouter_api_key,
                    base_url="https://openrouter.ai/api/v1",
                    model="text-embedding-ada-002" # A common default, or specify one known to OpenRouter
                )
                print("OpenAIEmbeddings initialized using OPENROUTER_API_KEY (model: text-embedding-ada-002).")
                embeddings_initialized_successfully = True
            except Exception as e:
                print(f"Error initializing OpenAIEmbeddings with OpenRouter key: {e}.")

        if not embeddings_initialized_successfully:
            self.embeddings_model = MagicMock(spec=OpenAIEmbeddings)
            def mock_embed_query(text: str) -> List[float]:
                print(f"MockEmbeddings: Simulating embedding for: {text[:30]}...")
                return [0.0] * 1536
            self.embeddings_model.embed_query = mock_embed_query
            def mock_embed_documents(texts: List[str]) -> List[List[float]]:
                print(f"MockEmbeddings: Simulating embedding for {len(texts)} documents...")
                return [[0.0] * 1536 for _ in texts]
            self.embeddings_model.embed_documents = mock_embed_documents
            print("Using MagicMock for OpenAIEmbeddings as no suitable API key was found or init failed.")

        # --- Initialize LLM (Chat Model) ---
        # self.llm is the argument passed to __init__
        # If it's a string (model name), we initialize it. Otherwise, we use the passed instance.
        if isinstance(self.llm, str):
            llm_model_name = self.llm
            llm_params = {"model_name": llm_model_name, "temperature": 0}
            llm_provider = "Direct OpenAI" # Default

            if openrouter_api_key: # Prioritize OpenRouter for LLM if key exists
                llm_params["api_key"] = openrouter_api_key
                llm_params["base_url"] = "https://openrouter.ai/api/v1"
                # OpenRouter model names often include the provider, e.g., "openai/gpt-3.5-turbo"
                # If llm_model_name doesn't have '/', assume it's a generic name and prepend openai/
                if "/" not in llm_model_name:
                    llm_params["model_name"] = f"openai/{llm_model_name}" # Default to openai prefix for OpenRouter
                llm_provider = "OpenRouter"
                print(f"Configuring LLM '{llm_params['model_name']}' for {llm_provider}.")
            elif direct_openai_api_key:
                llm_params["api_key"] = direct_openai_api_key
                print(f"Configuring LLM '{llm_params['model_name']}' for {llm_provider}.")
            else:
                print(f"WARNING: No API key for LLM '{llm_model_name}'. LLM calls will likely fail or use a mock if not pre-configured.")
                self.llm = MagicMock() # Fallback if string and no key
                print(f"Using MagicMock for LLM '{llm_model_name}'.")

            if not isinstance(self.llm, MagicMock): # If not already mocked
                try:
                    from langchain_openai import ChatOpenAI
                    self.llm = ChatOpenAI(**llm_params) # type: ignore
                    print(f"ChatOpenAI LLM '{llm_params['model_name']}' initialized for {llm_provider}.")
                except Exception as e:
                    print(f"Error initializing ChatOpenAI with model '{llm_params['model_name']}' for {llm_provider}: {e}.")
                    print("Falling back to MagicMock for LLM due to initialization error.")
                    self.llm = MagicMock()
        elif not (direct_openai_api_key or openrouter_api_key) and not isinstance(self.llm, MagicMock):
            print(f"Warning: LLM instance provided but no API key found. LLM calls might fail if it's not a mock.")


        # Retriever instances
        self.faiss_retriever: Optional[FaissDocumentationRetriever] = None
        self.neo4j_retriever: Optional[BaseDocumentationRetriever] = None # Placeholder for Neo4j
        
        self.active_retriever: Optional[BaseDocumentationRetriever] = None
        self.db_engine: Optional[create_engine] = None # Hinzufügen für direkten Engine-Zugriff
        
        self.sql_agent = None # To be initialized by _setup_sql_agent
        self.sql_callback_handler = SQLCaptureCallbackHandler() # Initialize the callback handler

        self._initialize_components() # Call initialization

    def _initialize_components(self):
        """
        Initializes the retriever components based on the retrieval_mode.
        Also sets up the SQL agent.
        """
        if self.retrieval_mode == 'faiss':
            if not self.parsed_docs:
                print("Warning: No documents loaded. FAISS retriever will be empty.")
                # Or raise an error: raise ValueError("Cannot initialize FAISS retriever without parsed documents.")
            try:
                self.faiss_retriever = FaissDocumentationRetriever(
                    documents=self.parsed_docs,
                    embeddings_model=self.embeddings_model
                )
                self.active_retriever = self.faiss_retriever
                print("FAISS retriever initialized and set as active.")
            except Exception as e:
                print(f"Error initializing FAISS retriever: {e}")
                # Potentially fall back to a no-op retriever or raise
        elif self.retrieval_mode == 'neo4j':
            # Placeholder for Neo4j retriever initialization
            # self.neo4j_retriever = Neo4jDocumentationRetriever(self.parsed_docs, self.neo4j_config, self.embeddings_model)
            # self.active_retriever = self.neo4j_retriever
            print("Neo4j retrieval mode selected, but Neo4j retriever is not yet implemented.")
            pass
        else:
            print(f"Warning: Unknown retrieval_mode '{self.retrieval_mode}'. No document retriever will be active.")

        # Setup SQL agent
        self.sql_agent = self._setup_sql_agent()
        if self.sql_agent:
            print("SQL Agent initialized successfully.")
        else:
            print("Warning: SQL Agent initialization failed.")


    def _setup_sql_agent(self):
        """
        Initializes the Langchain SQL Agent.
        """
        # --- Diagnose: SQLAlchemy Dialekte auflisten ---
        try:
            import importlib.metadata
            print("Inspecting SQLAlchemy dialects via importlib.metadata:")
            dialects_group = 'sqlalchemy.dialects'
            entry_points = []
            # In Python 3.10+ importlib.metadata.entry_points() returns a SelectableGroups object
            # For older versions, it might return a dict or require a different approach.
            # We'll try the modern approach first.
            try:
                eps = importlib.metadata.entry_points(group=dialects_group)
                if eps: # Check if eps is not None or empty
                     for ep in eps:
                        entry_points.append(ep.name)
            except AttributeError: # Fallback for older Python versions if .entry_points(group=...) is not available or behaves differently
                 # This fallback might need adjustment based on the specific Python version's importlib.metadata API
                all_eps = importlib.metadata.entry_points()
                if dialects_group in all_eps:
                    for ep in all_eps[dialects_group]:
                        entry_points.append(ep.name)

            if entry_points:
                print(f"Found entry points for '{dialects_group}':")
                for ep_name in sorted(list(set(entry_points))): # Sort and unique
                    print(f"  - {ep_name}")
            else:
                print(f"No entry points found for group '{dialects_group}'. This method might not work for this Python/SQLAlchemy version or no dialects are registered this way.")

        except Exception as e_diag:
            print(f"Error inspecting SQLAlchemy dialects via importlib.metadata: {e_diag}")
        # --- Ende Diagnose ---

        # # --- Test direkter fdb.connect für Firebird Embedded ---
        # if "firebird+fdb" in self.db_connection_string and "///" in self.db_connection_string: # Nur für Embedded-Test
        #     print("Attempting direct fdb.connect test for embedded Firebird...")
        #     try:
        #         url_for_direct_test = make_url(self.db_connection_string)
        #         db_path_for_direct_test = str(url_for_direct_test.database)
        #         if db_path_for_direct_test.startswith("//"): # Korrektur für Pfad, falls nötig
        #              db_path_for_direct_test = db_path_for_direct_test[1:]
        #
        #         print(f"Direct fdb.connect with DSN: {db_path_for_direct_test}, User: {url_for_direct_test.username}")
        #         conn_test_direct = fdb.connect(
        #             dsn=db_path_for_direct_test,
        #             user=url_for_direct_test.username,
        #             password=url_for_direct_test.password,
        #             charset="WIN1252"
        #         )
        #         print("Direct fdb.connect successful.")
        #         conn_test_direct.close()
        #         print("Direct fdb.connect closed.")
        #     except Exception as e_fdb_direct:
        #         print(f"Direct fdb.connect test failed: {e_fdb_direct}")
        #         print("Skipping further SQL Agent setup due to direct fdb.connect failure.")
        #         return None # Verhindert weiteren Initialisierungsversuch
        # # --- Ende direkter fdb.connect Test ---

        if not self.db_connection_string:
            print("Error: DB connection string is not set. Cannot initialize SQL Agent.")
            return None
        if not self.llm:
            print("Error: LLM is not set. Cannot initialize SQL Agent.")
            return None
            
        try:
            if self.db_connection_string == "sqlite:///:memory:":
                try:
                    print("Setting up SQLite in-memory database with persistent connection for TestTable...")
                    # Create a persistent in-memory SQLite connection
                    # The check_same_thread=False is important for some Langchain/SQLAlchemy uses.
                    connection = sqlite3.connect(":memory:", check_same_thread=False)
                    
                    # Create and populate TestTable using this connection
                    create_table_sql = "CREATE TABLE TestTable (id INTEGER PRIMARY KEY, name VARCHAR(100));"
                    connection.execute(create_table_sql)
                    print(f"Executed via sqlite3.Connection: {create_table_sql}")
                    
                    insert_sql = "INSERT INTO TestTable (id, name) VALUES (1, 'Sample Item');"
                    connection.execute(insert_sql)
                    print(f"Executed via sqlite3.Connection: {insert_sql}")
                    connection.commit()

                    # Verify table creation using the same connection
                    verification_query = "SELECT name FROM sqlite_master WHERE type='table' AND name='TestTable';"
                    cursor = connection.execute(verification_query)
                    verification_result = cursor.fetchall()
                    print(f"Verification query via sqlite3.Connection '{verification_query}' result: {verification_result}")
                    if not verification_result or "TestTable" not in str(verification_result):
                         print("WARNING: TestTable might not have been created successfully or is not visible via sqlite3.Connection.")

                    # Create SQLAlchemy engine that uses the existing connection
                    engine = create_engine(
                        "sqlite://",  # In-memory database
                        creator=lambda: connection,  # Reuse the existing connection
                        poolclass=StaticPool,  # Disable pooling for single connection
                        connect_args={"check_same_thread": False}
                    )
                    print("SQLAlchemy engine created for the persistent SQLite connection.")

                    # Initialize SQLDatabase with the engine and explicitly include TestTable
                    self.db_engine = engine # Engine speichern
                    db = SQLDatabase(self.db_engine, include_tables=['TestTable'])
                    print("SQLDatabase initialized with custom engine and include_tables=['TestTable'].")

                except Exception as e_create:
                    print(f"Could not create or verify TestTable in sqlite:///:memory: for test: {e_create}")
                    return None # Ensure agent setup fails if in-memory DB setup fails
            else:
                # Für Firebird: Verwende den ursprünglichen firebird+fdb:// Dialekt
                try:
                    print(f"Attempting to connect using original connection string: {self.db_connection_string}")
                    
                    # Erstelle die Engine direkt mit dem ursprünglichen Connection String
                    # VERSUCH MIT CREATOR-FUNKTION
                    def create_fdb_connection():
                        import fdb # Import hier, um sicherzustellen, dass es verfügbar ist
                        url_info = make_url(self.db_connection_string)
                        db_path_for_creator = str(url_info.database)
                        if db_path_for_creator.startswith("//"): # Korrektur für Pfad, falls nötig
                             db_path_for_creator = db_path_for_creator[1:]
                        
                        print(f"Creator function: Connecting to DSN: {db_path_for_creator}, User: {url_info.username or 'SYSDBA'}")
                        return fdb.connect(
                            dsn=db_path_for_creator,
                            user=url_info.username or "SYSDBA",
                            password=url_info.password or "masterkey",
                            charset="WIN1252" # Zeichensatz hier explizit für fdb.connect
                        )

                    engine = create_engine(
                        "firebird+fdb://", # Generischer DSN, da Creator verwendet wird
                        creator=create_fdb_connection,
                        poolclass=NullPool, # NullPool anstelle von StaticPool versuchen
                        echo=False
                    )
                    
                    # Entferne den separaten Test-Verbindungsblock, um potenzielle Sperrkonflikte zu reduzieren.
                    # Die Initialisierung von SQLDatabase wird die Verbindung testen.
                    
                    self.db_engine = engine
                    # Explizit 'BEWOHNER' und andere potenziell wichtige Tabellen einbeziehen
                    # Für den Test fokussieren wir uns auf BEWOHNER
                    self.db = SQLDatabase(self.db_engine) # Zurücksetzen, um alle Tabellen zu laden
                    # Teste die Verbindung durch Abrufen der Tabellennamen direkt nach der Initialisierung
                    print(f"✓ SQLDatabase initialized. Usable tables: {self.db.get_usable_table_names()}")
                    print("✓ SQLDatabase connection seems OK based on get_usable_table_names().")
                    
                except Exception as e_firebird:
                    print(f"✗ Error with firebird+fdb dialect: {e_firebird}")
                    import traceback
                    traceback.print_exc()
                    # Kein Fallback mehr, um das Firebird-Problem direkt zu adressieren
                    print("SQLAgent setup: Firebird connection failed. No fallback to SQLite.")
                    self.db_engine = None # Sicherstellen, dass keine alte Engine-Referenz bleibt
                    self.db = None        # Sicherstellen, dass keine alte DB-Referenz bleibt
                    return None # SQL Agent Initialisierung fehlschlagen lassen


            if self.db is None: # Zusätzliche Prüfung, falls die Erstellung oben fehlschlägt
                print("SQLDatabase instance could not be created.")
                return None

            toolkit = SQLDatabaseToolkit(db=self.db, llm=self.llm)
            
            # Define a more specific system message for the SQL agent
            # This can be further refined.
            system_message = """
            You are an expert Firebird SQL data analyst.
            Given an input question, first create a syntactically correct Firebird SQL query to run,
            then look at the results of the query and return the answer.
            Unless the user specifies a specific number of examples they wish to obtain, always limit your query to at most 10 results. For Firebird, use `SELECT FIRST N ...` or `SELECT ... ROWS N` or `SELECT ... FETCH FIRST N ROWS ONLY` to limit results. Do NOT use `LIMIT N`.
            You can order the results by a relevant column to return the most interesting examples in the database.
            Never query for all the columns from a specific table, only ask for the relevant columns given the question.
            
            VERY IMPORTANT: Only use column names that you can explicitly see in the schema description for the respective tables. Do not invent column names or assume they exist.
            
            Before generating a query, if you are unsure about table names or column names, you MUST use the 'sql_db_list_tables' tool to see available tables or the 'sql_db_schema' tool to get the schema for specific tables.
            When you use 'sql_db_schema', state clearly for which table(s) you are requesting the schema.
            After obtaining the schema information, explicitly state what you have learned or if the information was sufficient before constructing the SQL query.
            If the 'sql_db_schema' tool seems to not work or returns unexpected results, please state this in your thought process.
            Be careful to not query for columns that do not exist.
            Also, pay attention to which column is in which table. If the schema information is incomplete or seems to be missing for a table, state this and ask for clarification rather than guessing column names.
            If the schema information from the `sql_db_schema` tool is ambiguous or seems incomplete, prioritize the table and column information found in the supplementary documentation context (YAML, Markdown files) if available.

            Use the DDL and schema information provided in the documentation context and from the `sql_db_schema` tool to construct your queries.
            If a Stored Procedure seems relevant based on its name or description in the documentation, consider using it.
            For Firebird, Stored Procedures are often selected using a SELECT query, e.g., SELECT * FROM MY_PROCEDURE(param1, param2).

            Always use the following format STRICTLY:

            Question: The input question you must answer
            Thought: You should always think about what to do. Describe your thought process.
            Action: The action to take. Must be one of [sql_db_query, sql_db_schema, sql_db_list_tables, sql_db_query_checker].
            Action Input: The input to the action. For 'sql_db_schema', this should be a comma-separated list of table names, if querying multiple tables.
            Observation: The result of the action.
            ... (this Thought/Action/Action Input/Observation can repeat N times)
            Thought: I now know the final answer.
            Final Answer: The final answer to the original input question.

            Ensure your response for "Action" and "Action Input" are on separate lines and correctly labeled. Do not output just the tool name or tool name and input without the "Action:" and "Action Input:" prefixes.
            """
            # Note: The exact tools available (sql_db_query, etc.) depend on the SQLDatabaseToolkit.
            # The agent created by create_sql_agent with SQLDatabaseToolkit will have these.

            agent_executor = create_sql_agent(
                llm=self.llm,
                toolkit=toolkit,
                verbose=True, # Set to False for less console output in production
                handle_parsing_errors=True, # Handles errors if LLM outputs non-SQL
                max_iterations=10,
                callbacks=[self.sql_callback_handler], # Pass the callback handler here
                return_intermediate_steps=True, # Hinzufügen, um Schritte zu erhalten
                agent_kwargs={
                    "handle_parsing_errors": True
                }
            )
            # For some agent types, the system message is part of the prompt or passed differently.
            # The default create_sql_agent might not directly use "system_message" in agent_kwargs
            # in the same way as a direct ChatOpenAI call. It constructs its own prompt.
            # We might need to customize the prompt template if we want a very specific system message.
            # For now, we rely on the default prompt structure of create_sql_agent.
            
            return agent_executor
        except Exception as e:
            print(f"Error initializing SQL Agent: {e}")
            return None

    def _load_and_parse_documentation(
            self,
            schema_path: str = "output/schema",
            yamls_path: str = "output/yamls",
            ddl_path: str = "output/ddl"
        ) -> List[Document]:
        """
        Loads and parses documentation from specified project directories.
        Converts various file formats (Markdown, YAML, SQL) into Langchain Documents.

        Args:
            schema_path: Path to the directory containing general schema Markdown files.
            yamls_path: Path to the directory containing YAML table/procedure definitions.
            ddl_path: Path to the directory containing DDL SQL scripts.

        Returns:
            A list of Langchain Document objects.
        """
        all_documents: List[Document] = []
        doc_id_counter = 1
        MAX_DOC_CONTENT_LENGTH = 1500 # Maximale Zeichen pro Dokument für Embedding (stärker reduziert)

        # 1. Load Markdown files from output/schema/
        #    (index.md, relation_report.md, table_diagrams.md, table_clusters.md, and individual table/proc MDs)
        for md_file_path in glob.glob(os.path.join(schema_path, "*.md")):
            try:
                with open(md_file_path, 'r', encoding='utf-8') as f:
                    content = f.read()[:MAX_DOC_CONTENT_LENGTH] # Inhalt kürzen
                file_name = os.path.basename(md_file_path)
                metadata = {"source": file_name, "type": "schema_markdown", "path": md_file_path, "doc_id": f"doc_{doc_id_counter}"}
                all_documents.append(Document(page_content=content, metadata=metadata))
                doc_id_counter +=1
            except Exception as e:
                print(f"Error reading or processing Markdown file {md_file_path}: {e}")

        # 2. Load YAML files from output/yamls/
        for yaml_file_path in glob.glob(os.path.join(yamls_path, "*.yaml")):
            try:
                with open(yaml_file_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                file_name = os.path.basename(yaml_file_path)
                
                # Convert YAML data to a structured text representation
                # This is a basic representation, can be made more sophisticated
                content_parts = [f"Source YAML: {file_name}"]
                if isinstance(data, dict):
                    table_name = data.get('name', file_name.replace('.yaml', ''))
                    content_parts.append(f"Entity Name: {table_name}")
                    description = data.get('description', 'N/A')
                    content_parts.append(f"Description: {description}")

                    if 'columns' in data and isinstance(data['columns'], list):
                        content_parts.append("Columns:")
                        for col in data['columns']:
                            if isinstance(col, dict):
                                col_name = col.get('name', 'N/A')
                                col_type = col.get('type', 'N/A')
                                col_desc = col.get('description', 'N/A')
                                content_parts.append(f"  - {col_name} (Type: {col_type}): {col_desc}")
                    
                    if 'relations' in data and isinstance(data['relations'], list): # Assuming 'relations' key from previous plan
                        content_parts.append("Relations:")
                        for rel in data['relations']:
                             content_parts.append(f"  - {rel}")
                
                page_content = "\n".join(content_parts)[:MAX_DOC_CONTENT_LENGTH] # Inhalt kürzen
                metadata = {"source": file_name, "type": "yaml_definition", "path": yaml_file_path, "doc_id": f"doc_{doc_id_counter}"}
                all_documents.append(Document(page_content=page_content, metadata=metadata))
                doc_id_counter +=1
            except yaml.YAMLError as e:
                print(f"Error parsing YAML file {yaml_file_path}: {e}")
            except Exception as e:
                print(f"Error reading or processing YAML file {yaml_file_path}: {e}")

        # 3. Load SQL DDL files from output/ddl/
        for sql_file_path in glob.glob(os.path.join(ddl_path, "*.sql")):
            try:
                with open(sql_file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                file_name = os.path.basename(sql_file_path)
                # Attempt to determine if it's a table or procedure from filename
                entity_type = "procedure_ddl" if "procedure" in file_name.lower() else "table_ddl"
                metadata = {"source": file_name, "type": entity_type, "path": sql_file_path, "doc_id": f"doc_{doc_id_counter}"}
                # Prepend context to the SQL content
                page_content = f"DDL script for {file_name}:\n```sql\n{content}\n```"[:MAX_DOC_CONTENT_LENGTH] # Inhalt kürzen
                all_documents.append(Document(page_content=page_content, metadata=metadata))
                doc_id_counter +=1
            except Exception as e:
                print(f"Error reading or processing SQL file {sql_file_path}: {e}")
        
        print(f"Loaded {len(all_documents)} documents.")
        return all_documents

    # Placeholder for other methods as per plan.md
    # def _generate_textual_responses(self, query, sql_generated, sql_result, doc_context): ...

    def query(self, natural_language_query: str, retrieval_mode_override: Optional[str] = None) -> Dict[str, Any]:
        """
        Processes a natural language query:
        1. Retrieves relevant documentation context.
        2. Uses the SQL agent to generate and execute a SQL query.
        3. Prepares data for textual response generation.
        """
        if not self.sql_agent:
            return {"error": "SQL Agent is not initialized."}

        current_retrieval_mode = retrieval_mode_override if retrieval_mode_override else self.retrieval_mode
        
        doc_context_str = ""
        retrieved_docs: List[Document] = []

        if current_retrieval_mode == 'faiss' and self.faiss_retriever:
            print(f"Retrieving context using FAISS for query: \"{natural_language_query}\"")
            retrieved_docs = self.faiss_retriever.get_relevant_documents(natural_language_query)
            # self.active_retriever is already set during _initialize_components
        elif current_retrieval_mode == 'neo4j' and self.neo4j_retriever:
            # This part will be enabled when Neo4j retriever is implemented
            # print(f"Retrieving context using Neo4j for query: \"{natural_language_query}\"")
            # retrieved_docs = self.neo4j_retriever.get_relevant_documents(natural_language_query)
            print("Neo4j retriever selected but not fully implemented in query method yet.")
            # self.active_retriever would be set if neo4j was initialized
            pass
        
        if not self.active_retriever and (current_retrieval_mode == 'faiss' or current_retrieval_mode == 'neo4j'):
             print(f"Warning: Retriever for mode '{current_retrieval_mode}' is not available or not initialized. Proceeding without doc context.")


        if retrieved_docs:
            doc_context_str = "\n\n".join([f"--- Source: {doc.metadata.get('source', 'N/A')} ---\n{doc.page_content}" for doc in retrieved_docs])
            print(f"Retrieved context ({len(retrieved_docs)} docs):\n{doc_context_str[:500]}...")
        else:
            print("No relevant documentation context found or retriever not active for the selected mode.")
        
        enhanced_query_for_agent = f"""
        Based on the following documentation context:
        --- START OF CONTEXT ---
        {doc_context_str if doc_context_str else "No specific context retrieved."}
        --- END OF CONTEXT ---

        Please answer the following question: {natural_language_query}
        """
        
        print(f"\nSending to SQL agent:\nUser Query: {natural_language_query}\nEnhanced with context (first 200 chars of context): {doc_context_str[:200] if doc_context_str else 'N/A'}")

        try:
            self.sql_callback_handler.clear_log() # Clear previous full log and SQL query
            
            # Use invoke instead of run for more structured output
            agent_response_dict = self.sql_agent.invoke({"input": enhanced_query_for_agent, "chat_history": []})
            agent_final_answer = agent_response_dict.get("output", "No output from agent.")
            
            # Get SQL from the callback handler, which should be more reliable now
            generated_sql = self.sql_callback_handler.sql_query
            
            # Get the full log of actions and observations from the callback
            detailed_steps = self.sql_callback_handler.full_log
            
            if not generated_sql: # If callback didn't set it directly
                # Try to find it in the detailed_steps from the callback
                for log_entry in reversed(detailed_steps):
                    action_data = log_entry.get("action")
                    if action_data and action_data.get("tool") == "sql_db_query":
                        tool_input = action_data.get("tool_input")
                        if isinstance(tool_input, str):
                            generated_sql = tool_input
                            break
                        elif isinstance(tool_input, dict) and 'query' in tool_input:
                            generated_sql = tool_input['query']
                            break
            
            if not generated_sql: # If still not found
                generated_sql = "SQL_QUERY_NOT_EXTRACTED_BY_CALLBACK_OR_LOG_PARSE"
                print("Warning: SQL query could not be extracted via callback or by parsing its full_log.")
            else:
                # This print might be redundant if the callback already printed it.
                # Consider removing if callback's print is sufficient.
                print(f"SQL extracted (by query method logic): {generated_sql}")

            print(f"Agent Final Answer: {agent_final_answer}")

            # Now generate the three textual response variants
            text_responses = self._generate_textual_responses(
                natural_language_query=natural_language_query,
                retrieved_context=doc_context_str,
                agent_final_answer=agent_final_answer, # Use the 'output' from invoke
                generated_sql=generated_sql
            )

            return {
                "natural_language_query": natural_language_query,
                "retrieved_context": doc_context_str,
                "agent_final_answer": agent_final_answer,
                "generated_sql": generated_sql,
                "text_variants": text_responses,
                "detailed_steps": detailed_steps,
                "error": None
            }
 
        except Exception as e:
            print(f"Error during SQL agent execution: {e}")
            # Log the full exception for debugging
            import traceback
            traceback.print_exc()
            # Ensure text_variants is populated even in case of agent error before _generate_textual_responses
            error_text_variants = [
                {"variant_name": "Error Variant 1", "text": f"SQL Agent execution failed: {e}"},
                {"variant_name": "Error Variant 2", "text": "The system could not process the request with the SQL agent."},
                {"variant_name": "Error Variant 3", "text": "Please try rephrasing or check logs for SQL agent errors."}
            ]
            return {
                "natural_language_query": natural_language_query,
                "retrieved_context": doc_context_str,
                "agent_final_answer": None,
                "generated_sql": None,
                "text_variants": error_text_variants,
                "detailed_steps": self.sql_callback_handler.full_log if hasattr(self, 'sql_callback_handler') else [],
                "error": str(e)
            }
 
    def _generate_textual_responses(self,
                                    natural_language_query: str,
                                    retrieved_context: str,
                                    agent_final_answer: Optional[str],
                                    generated_sql: Optional[str]) -> List[Dict[str, str]]:
        """
        Generates three different textual response variants based on the agent's findings.
        """
        if not self.llm:
            print("Error: LLM is not set. Cannot generate textual responses.")
            return [{"variant_name": "Error", "text": "LLM not available."}]

        if agent_final_answer is None and generated_sql is None:
            return [
                {"variant_name": "Error Variant", "text": "The SQL agent failed to produce a response or SQL query."},
                {"variant_name": "Suggestion Variant", "text": "Could you try rephrasing your question? The system was unable to process it."},
                {"variant_name": "Contextual Suggestion", "text": f"Based on your query '{natural_language_query}', the system couldn't find a direct answer. You might want to explore related topics in the documentation."}
            ]

        # Fallback if LLM is a MagicMock or if we want to ensure some output even if LLM fails for other reasons
        if isinstance(self.llm, MagicMock) or not hasattr(self.llm, 'invoke'):
            print("LLM is a MagicMock or does not have 'invoke'. Generating placeholder responses.")
            return [
                {"variant_name": "Placeholder Basic", "text": f"Query: {natural_language_query}\nSQL: {generated_sql}\nAnswer: {agent_final_answer}"},
                {"variant_name": "Placeholder Detailed", "text": f"For your question '{natural_language_query}', the system generated the SQL query '{generated_sql}' and found the answer: {agent_final_answer}. Context used: {retrieved_context[:100]}..."},
                {"variant_name": "Placeholder Summary", "text": f"The answer to '{natural_language_query}' is {agent_final_answer}."}
            ]

        # Prompts for the three variants
        prompt_template_1 = f"""
        Original Question: {natural_language_query}
        Retrieved Documentation Context:
        {retrieved_context if retrieved_context else "No specific documentation context was retrieved."}
        ---
        Generated SQL Query (if available): {generated_sql if generated_sql else "Not available or not applicable."}
        ---
        Final Answer from SQL Agent: {agent_final_answer if agent_final_answer else "No answer was produced by the SQL agent."}
        ---
        Based on all the information above, provide a concise, direct answer to the original question.
        Focus on the 'Final Answer from SQL Agent'. If the agent's answer is sufficient, use it directly.
        If the context or SQL provides additional clarity, incorporate it briefly.
        Do not mention the SQL query or the documentation retrieval process unless it's essential for understanding the answer.
        """

        prompt_template_2 = f"""
        Original Question: {natural_language_query}
        Retrieved Documentation Context:
        {retrieved_context if retrieved_context else "No specific documentation context was retrieved."}
        ---
        Generated SQL Query (if available): {generated_sql if generated_sql else "Not available or not applicable."}
        ---
        Final Answer from SQL Agent: {agent_final_answer if agent_final_answer else "No answer was produced by the SQL agent."}
        ---
        Provide a more detailed explanation.
        Start by stating the answer derived from the 'Final Answer from SQL Agent'.
        Then, explain how this answer was found, mentioning the role of the SQL query (if available and relevant) and any key information from the documentation context that supports or clarifies the answer.
        If the SQL query is complex or insightful, you can briefly describe what it does.
        """

        prompt_template_3 = f"""
        Original Question: {natural_language_query}
        Retrieved Documentation Context:
        {retrieved_context if retrieved_context else "No specific documentation context was retrieved."}
        ---
        Generated SQL Query (if available): {generated_sql if generated_sql else "Not available or not applicable."}
        ---
        Final Answer from SQL Agent: {agent_final_answer if agent_final_answer else "No answer was produced by the SQL agent."}
        ---
        Provide a very brief, executive-summary style answer to the original question.
        This should be a single sentence if possible, directly addressing the user's query based on the 'Final Answer from SQL Agent'.
        Avoid technical jargon, SQL details, or context mentions unless absolutely critical to the core answer.
        """
        
        responses = []
        prompts = [
            ("Concise Direct Answer", prompt_template_1),
            ("Detailed Explanation", prompt_template_2),
            ("Executive Summary", prompt_template_3)
        ]

        for variant_name, prompt_content in prompts:
            try:
                # Assuming self.llm is an initialized Langchain LLM/ChatModel
                # For newer Langchain versions, it's usually .invoke() for chat models
                # or .generate() for LLMs. Adjust if your self.llm has a different API.
                if hasattr(self.llm, 'invoke'):
                    # For ChatModels (like ChatOpenAI)
                    from langchain_core.messages import HumanMessage
                    message = HumanMessage(content=prompt_content)
                    response_content = self.llm.invoke([message]).content # type: ignore
                elif hasattr(self.llm, 'generate'):
                    # For older LLMs or if invoke is not available
                    response_content = self.llm.generate([prompt_content]).generations[0][0].text # type: ignore
                else:
                    response_content = "LLM does not support .invoke or .generate."
                
                responses.append({"variant_name": variant_name, "text": str(response_content)})
            except Exception as e:
                print(f"Error generating text variant '{variant_name}' with LLM: {e}")
                responses.append({"variant_name": variant_name, "text": f"Error generating response: {e}"})
        
        return responses


# --- Main execution / Test section ---
if __name__ == "__main__":
    # Minimal FDB Connection Test ist jetzt Teil der globalen Initialisierung oben.
    # Der Code hier wird nur ausgeführt, wenn die globale Initialisierung erfolgreich war
    # oder wenn wir einen expliziten SQLite-Fallback für Tests ohne DB-Zugriff wollen.

    import shutil # For cleaning up dummy files/dirs
    # --- Configuration for Testing ---
    # TEST_DB_CONNECTION_STRING wird nicht mehr direkt hier verwendet, da die DB global initialisiert wird.
    # Wir verwenden GLOBAL_DB für den Agenten, falls es erfolgreich initialisiert wurde.
    
    # LLM Configuration (using a placeholder model name, replace if needed)
    # Ensure OPENROUTER_API_KEY or OPENAI_API_KEY is set in your environment or .env file
    # For OpenRouter, model name might be like "openai/gpt-3.5-turbo"
    # For direct OpenAI, model name might be "gpt-3.5-turbo"
    TEST_LLM_MODEL_NAME = "openai/gpt-4.1-nano" # Vom Benutzer angefordertes Modell

    # --- Setup Dummy Documentation ---
    # Create dummy directories and files for documentation loading
    dummy_schema_path = "output_dummy/schema"
    dummy_yamls_path = "output_dummy/yamls"
    dummy_ddl_path = "output_dummy/ddl"
    
    os.makedirs(dummy_schema_path, exist_ok=True)
    os.makedirs(dummy_yamls_path, exist_ok=True)
    os.makedirs(dummy_ddl_path, exist_ok=True)

    with open(os.path.join(dummy_schema_path, "index.md"), "w", encoding="utf-8") as f:
        f.write("# Main Schema\nThis is the main schema document.")
    with open(os.path.join(dummy_schema_path, "tables.md"), "w", encoding="utf-8") as f:
        f.write("# Tables\nDetails about tables.")
    
    # Dummy YAML for a hypothetical 'TestTable' (matching the one created in _setup_sql_agent for sqlite)
    dummy_test_table_yaml = {
        "name": "TestTable",
        "description": "A table for testing purposes.",
        "columns": [
            {"name": "id", "type": "INTEGER", "description": "Primary key"},
            {"name": "name", "type": "VARCHAR(100)", "description": "Name of the item"}
        ],
        "relations": [] # No relations for this simple example
    }
    with open(os.path.join(dummy_yamls_path, "test_table.yaml"), "w", encoding="utf-8") as f: # Ensure this matches the table name used in sqlite setup
        yaml.dump(dummy_test_table_yaml, f)

    with open(os.path.join(dummy_ddl_path, "create_test_table.sql"), "w", encoding="utf-8") as f:
        f.write("CREATE TABLE TestTable (id INTEGER PRIMARY KEY, name VARCHAR(100));")
    with open(os.path.join(dummy_ddl_path, "another_table.sql"), "w", encoding="utf-8") as f:
        f.write("CREATE TABLE AnotherTable (data TEXT);")

    # --- Symlink or Move 'output' to 'output_default' and 'output_dummy' to 'output' ---
    # This is to make the agent use the dummy files without changing its internal paths.
    # We'll restore them in the finally block.
    
    # Define paths
    default_output_path = "output"
    dummy_output_target_path = "output" # The agent expects 'output'
    
    # Backup map to store original locations if we move/rename
    backup_map = {}

    def setup_symlinks_or_moves(default_path, dummy_source_path, target_link_name, backup_mapping):
        """
        Sets up the environment for testing by either symlinking or moving directories.
        - If default_path exists, it's moved to default_path_backup.
        - dummy_source_path is then symlinked or moved to target_link_name.
        """
        backup_suffix = "_roo_backup"
        
        # Handle the original 'output' directory
        if os.path.exists(target_link_name):
            if os.path.islink(target_link_name):
                print(f"Removing existing symlink: {target_link_name}")
                os.unlink(target_link_name)
            else: # It's a directory or file
                backup_location = target_link_name + backup_suffix
                print(f"Backing up existing '{target_link_name}' to '{backup_location}'")
                if os.path.exists(backup_location):
                    print(f"Warning: Backup location '{backup_location}' already exists. Removing it.")
                    shutil.rmtree(backup_location) # Remove if it exists to avoid error in rename
                os.rename(target_link_name, backup_location)
                backup_mapping[target_link_name] = backup_location
        
        # Create symlink from dummy_source_path to target_link_name
        try:
            os.symlink(os.path.abspath(dummy_source_path), os.path.abspath(target_link_name), target_is_directory=True)
            print(f"Symlinked '{dummy_source_path}' to '{target_link_name}'")
        except OSError as e:
            print(f"Symlink creation failed (OSError: {e}). Falling back to moving/renaming '{dummy_source_path}' to '{target_link_name}'.")
            try:
                shutil.copytree(dummy_source_path, target_link_name) # Use copytree for directories
                print(f"Copied '{dummy_source_path}' to '{target_link_name}' as fallback.")
                backup_mapping[target_link_name] = "copied_dummy" # Mark that we copied, so we remove it later
            except Exception as move_e:
                print(f"Fallback move/copy also failed for '{dummy_source_path}' to '{target_link_name}': {move_e}")
                raise # Re-raise if fallback also fails

    # --- Test Execution ---
    agent = None
    try:
        # Setup: Use dummy 'output_dummy' as 'output' for the test
        setup_symlinks_or_moves(
            default_output_path,      # Original 'output' path (if it exists, it will be backed up)
            "output_dummy",           # The dummy directory we want to use
            dummy_output_target_path, # The name the agent expects ('output')
            backup_map
        )

        print(f"\n=== TESTING DIRECT FDB INTERFACE ===")
        print(f"Initializing FirebirdDirectSQLAgent with DB: {DB_CONNECTION_STRING_GLOBAL} and LLM: {TEST_LLM_MODEL_NAME}")
        
        # Teste zuerst die direkte FDB-Schnittstelle
        try:
            from firebird_sql_agent_direct import FirebirdDirectSQLAgent
            
            direct_agent = FirebirdDirectSQLAgent(
                db_connection_string=DB_CONNECTION_STRING_GLOBAL,
                llm=TEST_LLM_MODEL_NAME,
                retrieval_mode='faiss'
            )
            
            if direct_agent and direct_agent.sql_agent:
                print("✓ Direct FDB Agent initialized successfully.")
                
                # Test-Abfragen für die direkte FDB-Schnittstelle
                direct_test_queries = [
                    "Zeige mir die ersten 5 Bewohner.",
                    "Welche Spalten hat die Tabelle BEWOHNER?",
                    "Liste alle verfügbaren Tabellen auf."
                ]
                
                for i, test_query in enumerate(direct_test_queries, 1):
                    print(f"\n--- Direct FDB Test Query {i}: \"{test_query}\" ---")
                    try:
                        response = direct_agent.query(test_query)
                        
                        print(f"Response for Direct FDB Query {i}:")
                        print(f"  Natural Language Query: {response.get('natural_language_query')}")
                        print(f"  Generated SQL: {response.get('generated_sql')}")
                        print(f"  Agent Final Answer: {response.get('agent_final_answer')}")
                        
                        if response.get("text_variants"):
                            for j, variant in enumerate(response["text_variants"]):
                                print(f"  Text Variant {j+1} ({variant.get('variant_name')}):\n    {variant.get('text')[:200]}...")
                        
                        if response.get('error'):
                            print(f"  Error: {response.get('error')}")
                            
                    except Exception as e_direct_query:
                        print(f"Error in direct FDB query {i}: {e_direct_query}")
                        import traceback
                        traceback.print_exc()
            else:
                print("✗ Direct FDB Agent initialization failed.")
                
        except Exception as e_direct_agent:
            print(f"✗ Error initializing Direct FDB Agent: {e_direct_agent}")
            import traceback
            traceback.print_exc()

        print(f"\n=== TESTING ORIGINAL SQLALCHEMY APPROACH (for comparison) ===")
        print(f"Initializing FirebirdDocumentedSQLAgent with DB from global config ({DB_CONNECTION_STRING_GLOBAL}) and LLM: {TEST_LLM_MODEL_NAME}")
        
        # Attempt to use a real LLM if API keys are available, otherwise it will use MagicMock
        # The __init__ method handles API key loading and LLM/Embedding initialization
        agent = None # Initialisiere agent mit None
        if GLOBAL_DB: # Nur initialisieren, wenn die globale DB-Verbindung erfolgreich war
            print(f"Using globally initialized SQLDatabase instance (GLOBAL_DB) for agent.")
            agent = FirebirdDocumentedSQLAgent(
                db_connection_string=DB_CONNECTION_STRING_GLOBAL,
                llm=TEST_LLM_MODEL_NAME,
                retrieval_mode='faiss'
            )
        else:
            print("\nGlobal database initialization failed. Attempting Agent init with SQLite for non-DB tests.")
            try:
                print("Setting up fallback SQLite in-memory for agent testing...")
                import sqlite3 # Sicherstellen, dass sqlite3 importiert ist
                # Die SQLite Engine und DB-Erstellung muss hier erfolgen,
                # da der Agent eine SQLDatabase-Instanz erwartet.
                sqlite_engine_fallback = create_engine("sqlite:///:memory:", poolclass=NullPool)
                with sqlite_engine_fallback.connect() as conn_fallback:
                    conn_fallback.execute(text("CREATE TABLE TestTable (id INTEGER PRIMARY KEY, name VARCHAR(100));"))
                    conn_fallback.execute(text("INSERT INTO TestTable (id, name) VALUES (1, 'SQLite Sample');"))
                    conn_fallback.commit()
                
                # Wichtig: include_tables hier verwenden, da SQLDatabase sonst die Tabelle nicht kennt.
                sqlite_db_fallback = SQLDatabase(sqlite_engine_fallback, include_tables=['TestTable'])
                print("✓ Fallback SQLite DB created and initialized for agent.")
                
                # Der Konstruktor von FirebirdDocumentedSQLAgent erwartet eine SQLDatabase-Instanz.
                # Die db_connection_string wird für den SQLite-Fall nicht mehr direkt übergeben.
                agent = FirebirdDocumentedSQLAgent(
                    db_connection_string=DB_CONNECTION_STRING_GLOBAL,
                    llm=TEST_LLM_MODEL_NAME,
                    retrieval_mode='faiss'
                )
            except Exception as e_sqlite_fallback_agent:
                print(f"✗ Error creating SQLite fallback agent: {e_sqlite_fallback_agent}")
                agent = None # Sicherstellen, dass Agent None ist
        
        # Check if the agent and its SQL sub-agent were initialized
        if agent and agent.sql_agent and agent.db_engine: # Prüfen, ob die Engine gespeichert wurde
            print("\nAgent and SQL sub-agent initialized successfully.")

            # --- Direkter SQLDatabase Schema Test ---
            # Sicherstellen, dass agent und agent.db existieren, bevor darauf zugegriffen wird.
            # Dieser Test wird wahrscheinlich fehlschlagen, wenn der Agent aufgrund von DB-Problemen nicht initialisiert werden konnte.
            if agent and hasattr(agent, 'db') and agent.db:
                print(f"\n--- Attempting to get schema for BEWOHNER via SQLDatabase instance: {agent.db} ---")
                try:
                    # Zuerst prüfen, ob die Tabelle überhaupt in den bekannten Tabellen von SQLDatabase ist
                    all_known_tables = agent.db.get_usable_table_names()
                    print(f"All tables known to SQLDatabase: {all_known_tables}")
                    # Verwende den kleingeschriebenen Namen, wie er von get_usable_table_names() zurückgegeben wird
                    table_name_to_test = "bewohner"
                    if table_name_to_test in all_known_tables:
                        bewohner_schema = agent.db.get_table_info([table_name_to_test])
                        print(f"\nSchema for {table_name_to_test.upper()} (via SQLDatabase.get_table_info):")
                        print(bewohner_schema)
                    else:
                        print("Table BEWOHNER not found in SQLDatabase's usable table names.")
                except Exception as e_schema_test:
                    print(f"Error getting schema for BEWOHNER via SQLDatabase.get_table_info: {e_schema_test}")
                    import traceback
                    traceback.print_exc()
                print("--- End of direct SQLDatabase Schema test ---")
            elif agent:
                 print("\nSQLDatabase instance (agent.db) not found or agent not fully initialized for direct schema test.")
            else:
                print("\nAgent not initialized, skipping direct SQLDatabase Schema test.")
            # --- Ende Direkter SQLDatabase Schema Test ---

            # --- Direkter SQLAlchemy Inspector Test ---
            from sqlalchemy import inspect, text
            engine_to_inspect = agent.db_engine # Gespeicherte Engine verwenden
            print(f"\n--- Running direct SQLAlchemy Inspector test for table BEWOHNER on engine: {engine_to_inspect} ---")
            try:
                inspector = inspect(engine_to_inspect)
                columns = inspector.get_columns("BEWOHNER") # Großschreibung beachten, wie Firebird es speichert
                if columns:
                    print("Columns in BEWOHNER (via direct inspection):")
                    for column in columns:
                        print(f"  - {column['name']}: {column['type']}")
                else:
                    print("Could not retrieve columns for BEWOHNER via direct inspection (no columns found or table does not exist).")
                
                # Teste eine einfache Abfrage direkt über SQLAlchemy, um die Verbindung weiter zu prüfen
                print("\nAttempting direct SQLAlchemy query on BEWOHNER...")
                with engine_to_inspect.connect() as connection:
                    result = connection.execute(text("SELECT FIRST 5 * FROM BEWOHNER"))
                    print("Direct query successful. First 5 rows (or less):")
                    for row in result:
                        print(row)
                    result.close()

            except Exception as e_inspect:
                print(f"Error during direct SQLAlchemy inspection/query for BEWOHNER: {e_inspect}")
                import traceback
                traceback.print_exc()
            print("--- End of direct SQLAlchemy Inspector test ---")
            # --- Ende Direkter SQLAlchemy Inspector Test ---
 
            # Test query
            # This query should work with the in-memory SQLite TestTable
            test_query_1 = "Zeige mir die ersten 5 Bewohner." # Query for Wincasa DB
            print(f"\n--- Running Test Query 1: \"{test_query_1}\" ---")
            response_1 = agent.query(test_query_1)
            print(f"\nResponse for Query 1:")
            print(f"  Natural Language Query: {response_1.get('natural_language_query')}")
            # print(f"  Retrieved Context: {response_1.get('retrieved_context')[:200]}...") # Print first 200 chars
            print(f"  Generated SQL: {response_1.get('generated_sql')}")
            print(f"  Agent Final Answer: {response_1.get('agent_final_answer')}")
            if response_1.get("text_variants"):
                for i, variant in enumerate(response_1["text_variants"]):
                    print(f"  Text Variant {i+1} ({variant.get('variant_name')}):\n    {variant.get('text')}")
            if response_1.get('detailed_steps'):
                print("\n  Detailed Steps (Query 1 from Callback Handler):")
                for entry_idx, entry in enumerate(response_1['detailed_steps']):
                    action_data = entry.get('action', {})
                    observation = entry.get('observation', entry.get('error', 'N/A')) # Handle if it's an error entry
                    print(f"    Step {entry_idx + 1}:")
                    print(f"      Tool: {action_data.get('tool')}")
                    print(f"      Tool Input: {action_data.get('tool_input')}")
                    print(f"      Observation/Error: {str(observation)[:500]}...") # Truncate long observations
            if response_1.get('error'):
                print(f"  Error: {response_1.get('error')}")
 
            test_query_2 = "Welche Spalten hat die Tabelle BEWOHNER?" # Query for Wincasa DB
            print(f"\n--- Running Test Query 2: \"{test_query_2}\" ---")
            response_2 = agent.query(test_query_2)
            print(f"\nResponse for Query 2:")
            print(f"  Natural Language Query: {response_2.get('natural_language_query')}")
            print(f"  Generated SQL: {response_2.get('generated_sql')}")
            print(f"  Agent Final Answer: {response_2.get('agent_final_answer')}")
            if response_2.get("text_variants"):
                 for i, variant in enumerate(response_2["text_variants"]):
                    print(f"  Text Variant {i+1} ({variant.get('variant_name')}):\n    {variant.get('text')}")
            if response_2.get('detailed_steps'):
                print("\n  Detailed Steps (Query 2 from Callback Handler):")
                for entry_idx, entry in enumerate(response_2['detailed_steps']):
                    action_data = entry.get('action', {})
                    observation = entry.get('observation', entry.get('error', 'N/A'))
                    print(f"    Step {entry_idx + 1}:")
                    print(f"      Tool: {action_data.get('tool')}")
                    print(f"      Tool Input: {action_data.get('tool_input')}")
                    print(f"      Observation/Error: {str(observation)[:500]}...")
            if response_2.get('error'):
                print(f"  Error: {response_2.get('error')}")

            # test_query_3 = "What is the name of the item with id 99?" # Test non-existent
            # print(f"\n--- Running Test Query 3: \"{test_query_3}\" ---")
            # response_3 = agent.query(test_query_3)
            # print(f"\nResponse for Query 3:")
            # print(f"  Natural Language Query: {response_3.get('natural_language_query')}")
            # print(f"  Generated SQL: {response_3.get('generated_sql')}")
            # print(f"  Agent Final Answer: {response_3.get('agent_final_answer')}")
            # if response_3.get("text_variants"):
            #      for i, variant in enumerate(response_3["text_variants"]):
            #         print(f"  Text Variant {i+1} ({variant.get('variant_name')}):\n    {variant.get('text')}")
            # if response_3.get('detailed_steps'):
            #     print("\n  Detailed Steps (Query 3 from Callback Handler):")
            #     for entry_idx, entry in enumerate(response_3['detailed_steps']):
            #         action_data = entry.get('action', {})
            #         observation = entry.get('observation', entry.get('error', 'N/A'))
            #         print(f"    Step {entry_idx + 1}:")
            #         print(f"      Tool: {action_data.get('tool')}")
            #         print(f"      Tool Input: {action_data.get('tool_input')}")
            #         print(f"      Observation/Error: {str(observation)[:500]}...")
            # if response_3.get('error'):
            #     print(f"  Error: {response_3.get('error')}")

            # test_query_4 = "Are there any items with 'Sample' in their name?" # Test LIKE
            # print(f"\n--- Running Test Query 4: \"{test_query_4}\" ---")
            # response_4 = agent.query(test_query_4)
            # print(f"\nResponse for Query 4:")
            # print(f"  Natural Language Query: {response_4.get('natural_language_query')}")
            # print(f"  Generated SQL: {response_4.get('generated_sql')}")
            # print(f"  Agent Final Answer: {response_4.get('agent_final_answer')}")
            # if response_4.get("text_variants"):
            #      for i, variant in enumerate(response_4["text_variants"]):
            #         print(f"  Text Variant {i+1} ({variant.get('variant_name')}):\n    {variant.get('text')}")
            # if response_4.get('detailed_steps'):
            #     print("\n  Detailed Steps (Query 4 from Callback Handler):")
            #     for entry_idx, entry in enumerate(response_4['detailed_steps']):
            #         action_data = entry.get('action', {})
            #         observation = entry.get('observation', entry.get('error', 'N/A'))
            #         print(f"    Step {entry_idx + 1}:")
            #         print(f"      Tool: {action_data.get('tool')}")
            #         print(f"      Tool Input: {action_data.get('tool_input')}")
            #         print(f"      Observation/Error: {str(observation)[:500]}...")
            # if response_4.get('error'):
            #     print(f"  Error: {response_4.get('error')}")
 
        else:
            print("\nAgent or SQL sub-agent initialization failed. Check logs.")

    except Exception as e:
        print(f"\nAn error occurred during the test: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # --- Cleanup ---
        print("\n--- Cleaning up dummy files and restoring original 'output' directory ---")
        
        # Remove the symlink/copied dummy 'output'
        if os.path.islink(dummy_output_target_path):
            print(f"Removing symlink: {dummy_output_target_path}")
            os.unlink(dummy_output_target_path)
        elif backup_map.get(dummy_output_target_path) == "copied_dummy": # If we copied it
            print(f"Removing copied dummy directory: {dummy_output_target_path}")
            if os.path.exists(dummy_output_target_path): # Check existence before removal
                 shutil.rmtree(dummy_output_target_path)
        
        # Restore original 'output' if it was backed up
        backed_up_original_output = backup_map.get(dummy_output_target_path)
        if backed_up_original_output and backed_up_original_output != "copied_dummy":
            if os.path.exists(backed_up_original_output):
                print(f"Restoring original '{dummy_output_target_path}' from '{backed_up_original_output}'")
                os.rename(backed_up_original_output, dummy_output_target_path)
            else:
                print(f"Warning: Backup '{backed_up_original_output}' not found. Cannot restore.")
        
        # Remove the main dummy directory
        if os.path.exists("output_dummy"):
            print("Removing main dummy directory: output_dummy")
            shutil.rmtree("output_dummy")
        
        print("Cleanup complete.")

# Example of how to load environment variables from a specific .env file
# from dotenv import load_dotenv
# load_dotenv(dotenv_path='/path/to/your/.env') # Replace with actual path if needed

# Example of direct OpenAIEmbeddings initialization (if you have the key)
# try:
#     embeddings = OpenAIEmbeddings(api_key="sk-...") # Replace with your key
#     print("OpenAIEmbeddings initialized successfully with direct key.")
# except Exception as e:
#     print(f"Error initializing OpenAIEmbeddings with direct key: {e}")

# Example of OpenRouter Embeddings initialization
# try:
#     embeddings_openrouter = OpenAIEmbeddings(
#         api_key=os.getenv("OPENROUTER_API_KEY"), # Ensure this is set
#         base_url="https://openrouter.ai/api/v1",
#         model="text-embedding-ada-002" # Or other model
#     )
#     print("OpenAIEmbeddings initialized successfully with OpenRouter.")
# except Exception as e:
#     print(f"Error initializing OpenAIEmbeddings with OpenRouter: {e}")


# --- Test with a mock LLM to ensure agent structure works without API calls ---
def run_test_with_mock_llm():
    print("\n--- Running Test with Mock LLM ---")
    
    # Create dummy documentation as before
    dummy_schema_path_mock = "output_mock_schema"
    dummy_yamls_path_mock = "output_mock_yamls"
    dummy_ddl_path_mock = "output_mock_ddl"
    os.makedirs(dummy_schema_path_mock, exist_ok=True)
    os.makedirs(dummy_yamls_path_mock, exist_ok=True)
    os.makedirs(dummy_ddl_path_mock, exist_ok=True)
    with open(os.path.join(dummy_yamls_path_mock, "test_table.yaml"), "w", encoding="utf-fs8") as f: # Corrected typo utf-8
        yaml.dump({"name": "TestTable", "description": "Mock table"}, f)
    # Add other dummy files if needed for _load_and_parse_documentation

    mock_backup_map = {}
    try:
        setup_symlinks_or_moves(
            "output",
            "output_mock_yamls", # This should be the parent dummy dir, e.g., "output_mock"
                                 # if _load_and_parse_documentation expects output/yamls etc.
                                 # For simplicity, let's assume _load_and_parse_documentation
                                 # will be called with schema_path="output_mock_schema", etc.
                                 # OR, we create output_mock/yamls, output_mock/schema etc.
            "output", # Target link name
            mock_backup_map
        )
        
        # Create a proper mock structure for 'output_mock'
        os.makedirs("output_mock/schema", exist_ok=True)
        os.makedirs("output_mock/yamls", exist_ok=True)
        os.makedirs("output_mock/ddl", exist_ok=True)
        with open(os.path.join("output_mock/yamls", "test_table.yaml"), "w", encoding="utf-8") as f:
             yaml.dump({"name": "TestTable", "description": "Mock table for mock LLM test"}, f)


        # If OPENAI_API_KEY is not set, the agent's __init__ should fall back to MagicMock for LLM
        # We can explicitly pass a MagicMock instance too.
        from unittest.mock import MagicMock
        mock_llm = MagicMock()
        
        # Configure the mock LLM to return a plausible response for agent.run()
        # The SQL agent's .run() method typically returns a string which is the final answer.
        # For the SQL agent part:
        mock_sql_agent_run_return = "The TestTable contains 10 items."
        
        # For the _generate_textual_responses part, the mock_llm.invoke might be called.
        # Let's make it return something simple.
        if hasattr(mock_llm, 'invoke'):
            mock_llm.invoke.return_value = MagicMock(content="Mocked LLM response for text generation.")
        elif hasattr(mock_llm, 'generate'): # For older Langchain LLM interface
             mock_llm.generate.return_value = MagicMock(generations=[[MagicMock(text="Mocked LLM response for text generation.")]])


        # Temporarily unset API keys to force mock usage if relying on internal fallback
        original_openai_key = os.environ.pop("OPENAI_API_KEY", None)
        original_openrouter_key = os.environ.pop("OPENROUTER_API_KEY", None)

        try:
            # Pass the MagicMock instance directly
            mock_agent = FirebirdDocumentedSQLAgent(
                db_connection_string="sqlite:///:memory:", 
                llm=mock_llm, # Pass the MagicMock instance
                retrieval_mode='faiss'
            )

            # We need to mock the sql_agent.run part specifically if the outer llm mock isn't enough
            if mock_agent.sql_agent: # If sql_agent was created (it should be, even with mock LLM for toolkit)
                mock_agent.sql_agent.run = MagicMock(return_value=mock_sql_agent_run_return)
            else:
                print("Warning: SQL agent was not created in mock test, cannot mock its run method.")


            if mock_agent:
                print("\nMock LLM Agent initialized.")
                test_query_mock = "How many items in TestTable with mock?"
                response_mock = mock_agent.query(test_query_mock)
                print(f"\nResponse for Mock LLM Query:")
                print(f"  Natural Language Query: {response_mock.get('natural_language_query')}")
                print(f"  Agent Final Answer: {response_mock.get('agent_final_answer')}") # Should be mock_sql_agent_run_return
                if response_mock.get("text_variants"):
                    for i, variant in enumerate(response_mock["text_variants"]):
                        print(f"  Text Variant {i+1} ({variant.get('variant_name')}):\n    {variant.get('text')}")
                if response_mock.get('error'):
                    print(f"  Error: {response_mock.get('error')}")
            else:
                print("Mock LLM Agent initialization failed.")
        finally:
            # Restore API keys if they were popped
            if original_openai_key:
                os.environ["OPENAI_API_KEY"] = original_openai_key
            if original_openrouter_key:
                os.environ["OPENROUTER_API_KEY"] = original_openrouter_key
    
    except Exception as e_mock:
        print(f"Error during mock LLM test: {e_mock}")
        traceback.print_exc()
    finally:
        # Cleanup for mock test
        if os.path.islink("output") and os.readlink("output") == os.path.abspath("output_mock"): # Check if it points to output_mock
            os.unlink("output")
        elif os.path.exists("output") and mock_backup_map.get("output") == "copied_dummy": # if output_mock was copied to output
             shutil.rmtree("output")


        if mock_backup_map.get("output") and mock_backup_map.get("output") != "copied_dummy":
            if os.path.exists(mock_backup_map["output"]):
                 os.rename(mock_backup_map["output"], "output")
        
        shutil.rmtree(dummy_schema_path_mock, ignore_errors=True)
        shutil.rmtree(dummy_yamls_path_mock, ignore_errors=True)
        shutil.rmtree(dummy_ddl_path_mock, ignore_errors=True)
        shutil.rmtree("output_mock", ignore_errors=True) # Remove the parent mock dir
        print("Mock LLM test cleanup complete.")

