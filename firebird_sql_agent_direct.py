import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Tuple
from unittest.mock import MagicMock
import yaml
import glob
import time

# Langchain imports
from langchain_core.documents import Document
from langchain_core.callbacks.base import BaseCallbackHandler
from langchain_core.agents import AgentAction, AgentFinish
from langchain_openai import OpenAIEmbeddings
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits.sql.base import create_sql_agent
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_core.tools import BaseTool
from langchain_core.callbacks.manager import CallbackManagerForToolRun

# Lokale Imports
from fdb_direct_interface import FDBDirectInterface
from retrievers import FaissDocumentationRetriever, BaseDocumentationRetriever
from enhanced_retrievers import EnhancedMultiStageRetriever, EnhancedFaissRetriever
from query_preprocessor import QueryPreprocessor
from db_knowledge_compiler import DatabaseKnowledgeCompiler

# Phoenix monitoring import
from phoenix_monitoring import get_monitor, trace_query


class FDBQueryTool(BaseTool):
    """
    Custom Tool für direkte FDB-Abfragen, das die FDBDirectInterface verwendet.
    """
    name: str = "fdb_query"
    description: str = """
    Führt SQL-SELECT-Abfragen direkt auf der Firebird-Datenbank aus.
    Input sollte eine gültige SQL-SELECT-Abfrage sein.
    Gibt die Ergebnisse als formatierte Tabelle zurück.
    """
    
    def __init__(self, fdb_interface: FDBDirectInterface, **kwargs):
        super().__init__(**kwargs)
        # Speichere die FDB-Interface-Referenz in einer privaten Variable
        self._fdb_interface = fdb_interface
    
    def _run(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Führt die SQL-Abfrage aus und gibt formatierte Ergebnisse zurück."""
        monitor = get_monitor(enable_ui=False)
        start_time = time.time()
        
        try:
            # SQL-Abfrage ausführen
            results = self._fdb_interface.run_sql(query)
            
            if not results:
                return "Abfrage ausgeführt, aber keine Ergebnisse zurückgegeben."
            
            # Spaltennamen abrufen
            column_names = self._fdb_interface.get_column_names(query)
            
            # Ergebnisse formatieren
            if column_names:
                # Header erstellen
                formatted_results = [" | ".join(column_names)]
                formatted_results.append("-" * len(formatted_results[0]))
                
                # Datenzeilen hinzufügen
                for row in results[:10]:  # Limitiere auf 10 Zeilen für bessere Lesbarkeit
                    formatted_row = " | ".join(str(cell) if cell is not None else "NULL" for cell in row)
                    formatted_results.append(formatted_row)
                
                if len(results) > 10:
                    formatted_results.append(f"... und {len(results) - 10} weitere Zeilen")
                
                return "\n".join(formatted_results)
            else:
                # Fallback ohne Spaltennamen
                formatted_results = []
                for i, row in enumerate(results[:10]):
                    formatted_results.append(f"Zeile {i+1}: {row}")
                
                if len(results) > 10:
                    formatted_results.append(f"... und {len(results) - 10} weitere Zeilen")
                
                result_str = "\n".join(formatted_results)
                
                # Track successful SQL execution
                execution_time = time.time() - start_time
                monitor.track_query_execution(
                    query="",  # Original user query not available here
                    sql=query,
                    execution_time=execution_time,
                    rows_returned=len(results),
                    success=True
                )
                
                return result_str
                
        except Exception as e:
            # Track failed SQL execution
            execution_time = time.time() - start_time
            monitor.track_query_execution(
                query="",
                sql=query,
                execution_time=execution_time,
                rows_returned=0,
                success=False,
                error=str(e)
            )
            return f"Fehler beim Ausführen der Abfrage: {str(e)}"


class FDBSchemaInfoTool(BaseTool):
    """
    Custom Tool für Schema-Informationen über die FDBDirectInterface.
    """
    name: str = "fdb_schema"
    description: str = """
    Gibt Schema-Informationen für Firebird-Tabellen zurück.
    Input sollte eine kommagetrennte Liste von Tabellennamen sein.
    Wenn leer, werden alle verfügbaren Tabellen aufgelistet.
    """
    
    def __init__(self, fdb_interface: FDBDirectInterface, **kwargs):
        super().__init__(**kwargs)
        self._fdb_interface = fdb_interface
    
    def _run(
        self,
        table_names: str = "",
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Gibt Schema-Informationen für die angegebenen Tabellen zurück."""
        try:
            if not table_names.strip():
                # Alle Tabellen auflisten
                all_tables = self._fdb_interface.get_table_names()
                if all_tables:
                    return f"Verfügbare Tabellen ({len(all_tables)}):\n" + "\n".join(f"- {table}" for table in all_tables)
                else:
                    return "Keine Tabellen gefunden."
            
            # Spezifische Tabellen
            tables = [name.strip() for name in table_names.split(",") if name.strip()]
            return self._fdb_interface.get_table_info(tables)
            
        except Exception as e:
            return f"Fehler beim Abrufen der Schema-Informationen: {str(e)}"


class FDBListTablesTool(BaseTool):
    """
    Custom Tool zum Auflisten aller Tabellen.
    """
    name: str = "fdb_list_tables"
    description: str = "Listet alle verfügbaren Tabellen in der Firebird-Datenbank auf."
    
    def __init__(self, fdb_interface: FDBDirectInterface, **kwargs):
        super().__init__(**kwargs)
        self._fdb_interface = fdb_interface
    
    def _run(
        self,
        query: str = "",
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Listet alle verfügbaren Tabellen auf."""
        try:
            tables = self._fdb_interface.get_table_names()
            if tables:
                return f"Verfügbare Tabellen ({len(tables)}):\n" + ", ".join(tables)
            else:
                return "Keine Tabellen gefunden."
        except Exception as e:
            return f"Fehler beim Auflisten der Tabellen: {str(e)}"


class DirectFDBCallbackHandler(BaseCallbackHandler):
    """Callback Handler für die direkte FDB-Schnittstelle."""
    
    def __init__(self):
        super().__init__()
        self.sql_query: Optional[str] = None
        self.full_log: List[Dict[str, Any]] = []
        self._current_action: Optional[AgentAction] = None
        self.monitor = get_monitor(enable_ui=False)
        self._llm_start_time = None

    def on_agent_action(self, action: AgentAction, **kwargs: Any) -> Any:
        """Called when the agent is about to perform an action."""
        print(f"DirectFDB Callback: Agent action: {action.tool}, Input: {action.tool_input}")
        self._current_action = action
        
        # SQL-Abfrage erfassen
        if action.tool == "fdb_query":
            if isinstance(action.tool_input, str):
                self.sql_query = action.tool_input
            elif isinstance(action.tool_input, dict) and 'query' in action.tool_input:
                self.sql_query = action.tool_input['query']
            else:
                self.sql_query = str(action.tool_input)
            
            print(f"DirectFDB Callback captured SQL: {self.sql_query}")

    def on_tool_end(self, output: str, name: str, **kwargs: Any) -> Any:
        """Called when a tool has finished running."""
        print(f"DirectFDB Callback: Tool '{name}' ended. Output: {str(output)[:200]}...")
        if self._current_action:
            self.full_log.append({
                "action": self._current_action.dict(),
                "observation": output
            })
            self._current_action = None

    def on_tool_error(self, error: Union[Exception, KeyboardInterrupt], name: str, **kwargs: Any) -> Any:
        """Called when a tool errors."""
        print(f"DirectFDB Callback: Tool '{name}' errored: {error}")
        if self._current_action:
            self.full_log.append({
                "action": self._current_action.dict(),
                "error": str(error)
            })
            self._current_action = None

    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any) -> Any:
        """Called when LLM starts running."""
        self._llm_start_time = time.time()
        print(f"DirectFDB Callback: LLM starting with prompt length: {len(prompts[0]) if prompts else 0}")
    
    def on_llm_end(self, response: Any, **kwargs: Any) -> Any:
        """Called when LLM ends running."""
        if self._llm_start_time:
            duration = time.time() - self._llm_start_time
            
            # Extract response text and estimate tokens
            response_text = ""
            if hasattr(response, 'generations') and response.generations:
                response_text = response.generations[0][0].text if response.generations[0] else ""
            
            # Rough token estimation (1 token ≈ 4 chars)
            prompt_tokens = len(str(kwargs.get('prompts', [''])[0])) // 4 if 'prompts' in kwargs else 100
            completion_tokens = len(response_text) // 4
            total_tokens = prompt_tokens + completion_tokens
            
            # Estimate cost (GPT-4 pricing as example)
            cost = (prompt_tokens * 0.03 + completion_tokens * 0.06) / 1000
            
            self.monitor.track_llm_call(
                model="gpt-4",  # Default, could be extracted from serialized
                prompt=str(kwargs.get('prompts', [''])[0])[:500] if 'prompts' in kwargs else "",
                response=response_text[:500],
                tokens_used=total_tokens,
                cost=cost,
                duration=duration
            )
            
            self._llm_start_time = None
    
    def clear_log(self):
        """Clears all captured data for the next run."""
        self.sql_query = None
        self.full_log = []
        self._current_action = None
        self._llm_start_time = None


class FirebirdDirectSQLAgent:
    """
    Firebird SQL Agent mit direkter FDB-Schnittstelle.
    Umgeht SQLAlchemy-Sperrprobleme durch direkte fdb-Verbindungen.
    """
    
    def __init__(self, db_connection_string: str, llm: Any, retrieval_mode: str = 'faiss', 
                 neo4j_config: Dict = None, use_enhanced_knowledge: bool = True, 
                 doc_mode: str = 'yaml_only'):
        """
        Initialisiert den FirebirdDirectSQLAgent.
        
        Args:
            db_connection_string: SQLAlchemy-Connection-String für Firebird
            llm: Language Model Instanz
            retrieval_mode: 'faiss', 'neo4j', oder 'enhanced'
            neo4j_config: Neo4j-Konfiguration (falls verwendet)
            use_enhanced_knowledge: Aktiviert das erweiterte Wissenssystem
            doc_mode: 'yaml_only' (default), 'all', 'markdown_only' - controls which docs to load
        """
        self.db_connection_string = db_connection_string
        self.llm = llm
        self.retrieval_mode = retrieval_mode
        self.neo4j_config = neo4j_config
        self.use_enhanced_knowledge = use_enhanced_knowledge
        self.doc_mode = doc_mode
        
        # FDB Direct Interface initialisieren
        print(f"Initialisiere FDBDirectInterface für: {db_connection_string}")
        self.fdb_interface = FDBDirectInterface.from_connection_string(db_connection_string)
        
        # Knowledge Base kompilieren (falls noch nicht vorhanden)
        if self.use_enhanced_knowledge:
            self._ensure_knowledge_base()
        
        # Query Preprocessor initialisieren
        self.query_preprocessor = QueryPreprocessor() if self.use_enhanced_knowledge else None
        
        # Dokumentation laden
        self.parsed_docs: List[Document] = self._load_and_parse_documentation()
        
        # LLM und Embeddings konfigurieren
        self._setup_llm_and_embeddings()
        
        # Retriever initialisieren
        self.faiss_retriever: Optional[FaissDocumentationRetriever] = None
        self.neo4j_retriever: Optional[BaseDocumentationRetriever] = None
        self.enhanced_retriever: Optional[EnhancedMultiStageRetriever] = None
        self.active_retriever: Optional[BaseDocumentationRetriever] = None
        
        # SQL Agent und Callback Handler
        self.sql_agent = None
        self.callback_handler = DirectFDBCallbackHandler()
        
        # Komponenten initialisieren
        self._initialize_components()
    
    def _setup_llm_and_embeddings(self):
        """Konfiguriert LLM und Embeddings."""
        from dotenv import load_dotenv
        
        # Environment-Dateien laden
        openrouter_env_path = '/home/envs/openrouter.env'
        if os.path.exists(openrouter_env_path):
            load_dotenv(dotenv_path=openrouter_env_path, override=True)
            print(f"Loaded environment variables from {openrouter_env_path}")
        
        openai_env_path = '/home/envs/openai.env'
        if os.path.exists(openai_env_path):
            load_dotenv(dotenv_path=openai_env_path, override=True)
            print(f"Loaded environment variables from {openai_env_path}")
        
        # API-Schlüssel abrufen
        openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        direct_openai_api_key = os.getenv("OPENAI_API_KEY")
        
        # Embeddings initialisieren
        embeddings_initialized_successfully = False
        if direct_openai_api_key:
            try:
                self.embeddings_model = OpenAIEmbeddings(
                    api_key=direct_openai_api_key,
                    model="text-embedding-3-large"
                )
                print("OpenAIEmbeddings initialized using direct OPENAI_API_KEY.")
                embeddings_initialized_successfully = True
            except Exception as e:
                print(f"Error initializing OpenAIEmbeddings with direct key: {e}")
        
        if not embeddings_initialized_successfully and openrouter_api_key:
            try:
                self.embeddings_model = OpenAIEmbeddings(
                    api_key=openrouter_api_key,
                    base_url="https://openrouter.ai/api/v1",
                    model="text-embedding-ada-002"
                )
                print("OpenAIEmbeddings initialized using OPENROUTER_API_KEY.")
                embeddings_initialized_successfully = True
            except Exception as e:
                print(f"Error initializing OpenAIEmbeddings with OpenRouter key: {e}")
        
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
            print("Using MagicMock for OpenAIEmbeddings.")
        
        # LLM initialisieren
        if isinstance(self.llm, str):
            llm_model_name = self.llm
            llm_params = {"model_name": llm_model_name, "temperature": 0}
            llm_provider = "Direct OpenAI"
            
            if openrouter_api_key:
                llm_params["api_key"] = openrouter_api_key
                llm_params["base_url"] = "https://openrouter.ai/api/v1"
                if "/" not in llm_model_name:
                    llm_params["model_name"] = f"openai/{llm_model_name}"
                llm_provider = "OpenRouter"
                print(f"Configuring LLM '{llm_params['model_name']}' for {llm_provider}.")
            elif direct_openai_api_key:
                llm_params["api_key"] = direct_openai_api_key
                print(f"Configuring LLM '{llm_params['model_name']}' for {llm_provider}.")
            else:
                print(f"WARNING: No API key for LLM '{llm_model_name}'. Using MagicMock.")
                self.llm = MagicMock()
            
            if not isinstance(self.llm, MagicMock):
                try:
                    from langchain_openai import ChatOpenAI
                    self.llm = ChatOpenAI(**llm_params)
                    print(f"ChatOpenAI LLM '{llm_params['model_name']}' initialized for {llm_provider}.")
                except Exception as e:
                    print(f"Error initializing ChatOpenAI: {e}. Falling back to MagicMock.")
                    self.llm = MagicMock()
    
    def _ensure_knowledge_base(self):
        """Stellt sicher, dass die Knowledge Base kompiliert ist."""
        kb_path = Path("output/compiled_knowledge_base.json")
        if not kb_path.exists():
            print("Knowledge Base nicht gefunden. Kompiliere...")
            compiler = DatabaseKnowledgeCompiler()
            compiler.compile_knowledge()
            print("Knowledge Base erfolgreich kompiliert.")
    
    def _initialize_components(self):
        """Initialisiert Retriever und SQL Agent."""
        # FAISS Retriever
        if self.retrieval_mode == 'faiss':
            if not self.parsed_docs:
                print("Warning: No documents loaded. FAISS retriever will be empty.")
            try:
                if self.use_enhanced_knowledge:
                    # Enhanced FAISS Retriever mit Knowledge Base
                    self.faiss_retriever = EnhancedFaissRetriever(
                        parsed_docs=self.parsed_docs,
                        openai_api_key=os.getenv("OPENAI_API_KEY", "")
                    )
                else:
                    # Standard FAISS Retriever
                    self.faiss_retriever = FaissDocumentationRetriever(
                        documents=self.parsed_docs,
                        embeddings_model=self.embeddings_model
                    )
                self.active_retriever = self.faiss_retriever
                print(f"{'Enhanced' if self.use_enhanced_knowledge else 'Standard'} FAISS retriever initialized.")
            except Exception as e:
                print(f"Error initializing FAISS retriever: {e}")
                self.faiss_retriever = None
                self.active_retriever = None
        
        elif self.retrieval_mode == 'enhanced':
            # Multi-Stage Enhanced Retriever
            if not self.parsed_docs:
                print("Warning: No documents loaded. Enhanced retriever will be empty.")
            try:
                self.enhanced_retriever = EnhancedMultiStageRetriever(
                    parsed_docs=self.parsed_docs,
                    openai_api_key=os.getenv("OPENAI_API_KEY", "")
                )
                self.active_retriever = self.enhanced_retriever
                print("Enhanced Multi-Stage retriever initialized and set as active.")
            except Exception as e:
                print(f"Error initializing Enhanced retriever: {e}")
                self.enhanced_retriever = None
                self.active_retriever = None
        
        elif self.retrieval_mode == 'neo4j':
            print("Neo4j retrieval mode selected, but not yet implemented.")
        
        # SQL Agent mit direkten FDB-Tools
        self.sql_agent = self._setup_direct_sql_agent()
        if self.sql_agent:
            print("Direct FDB SQL Agent initialized successfully.")
        else:
            print("Warning: Direct FDB SQL Agent initialization failed.")
    
    def _setup_direct_sql_agent(self):
        """Erstellt einen SQL Agent mit direkten FDB-Tools."""
        if not self.llm:
            print("Error: LLM is not set. Cannot initialize SQL Agent.")
            return None
        
        try:
            # Custom Tools für direkte FDB-Operationen erstellen
            tools = [
                FDBQueryTool(self.fdb_interface),
                FDBSchemaInfoTool(self.fdb_interface),
                FDBListTablesTool(self.fdb_interface)
            ]
            
            # System-Nachricht für den Agent mit erweitertem Datenbankwissen
            if self.use_enhanced_knowledge:
                # Lade kompakten Datenbankkontext
                kb_path = Path("output/database_context_prompt.txt")
                if kb_path.exists():
                    with open(kb_path, 'r', encoding='utf-8') as f:
                        db_context = f.read()
                else:
                    db_context = "Datenbank: WINCASA Property Management System"
                
                system_message = f"""
Du bist ein Experte für das WINCASA Property Management Firebird SQL-Datenbanksystem.

{db_context}

Du hast Zugriff auf folgende Tools:
1. fdb_query: Führt SQL-SELECT-Abfragen direkt auf der Firebird-Datenbank aus
2. fdb_schema: Gibt Schema-Informationen für Tabellen zurück
3. fdb_list_tables: Listet alle verfügbaren Tabellen auf

Wichtige Hinweise für SQL-Abfragen:
- Verwende nur Spaltennamen, die du explizit in der Schema-Beschreibung siehst
- Für Firebird verwende `SELECT FIRST N ...` anstatt `LIMIT N`
- Bei JOINs bevorzuge die dokumentierten Beziehungen (z.B. EIGENTUEMER -> OBJEKTE über VEREIG)
- Deutsche Geschäftsbegriffe: Eigentümer=Owner, Bewohner=Tenant, Objekte=Properties, Konten=Accounts
- Für Finanzabfragen nutze oft die Tabellen: KONTEN, ZAHLUNG, BUCHUNG, SOLLSTELLUNG
- Für Personenabfragen nutze: EIGENTUEMER, BEWOHNER mit deren Adresstabellen EIGADR, BEWADR

WICHTIGE ADRESSABFRAGE-HINWEISE für BEWOHNER-Tabelle:
- BSTR-Spalte enthält: "Straßenname Hausnummer" (z.B. "Marienstraße 26")
- BPLZORT-Spalte enthält: "PLZ Ort" (z.B. "45307 Essen")
- VERWENDE NIEMALS EXACT MATCH für Adressen! Verwende IMMER LIKE-Muster!
- Korrekte Syntax: WHERE BSTR LIKE 'Marienstraße%' AND BPLZORT LIKE '%45307%'
- FALSCH: WHERE BSTR = 'Marienstraße' (findet nichts!)
- RICHTIG: WHERE BSTR LIKE 'Marienstraße%' (findet "Marienstraße 26")

Vorgehen:
1. Analysiere die Anfrage und identifiziere relevante Geschäftsentitäten
2. Prüfe verfügbare Tabellen mit fdb_list_tables falls nötig
3. Hole Schema-Informationen mit fdb_schema für die relevanten Tabellen
4. Erstelle eine syntaktisch korrekte Firebird SQL-Abfrage
5. Führe die Abfrage aus und analysiere die Ergebnisse
6. Gib eine klare, geschäftsorientierte Antwort

Antworte im ReAct-Format (Thought/Action/Action Input/Observation).
"""
            else:
                # Standard System-Nachricht ohne erweiterte Wissensbasis
                system_message = """
Du bist ein Experte für Firebird SQL-Datenanalyse.
Du hast Zugriff auf folgende Tools:

1. fdb_query: Führt SQL-SELECT-Abfragen direkt auf der Firebird-Datenbank aus
2. fdb_schema: Gibt Schema-Informationen für Tabellen zurück
3. fdb_list_tables: Listet alle verfügbaren Tabellen auf

Für eine gegebene Frage:
1. Erstelle eine syntaktisch korrekte Firebird SQL-Abfrage
2. Führe die Abfrage aus und analysiere die Ergebnisse
3. Gib eine klare Antwort basierend auf den Ergebnissen

WICHTIG: 
- Verwende nur Spaltennamen, die du explizit in der Schema-Beschreibung siehst
- Für Firebird verwende `SELECT FIRST N ...` anstatt `LIMIT N`
- Prüfe zuerst verfügbare Tabellen mit fdb_list_tables
- Hole Schema-Informationen mit fdb_schema bevor du Abfragen erstellst
- Verwende nur SELECT-Abfragen

Antworte immer im folgenden Format:

Frage: Die zu beantwortende Eingabefrage
Gedanke: Beschreibe deinen Denkprozess
Aktion: Die auszuführende Aktion (fdb_query, fdb_schema, oder fdb_list_tables)
Aktions-Eingabe: Die Eingabe für die Aktion
Beobachtung: Das Ergebnis der Aktion
... (Gedanke/Aktion/Aktions-Eingabe/Beobachtung können sich N-mal wiederholen)
Gedanke: Ich kenne jetzt die endgültige Antwort
Endgültige Antwort: Die endgültige Antwort auf die ursprüngliche Eingabefrage
"""
            
            # Agent mit ReAct-Prompt erstellen
            from langchain.agents import create_react_agent, AgentExecutor
            from langchain import hub
            
            # ReAct-Prompt laden oder erstellen
            try:
                prompt = hub.pull("hwchase17/react")
            except:
                # Fallback: Einfacher ReAct-Prompt
                from langchain.prompts import PromptTemplate
                template = """Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought:{agent_scratchpad}"""
                
                prompt = PromptTemplate.from_template(template)
            
            # Agent erstellen
            agent = create_react_agent(self.llm, tools, prompt)
            
            # Agent Executor erstellen
            agent_executor = AgentExecutor(
                agent=agent,
                tools=tools,
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=10,
                callbacks=[self.callback_handler],
                return_intermediate_steps=True
            )
            
            return agent_executor
            
        except Exception as e:
            print(f"Error initializing Direct FDB SQL Agent: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _load_and_parse_documentation(
        self,
        schema_path: str = "output/schema",
        yamls_path: str = "output/yamls", 
        ddl_path: str = "output/ddl"
    ) -> List[Document]:
        """Lädt und parst Dokumentation aus den angegebenen Verzeichnissen."""
        all_documents: List[Document] = []
        doc_id_counter = 1
        MAX_DOC_CONTENT_LENGTH = 1500
        
        print(f"Loading documentation in mode: {self.doc_mode}")
        
        # Markdown-Dateien laden (nur wenn erlaubt)
        if self.doc_mode in ['all', 'markdown_only']:
            print(f"Loading markdown files from {schema_path}")
            for md_file_path in glob.glob(os.path.join(schema_path, "*.md")):
                try:
                    with open(md_file_path, 'r', encoding='utf-8') as f:
                        content = f.read()[:MAX_DOC_CONTENT_LENGTH]
                    file_name = os.path.basename(md_file_path)
                    metadata = {"source": file_name, "type": "schema_markdown", "path": md_file_path, "doc_id": f"doc_{doc_id_counter}"}
                    all_documents.append(Document(page_content=content, metadata=metadata))
                    doc_id_counter += 1
                except Exception as e:
                    print(f"Error reading Markdown file {md_file_path}: {e}")
        else:
            print("Skipping markdown files per doc_mode setting")
        
        # YAML-Dateien laden (nur wenn erlaubt)
        if self.doc_mode in ['all', 'yaml_only']:
            print(f"Loading YAML files from {yamls_path}")
            for yaml_file_path in glob.glob(os.path.join(yamls_path, "*.yaml")):
                try:
                    with open(yaml_file_path, 'r', encoding='utf-8') as f:
                        data = yaml.safe_load(f)
                    file_name = os.path.basename(yaml_file_path)
                    
                    content_parts = [f"Source YAML: {file_name}"]
                    if isinstance(data, dict):
                        table_name = data.get('table_name', data.get('name', file_name.replace('.yaml', '')))
                        content_parts.append(f"Entity Name: {table_name}")
                        description = data.get('description', 'N/A')
                        content_parts.append(f"Description: {description}")
                        
                        if 'columns' in data and isinstance(data['columns'], list):
                            content_parts.append("Columns:")
                            for col in data['columns']:
                                if isinstance(col, dict):
                                    col_name = col.get('name', 'N/A')
                                    col_type = col.get('type', 'N/A')
                                    # Enhanced: Include business context from common_queries
                                    col_queries = col.get('common_queries', [])
                                    if col_queries:
                                        col_desc = f"Business context: {col_queries[0]}"
                                    else:
                                        col_desc = col.get('description', 'N/A')
                                    content_parts.append(f"  - {col_name} (Type: {col_type}): {col_desc}")
                        
                        if 'relations' in data and isinstance(data['relations'], list):
                            content_parts.append("Relations:")
                            for rel in data['relations']:
                                content_parts.append(f"  - {rel}")
                    
                    page_content = "\n".join(content_parts)[:MAX_DOC_CONTENT_LENGTH]
                    metadata = {"source": file_name, "type": "yaml_definition", "path": yaml_file_path, "doc_id": f"doc_{doc_id_counter}"}
                    all_documents.append(Document(page_content=page_content, metadata=metadata))
                    doc_id_counter += 1
                except Exception as e:
                    print(f"Error reading YAML file {yaml_file_path}: {e}")
        else:
            print("Skipping YAML files per doc_mode setting")
        
        # SQL DDL-Dateien laden (nur wenn erlaubt)
        if self.doc_mode in ['all', 'yaml_only']:  # DDL goes with YAML since they have structural info
            print(f"Loading DDL files from {ddl_path}")
            for sql_file_path in glob.glob(os.path.join(ddl_path, "*.sql")):
                try:
                    with open(sql_file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    file_name = os.path.basename(sql_file_path)
                    entity_type = "procedure_ddl" if "procedure" in file_name.lower() else "table_ddl"
                    metadata = {"source": file_name, "type": entity_type, "path": sql_file_path, "doc_id": f"doc_{doc_id_counter}"}
                    page_content = f"DDL script for {file_name}:\n```sql\n{content}\n```"[:MAX_DOC_CONTENT_LENGTH]
                    all_documents.append(Document(page_content=page_content, metadata=metadata))
                    doc_id_counter += 1
                except Exception as e:
                    print(f"Error reading SQL file {sql_file_path}: {e}")
        else:
            print("Skipping DDL files per doc_mode setting")
        
        print(f"Loaded {len(all_documents)} documents.")
        return all_documents
    
    def query(self, natural_language_query: str, retrieval_mode_override: Optional[str] = None) -> Dict[str, Any]:
        """
        Verarbeitet eine natürlichsprachliche Abfrage mit optionaler Vorverarbeitung.
        
        Args:
            natural_language_query: Die zu verarbeitende Abfrage
            retrieval_mode_override: Optionale Überschreibung des Retrieval-Modus
            
        Returns:
            Dictionary mit Abfrageergebnissen
        """
        if not self.sql_agent:
            return {"error": "SQL Agent is not initialized."}
        
        current_retrieval_mode = retrieval_mode_override if retrieval_mode_override else self.retrieval_mode
        
        # Start Phoenix monitoring for this query
        monitor = get_monitor(enable_ui=False)
        query_start_time = time.time()
        
        # Query Preprocessing (falls aktiviert)
        preprocessing_info = {}
        if self.use_enhanced_knowledge and self.query_preprocessor:
            print(f"Preprocessing query: \"{natural_language_query}\"")
            preprocessing_info = self.query_preprocessor.preprocess_query(natural_language_query)
            print(f"Identified tables: {preprocessing_info.get('tables', [])}")
            print(f"Query intent: {preprocessing_info.get('intent', {}).get('type', 'unknown')}")
            if preprocessing_info.get('suggestions'):
                print(f"Suggestions: {preprocessing_info['suggestions']}")
        
        # Dokumentationskontext abrufen
        doc_context_str = ""
        retrieved_docs: List[Document] = []
        
        # Wähle den aktiven Retriever basierend auf dem Modus
        active_retriever = None
        if current_retrieval_mode == 'faiss' and self.faiss_retriever:
            active_retriever = self.faiss_retriever
            print(f"Using {'Enhanced' if self.use_enhanced_knowledge else 'Standard'} FAISS retriever")
        elif current_retrieval_mode == 'enhanced' and self.enhanced_retriever:
            active_retriever = self.enhanced_retriever
            print("Using Enhanced Multi-Stage retriever")
        elif current_retrieval_mode == 'neo4j' and self.neo4j_retriever:
            active_retriever = self.neo4j_retriever
            print("Using Neo4j retriever")
        else:
            active_retriever = self.active_retriever
        
        if active_retriever:
            print(f"Retrieving context for query: \"{natural_language_query}\"")
            retrieval_start = time.time()
            try:
                retrieved_docs = active_retriever.get_relevant_documents(natural_language_query)
                retrieval_duration = time.time() - retrieval_start
                
                # Track retrieval in Phoenix
                relevance_scores = []
                for doc in retrieved_docs:
                    # Extract relevance score if available in metadata
                    score = doc.metadata.get('score', 1.0)
                    relevance_scores.append(float(score) if score else 1.0)
                
                monitor.track_retrieval(
                    retrieval_mode=current_retrieval_mode,
                    query=natural_language_query,
                    documents_retrieved=len(retrieved_docs),
                    relevance_scores=relevance_scores,
                    duration=retrieval_duration,
                    success=True
                )
            except Exception as e:
                print(f"Error during retrieval: {e}")
                monitor.track_retrieval(
                    retrieval_mode=current_retrieval_mode,
                    query=natural_language_query,
                    documents_retrieved=0,
                    relevance_scores=[],
                    duration=time.time() - retrieval_start,
                    success=False
                )
                retrieved_docs = []
        
        if retrieved_docs:
            doc_context_str = "\n\n".join([f"--- Source: {doc.metadata.get('source', 'N/A')} ---\n{doc.page_content}" for doc in retrieved_docs])
            print(f"Retrieved context ({len(retrieved_docs)} docs):\n{doc_context_str[:500]}...")
        else:
            print("No relevant documentation context found.")
        
        # Erweiterte Abfrage für den Agent mit Preprocessing-Informationen
        query_to_send = natural_language_query
        if preprocessing_info and preprocessing_info.get('enriched_query'):
            query_to_send = preprocessing_info['enriched_query']
        
        enhanced_query_for_agent = f"""
Basierend auf dem folgenden Dokumentationskontext:
--- START OF CONTEXT ---
{doc_context_str if doc_context_str else "Kein spezifischer Kontext abgerufen."}
--- END OF CONTEXT ---

{f"Zusätzliche Hinweise: {', '.join(preprocessing_info.get('suggestions', []))}" if preprocessing_info.get('suggestions') else ""}

Bitte beantworte die folgende Frage: {query_to_send}
"""
        
        print(f"\nSending to Direct FDB SQL agent:\nUser Query: {natural_language_query}\nEnhanced with context (first 200 chars): {doc_context_str[:200] if doc_context_str else 'N/A'}")
        
        try:
            self.callback_handler.clear_log()
            
            # Wrap agent execution with Phoenix tracing
            with trace_query(natural_language_query, {
                "retrieval_mode": current_retrieval_mode,
                "documents_retrieved": len(retrieved_docs) if retrieved_docs else 0
            }) as trace_ctx:
                # Agent ausführen
                agent_start_time = time.time()
                agent_response_dict = self.sql_agent.invoke({"input": enhanced_query_for_agent})
                agent_execution_time = time.time() - agent_start_time
                agent_final_answer = agent_response_dict.get("output", "No output from agent.")
            
            # SQL aus dem Callback Handler abrufen
            generated_sql = self.callback_handler.sql_query
            detailed_steps = self.callback_handler.full_log
            
            if not generated_sql:
                # Versuche SQL aus den detaillierten Schritten zu extrahieren
                for log_entry in reversed(detailed_steps):
                    action_data = log_entry.get("action")
                    if action_data and action_data.get("tool") == "fdb_query":
                        tool_input = action_data.get("tool_input")
                        if isinstance(tool_input, str):
                            generated_sql = tool_input
                            break
                        elif isinstance(tool_input, dict) and 'query' in tool_input:
                            generated_sql = tool_input['query']
                            break
            
            if not generated_sql:
                generated_sql = "SQL_QUERY_NOT_EXTRACTED_BY_CALLBACK"
                print("Warning: SQL query could not be extracted via callback.")
            else:
                print(f"SQL extracted: {generated_sql}")
            
            print(f"Agent Final Answer: {agent_final_answer}")
            
            # Textuelle Antworten generieren
            text_responses = self._generate_textual_responses(
                natural_language_query=natural_language_query,
                retrieved_context=doc_context_str,
                agent_final_answer=agent_final_answer,
                generated_sql=generated_sql
            )
            
            # Track complete query execution
            total_execution_time = time.time() - query_start_time
            monitor.track_query_execution(
                query=natural_language_query,
                sql=generated_sql if generated_sql else "N/A",
                execution_time=total_execution_time,
                rows_returned=-1,  # We don't have row count at this level
                success=True
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
            print(f"Error during Direct FDB SQL agent execution: {e}")
            import traceback
            traceback.print_exc()
            
            # Track failed query execution
            total_execution_time = time.time() - query_start_time
            monitor.track_query_execution(
                query=natural_language_query,
                sql="N/A",
                execution_time=total_execution_time,
                rows_returned=0,
                success=False,
                error=str(e)
            )
            
            error_text_variants = [
                {"variant_name": "Error Variant 1", "text": f"Direct FDB SQL Agent execution failed: {e}"},
                {"variant_name": "Error Variant 2", "text": "The system could not process the request with the direct FDB agent."},
                {"variant_name": "Error Variant 3", "text": "Please try rephrasing or check logs for direct FDB agent errors."}
            ]
            
            return {
                "natural_language_query": natural_language_query,
                "retrieved_context": doc_context_str,
                "agent_final_answer": None,
                "generated_sql": None,
                "text_variants": error_text_variants,
                "detailed_steps": self.callback_handler.full_log if hasattr(self, 'callback_handler') else [],
                "error": str(e)
            }
    
    def _generate_textual_responses(self,
                                   natural_language_query: str,
                                   retrieved_context: str,
                                   agent_final_answer: Optional[str],
                                   generated_sql: Optional[str]) -> List[Dict[str, str]]:
        """
        Generiert drei verschiedene textuelle Antwortvarianten basierend auf den Agent-Ergebnissen.
        """
        if not self.llm:
            print("Error: LLM is not set. Cannot generate textual responses.")
            return [{"variant_name": "Error", "text": "LLM not available."}]

        if agent_final_answer is None and generated_sql is None:
            return [
                {"variant_name": "Error Variant", "text": "The Direct FDB SQL agent failed to produce a response or SQL query."},
                {"variant_name": "Suggestion Variant", "text": "Could you try rephrasing your question? The system was unable to process it."},
                {"variant_name": "Contextual Suggestion", "text": f"Based on your query '{natural_language_query}', the system couldn't find a direct answer. You might want to explore related topics in the documentation."}
            ]

        # Fallback für MagicMock oder wenn LLM nicht verfügbar
        if isinstance(self.llm, MagicMock) or not hasattr(self.llm, 'invoke'):
            print("LLM is a MagicMock or does not have 'invoke'. Generating placeholder responses.")
            return [
                {"variant_name": "Placeholder Basic", "text": f"Query: {natural_language_query}\nSQL: {generated_sql}\nAnswer: {agent_final_answer}"},
                {"variant_name": "Placeholder Detailed", "text": f"For your question '{natural_language_query}', the system generated the SQL query '{generated_sql}' and found the answer: {agent_final_answer}. Context used: {retrieved_context[:100]}..."},
                {"variant_name": "Placeholder Summary", "text": f"The answer to '{natural_language_query}' is {agent_final_answer}."}
            ]

        # Prompts für die drei Varianten
        prompt_template_1 = f"""
        Original Question: {natural_language_query}
        Retrieved Documentation Context:
        {retrieved_context if retrieved_context else "No specific documentation context was retrieved."}
        ---
        Generated SQL Query (if available): {generated_sql if generated_sql else "Not available or not applicable."}
        ---
        Final Answer from Direct FDB SQL Agent: {agent_final_answer if agent_final_answer else "No answer was produced by the agent."}
        ---
        Based on all the information above, provide a concise, direct answer to the original question.
        Focus on the 'Final Answer from Direct FDB SQL Agent'. If the agent's answer is sufficient, use it directly.
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
        Final Answer from Direct FDB SQL Agent: {agent_final_answer if agent_final_answer else "No answer was produced by the agent."}
        ---
        Provide a more detailed explanation.
        Start by stating the answer derived from the 'Final Answer from Direct FDB SQL Agent'.
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
        Final Answer from Direct FDB SQL Agent: {agent_final_answer if agent_final_answer else "No answer was produced by the agent."}
        ---
        Provide a very brief, executive-summary style answer to the original question.
        This should be a single sentence if possible, directly addressing the user's query based on the 'Final Answer from Direct FDB SQL Agent'.
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
                if hasattr(self.llm, 'invoke'):
                    from langchain_core.messages import HumanMessage
                    message = HumanMessage(content=prompt_content)
                    response_content = self.llm.invoke([message]).content
                elif hasattr(self.llm, 'generate'):
                    response_content = self.llm.generate([prompt_content]).generations[0][0].text
                else:
                    response_content = "LLM does not support .invoke or .generate."
                
                responses.append({"variant_name": variant_name, "text": str(response_content)})
            except Exception as e:
                print(f"Error generating text variant '{variant_name}' with LLM: {e}")
                responses.append({"variant_name": variant_name, "text": f"Error generating response: {e}"})
        
        return responses


# --- Main execution / Test section ---
if __name__ == "__main__":
    import shutil
    
    # Konfiguration für Tests
    DB_CONNECTION_STRING = "firebird+fdb://sysdba:masterkey@//home/projects/langchain_project/WINCASA2022.FDB"
    TEST_LLM_MODEL_NAME = "openai/gpt-4.1-nano"
    
    # Dummy-Dokumentation erstellen
    dummy_schema_path = "output_dummy_direct/schema"
    dummy_yamls_path = "output_dummy_direct/yamls"
    dummy_ddl_path = "output_dummy_direct/ddl"
    
    os.makedirs(dummy_schema_path, exist_ok=True)
    os.makedirs(dummy_yamls_path, exist_ok=True)
    os.makedirs(dummy_ddl_path, exist_ok=True)

    with open(os.path.join(dummy_schema_path, "index.md"), "w", encoding="utf-8") as f:
        f.write("# Main Schema\nThis is the main schema document for direct FDB testing.")
    
    # Dummy YAML für BEWOHNER-Tabelle
    dummy_bewohner_yaml = {
        "name": "BEWOHNER",
        "description": "Tabelle für Bewohner-Informationen.",
        "columns": [
            {"name": "ID", "type": "INTEGER", "description": "Primärschlüssel"},
            {"name": "NAME", "type": "VARCHAR(100)", "description": "Name des Bewohners"},
            {"name": "VORNAME", "type": "VARCHAR(100)", "description": "Vorname des Bewohners"}
        ],
        "relations": []
    }
    with open(os.path.join(dummy_yamls_path, "bewohner.yaml"), "w", encoding="utf-8") as f:
        yaml.dump(dummy_bewohner_yaml, f)

    with open(os.path.join(dummy_ddl_path, "create_bewohner.sql"), "w", encoding="utf-8") as f:
        f.write("CREATE TABLE BEWOHNER (ID INTEGER PRIMARY KEY, NAME VARCHAR(100), VORNAME VARCHAR(100));")

    # Backup-Map für Cleanup
    backup_map = {}
    
    def setup_symlinks_or_moves(default_path, dummy_source_path, target_link_name, backup_mapping):
        """Setup-Funktion für Test-Umgebung."""
        backup_suffix = "_roo_backup_direct"
        
        if os.path.exists(target_link_name):
            if os.path.islink(target_link_name):
                print(f"Removing existing symlink: {target_link_name}")
                os.unlink(target_link_name)
            else:
                backup_location = target_link_name + backup_suffix
                print(f"Backing up existing '{target_link_name}' to '{backup_location}'")
                if os.path.exists(backup_location):
                    shutil.rmtree(backup_location)
                os.rename(target_link_name, backup_location)
                backup_mapping[target_link_name] = backup_location
        
        try:
            os.symlink(os.path.abspath(dummy_source_path), os.path.abspath(target_link_name), target_is_directory=True)
            print(f"Symlinked '{dummy_source_path}' to '{target_link_name}'")
        except OSError as e:
            print(f"Symlink creation failed: {e}. Falling back to copy.")
            try:
                shutil.copytree(dummy_source_path, target_link_name)
                print(f"Copied '{dummy_source_path}' to '{target_link_name}' as fallback.")
                backup_mapping[target_link_name] = "copied_dummy"
            except Exception as move_e:
                print(f"Fallback copy also failed: {move_e}")
                raise

    # Test ausführen
    agent = None
    try:
        # Setup: Dummy 'output_dummy_direct' als 'output' verwenden
        setup_symlinks_or_moves(
            "output",
            "output_dummy_direct",
            "output",
            backup_map
        )

        print(f"\nInitializing FirebirdDirectSQLAgent with DB: {DB_CONNECTION_STRING} and LLM: {TEST_LLM_MODEL_NAME}")
        
        # Agent initialisieren
        agent = FirebirdDirectSQLAgent(
            db_connection_string=DB_CONNECTION_STRING,
            llm=TEST_LLM_MODEL_NAME,
            retrieval_mode='faiss'
        )

        if agent and agent.sql_agent:
            print("\nDirect FDB Agent initialized successfully.")
            
            # Test-Abfragen
            test_queries = [
                "Zeige mir die ersten 5 Bewohner.",
                "Welche Spalten hat die Tabelle BEWOHNER?",
                "Wie viele Bewohner gibt es insgesamt?"
            ]
            
            for i, test_query in enumerate(test_queries, 1):
                print(f"\n--- Running Test Query {i}: \"{test_query}\" ---")
                response = agent.query(test_query)
                
                print(f"\nResponse for Query {i}:")
                print(f"  Natural Language Query: {response.get('natural_language_query')}")
                print(f"  Generated SQL: {response.get('generated_sql')}")
                print(f"  Agent Final Answer: {response.get('agent_final_answer')}")
                
                if response.get("text_variants"):
                    for j, variant in enumerate(response["text_variants"]):
                        print(f"  Text Variant {j+1} ({variant.get('variant_name')}):\n    {variant.get('text')}")
                
                if response.get('detailed_steps'):
                    print(f"\n  Detailed Steps (Query {i}):")
                    for entry_idx, entry in enumerate(response['detailed_steps']):
                        action_data = entry.get('action', {})
                        observation = entry.get('observation', entry.get('error', 'N/A'))
                        print(f"    Step {entry_idx + 1}:")
                        print(f"      Tool: {action_data.get('tool')}")
                        print(f"      Tool Input: {action_data.get('tool_input')}")
                        print(f"      Observation/Error: {str(observation)[:300]}...")
                
                if response.get('error'):
                    print(f"  Error: {response.get('error')}")
        else:
            print("\nDirect FDB Agent initialization failed. Check logs.")

    except Exception as e:
        print(f"\nAn error occurred during the direct FDB test: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Cleanup
        print("\n--- Cleaning up dummy files and restoring original 'output' directory ---")
        
        if os.path.islink("output"):
            print("Removing symlink: output")
            os.unlink("output")
        elif backup_map.get("output") == "copied_dummy":
            print("Removing copied dummy directory: output")
            if os.path.exists("output"):
                shutil.rmtree("output")
        
        backed_up_original_output = backup_map.get("output")
        if backed_up_original_output and backed_up_original_output != "copied_dummy":
            if os.path.exists(backed_up_original_output):
                print(f"Restoring original 'output' from '{backed_up_original_output}'")
                os.rename(backed_up_original_output, "output")
            else:
                print(f"Warning: Backup '{backed_up_original_output}' not found. Cannot restore.")
        
        if os.path.exists("output_dummy_direct"):
            print("Removing main dummy directory: output_dummy_direct")
            shutil.rmtree("output_dummy_direct")
        
        print("Direct FDB test cleanup complete.")