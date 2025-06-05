import os
import unittest
from typing import Any, Dict, List
from unittest.mock import MagicMock, mock_open, patch

import yaml  # type: ignore

# Assuming firebird_sql_agent.py and retrievers.py are in the same directory or python path
from firebird_sql_agent import FirebirdDocumentedSQLAgent
from langchain_core.documents import Document

# We might need to mock OpenAIEmbeddings and other Langchain components later


# Dummy LLM for testing purposes
class DummyLLM:
    def invoke(self, prompt: str) -> str:
        if (
            "Variant 1 Text:" in prompt
        ):  # Mocking response for _generate_textual_responses
            return """
            Variant 1 Text: This is a concise dummy answer.
            Variant 2 Text: This is a more detailed dummy answer based on context.
            Variant 3 Text: For more info, ask about dummy follow-up.
            """
        return "Dummy LLM response to: " + prompt[:50]  # For SQL agent or other calls

    def __call__(self, prompt: str) -> str:  # for older langchain versions
        return self.invoke(prompt)


class TestFirebirdDocumentedSQLAgent(unittest.TestCase):

    def setUp(self):
        # Basic LLM mock - can be enhanced
        self.mock_llm = DummyLLM()
        # Mock DB connection string (not actually connecting)
        self.mock_db_conn_str = (
            "firebird+fdb://dummy_user:dummy_password@localhost:3050/dummy.fdb"
        )

    @patch("glob.glob")
    @patch("builtins.open", new_callable=mock_open)
    @patch("os.path.basename")
    def test_load_and_parse_documentation_success(
        self, mock_basename, mock_open_file, mock_glob
    ):
        # --- Setup Mocks ---
        # Mock glob to return specific file paths for each category
        def glob_side_effect(pattern):
            if "output/schema/*.md" in pattern:
                return ["output/schema/index.md", "output/schema/tableA.md"]
            elif "output/yamls/*.yaml" in pattern:
                return ["output/yamls/tableA.yaml", "output/yamls/procB.yaml"]
            elif "output/ddl/*.sql" in pattern:
                return ["output/ddl/tableA_ddl.sql", "output/ddl/procB_procedure.sql"]
            return []

        mock_glob.side_effect = glob_side_effect

        # Mock os.path.basename
        def basename_side_effect(path):
            return path.split("/")[-1]

        mock_basename.side_effect = basename_side_effect

        # Mock file contents
        mock_schema_index_content = "# Main Index\nContent for index."
        mock_schema_tableA_content = "## Table A\nDetails about Table A."
        mock_yaml_tableA_content = yaml.dump(
            {
                "name": "TABLE_A_FROM_YAML",
                "description": "YAML description for Table A.",
                "columns": [
                    {"name": "id", "type": "INTEGER", "description": "Primary key"}
                ],
                "relations": ["Related to TABLE_B"],
            }
        )
        mock_yaml_procB_content = yaml.dump(
            {
                "name": "PROC_B_FROM_YAML",
                "description": "YAML description for Procedure B.",
                "parameters": [{"name": "param1", "type": "VARCHAR"}],
            }
        )
        mock_ddl_tableA_content = "CREATE TABLE TABLE_A_DDL (id INTEGER);"
        mock_ddl_procB_content = (
            "CREATE PROCEDURE PROC_B_DDL (param1 VARCHAR(10)) AS BEGIN ... END;"
        )

        def open_side_effect(path, *args, **kwargs):
            if path == "output/schema/index.md":
                return mock_open(read_data=mock_schema_index_content).return_value
            elif path == "output/schema/tableA.md":
                return mock_open(read_data=mock_schema_tableA_content).return_value
            elif path == "output/yamls/tableA.yaml":
                return mock_open(read_data=mock_yaml_tableA_content).return_value
            elif path == "output/yamls/procB.yaml":
                return mock_open(read_data=mock_yaml_procB_content).return_value
            elif path == "output/ddl/tableA_ddl.sql":
                return mock_open(read_data=mock_ddl_tableA_content).return_value
            elif path == "output/ddl/procB_procedure.sql":
                return mock_open(read_data=mock_ddl_procB_content).return_value
            raise FileNotFoundError(f"File not found in mock: {path}")

        mock_open_file.side_effect = open_side_effect

        # --- Instantiate Agent (only uses _load_and_parse_documentation for this test) ---
        # We pass None for LLM and db_connection_string as they are not used by the tested method directly
        # and OpenAIEmbeddings is initialized inside the agent.
        # For a more isolated test of _load_and_parse_documentation, we could make it static
        # or call it on a partially initialized object.
        with patch.object(
            FirebirdDocumentedSQLAgent, "_initialize_components", lambda self: None
        ):  # Prevent full init
            agent = FirebirdDocumentedSQLAgent(
                db_connection_string=self.mock_db_conn_str, llm=self.mock_llm
            )
            # The _load_and_parse_documentation is called in __init__
            parsed_docs = agent.parsed_docs

        # --- Assertions ---
        self.assertEqual(len(parsed_docs), 6)  # 2 MD, 2 YAML, 2 SQL

        # Check content and metadata of a sample from each type
        # MD
        doc_index_md = next(
            d for d in parsed_docs if d.metadata["source"] == "index.md"
        )
        self.assertIn("# Main Index", doc_index_md.page_content)
        self.assertEqual(doc_index_md.metadata["type"], "schema_markdown")

        # YAML (Table)
        doc_yaml_tableA = next(
            d for d in parsed_docs if d.metadata["source"] == "tableA.yaml"
        )
        self.assertIn("Entity Name: TABLE_A_FROM_YAML", doc_yaml_tableA.page_content)
        self.assertIn("Primary key", doc_yaml_tableA.page_content)
        self.assertIn("Related to TABLE_B", doc_yaml_tableA.page_content)
        self.assertEqual(doc_yaml_tableA.metadata["type"], "yaml_definition")

        # YAML (Procedure)
        doc_yaml_procB = next(
            d for d in parsed_docs if d.metadata["source"] == "procB.yaml"
        )
        self.assertIn("Entity Name: PROC_B_FROM_YAML", doc_yaml_procB.page_content)
        self.assertIn(
            "param1", doc_yaml_procB.page_content
        )  # Check if parameters are mentioned
        self.assertEqual(doc_yaml_procB.metadata["type"], "yaml_definition")

        # SQL (Table DDL)
        doc_ddl_tableA = next(
            d for d in parsed_docs if d.metadata["source"] == "tableA_ddl.sql"
        )
        self.assertIn("CREATE TABLE TABLE_A_DDL", doc_ddl_tableA.page_content)
        self.assertEqual(doc_ddl_tableA.metadata["type"], "table_ddl")

        # SQL (Procedure DDL)
        doc_ddl_procB = next(
            d for d in parsed_docs if d.metadata["source"] == "procB_procedure.sql"
        )
        self.assertIn("CREATE PROCEDURE PROC_B_DDL", doc_ddl_procB.page_content)
        self.assertEqual(doc_ddl_procB.metadata["type"], "procedure_ddl")

        # Check unique doc_id
        doc_ids = [d.metadata["doc_id"] for d in parsed_docs]
        self.assertEqual(
            len(doc_ids), len(set(doc_ids)), "Document IDs should be unique"
        )

    @patch("firebird_sql_agent.FaissDocumentationRetriever")
    @patch("firebird_sql_agent.OpenAIEmbeddings")
    def test_initialize_components_faiss_mode(
        self, MockOpenAIEmbeddings, MockFaissDocumentationRetriever
    ):
        # Setup Mocks
        mock_faiss_retriever_instance = MockFaissDocumentationRetriever.return_value
        MockOpenAIEmbeddings.return_value = (
            MagicMock()
        )  # Mock OpenAIEmbeddings instance

        # Instantiate Agent with FAISS mode
        # We need to patch _load_and_parse_documentation or ensure it runs without error
        # For simplicity, let's assume parsed_docs is populated or mock it.
        with patch.object(
            FirebirdDocumentedSQLAgent,
            "_load_and_parse_documentation",
            lambda self: setattr(self, "parsed_docs", [Document(page_content="doc1")]),
        ):
            agent = FirebirdDocumentedSQLAgent(
                db_connection_string=self.mock_db_conn_str,
                llm=self.mock_llm,
                retrieval_mode="faiss",
            )

        # Assertions
        MockFaissDocumentationRetriever.assert_called_once_with(
            documents=[Document(page_content="doc1")],
            embeddings_model=MockOpenAIEmbeddings.return_value,
            # Add other expected args for FaissDocumentationRetriever if any
        )
        self.assertIs(agent.faiss_retriever, mock_faiss_retriever_instance)
        self.assertIs(agent.active_retriever, mock_faiss_retriever_instance)
        self.assertIsNone(agent.neo4j_retriever)
        self.assertEqual(agent.retrieval_mode, "faiss")

    def test_initialize_components_unknown_mode(self):
        with patch.object(
            FirebirdDocumentedSQLAgent,
            "_load_and_parse_documentation",
            lambda self: setattr(self, "parsed_docs", [Document(page_content="doc1")]),
        ):
            with self.assertRaises(ValueError) as context:
                FirebirdDocumentedSQLAgent(
                    db_connection_string=self.mock_db_conn_str,
                    llm=self.mock_llm,
                    retrieval_mode="unknown_mode",  # Invalid mode
                )
        self.assertIn("Unsupported retrieval_mode", str(context.exception))
        self.assertIn("unknown_mode", str(context.exception))

    @patch("firebird_sql_agent.create_sql_agent")
    @patch("firebird_sql_agent.SQLDatabaseToolkit")
    @patch("firebird_sql_agent.SQLDatabase")
    def test_setup_sql_agent_success(
        self, MockSQLDatabase, MockSQLDatabaseToolkit, MockCreateSqlAgent
    ):
        # Setup Mocks
        mock_db_instance = MockSQLDatabase.return_value
        mock_toolkit_instance = MockSQLDatabaseToolkit.return_value
        mock_sql_agent_instance = MockCreateSqlAgent.return_value

        # Mock an LLM instance if not using self.mock_llm directly in the agent's _setup_sql_agent
        # self.mock_llm is already a DummyLLM, which should be fine.

        # Instantiate Agent
        # We need to patch _load_and_parse_documentation and _initialize_components
        # to isolate the _setup_sql_agent call which happens during __init__.
        with patch.object(
            FirebirdDocumentedSQLAgent,
            "_load_and_parse_documentation",
            lambda self: setattr(self, "parsed_docs", [Document(page_content="doc1")]),
        ):
            with patch.object(
                FirebirdDocumentedSQLAgent, "_initialize_components", lambda self: None
            ):  # Prevent retriever init
                agent = FirebirdDocumentedSQLAgent(
                    db_connection_string=self.mock_db_conn_str,
                    llm=self.mock_llm,  # This LLM will be passed to _setup_sql_agent
                )
                # _setup_sql_agent is called within __init__ after the patched methods

        # Assertions
        MockSQLDatabase.assert_called_once_with(
            self.mock_db_conn_str,
            engine_args={
                "connect_args": {"timeout": 30}
            },  # Check for specific engine_args if any
            # Add other expected args for SQLDatabase if any
            # e.g. sample_rows_in_table_info, include_tables, etc.
            # Based on firebird_sql_agent.py, these are the defaults:
            sample_rows_in_table_info=3,
            include_tables=[],  # Assuming it's not using include_tables initially
            custom_table_info={},
        )

        MockSQLDatabaseToolkit.assert_called_once_with(
            db=mock_db_instance, llm=self.mock_llm
        )

        # Check that create_sql_agent was called.
        # We need to check the agent_executor_kwargs and system_message (prefix)
        # For the prefix, we can check if it contains key phrases.
        args, kwargs = MockCreateSqlAgent.call_args
        self.assertIs(args[0], mock_toolkit_instance)  # First arg is toolkit
        self.assertIs(args[1], self.mock_llm)  # Second arg is llm
        self.assertIn(
            "You are an agent designed to interact with a Firebird SQL database",
            kwargs.get("prefix", ""),
        )
        self.assertIn(
            "WINCASA2022", kwargs.get("prefix", "")
        )  # Check for specific context words
        self.assertTrue(
            kwargs.get("verbose", False)
        )  # or check its actual value if set
        # Check agent_executor_kwargs if specific ones are set
        self.assertEqual(
            kwargs.get("agent_executor_kwargs", {}).get("handle_parsing_errors"), True
        )

        self.assertIs(agent.sql_agent, mock_sql_agent_instance)

    # TODO: Add more tests for other methods:
    # - test_initialize_components_neo4j_mode (mock Neo4jDocumentationRetriever - later)

    @patch("firebird_sql_agent.create_sql_agent")
    @patch("firebird_sql_agent.SQLDatabaseToolkit")
    @patch("firebird_sql_agent.SQLDatabase")
    @patch("logging.warning")  # To check for the warning log
    def test_setup_sql_agent_no_db_conn(
        self,
        mock_log_warning,
        MockSQLDatabase,
        MockSQLDatabaseToolkit,
        MockCreateSqlAgent,
    ):
        # Instantiate Agent with no db_connection_string
        with patch.object(
            FirebirdDocumentedSQLAgent,
            "_load_and_parse_documentation",
            lambda self: setattr(self, "parsed_docs", [Document(page_content="doc1")]),
        ):
            with patch.object(
                FirebirdDocumentedSQLAgent, "_initialize_components", lambda self: None
            ):  # Prevent retriever init
                agent = FirebirdDocumentedSQLAgent(
                    db_connection_string=None, llm=self.mock_llm  # No DB connection
                )

        # Assertions
        self.assertIsNone(agent.sql_agent)
        MockSQLDatabase.assert_not_called()
        MockSQLDatabaseToolkit.assert_not_called()
        MockCreateSqlAgent.assert_not_called()
        mock_log_warning.assert_called_with(
            "SQL Agent not created due to missing DB connection string or LLM."
        )

    @patch("firebird_sql_agent.create_sql_agent")
    @patch("firebird_sql_agent.SQLDatabaseToolkit")
    @patch("firebird_sql_agent.SQLDatabase")
    @patch("logging.warning")  # To check for the warning log
    def test_setup_sql_agent_no_llm(
        self,
        mock_log_warning,
        MockSQLDatabase,
        MockSQLDatabaseToolkit,
        MockCreateSqlAgent,
    ):
        # Instantiate Agent with no llm
        with patch.object(
            FirebirdDocumentedSQLAgent,
            "_load_and_parse_documentation",
            lambda self: setattr(self, "parsed_docs", [Document(page_content="doc1")]),
        ):
            with patch.object(
                FirebirdDocumentedSQLAgent, "_initialize_components", lambda self: None
            ):  # Prevent retriever init
                agent = FirebirdDocumentedSQLAgent(
                    db_connection_string=self.mock_db_conn_str, llm=None  # No LLM
                )

        # Assertions
        self.assertIsNone(agent.sql_agent)
        MockSQLDatabase.assert_not_called()  # SQLDatabase might be called if db_conn_str is present, but toolkit and agent should not.
        # Let's refine: if LLM is None, toolkit creation should fail or be skipped.
        # Based on current code, SQLDatabase would be created, but toolkit/agent would not.
        # For a stricter test, we might expect SQLDatabase not to be called if LLM is essential for the whole setup.
        # However, the current warning message suggests it checks for *either* missing.
        # Let's assume the current logic: SQLDatabase might be init, but not toolkit/agent.
        # If the logic is that _setup_sql_agent bails early if no LLM, then SQLDatabase might not be called.
        # The current implementation of _setup_sql_agent checks for llm and db_conn_str *before* creating SQLDatabase.
        MockSQLDatabase.assert_not_called()
        MockSQLDatabaseToolkit.assert_not_called()
        MockCreateSqlAgent.assert_not_called()
        mock_log_warning.assert_called_with(
            "SQL Agent not created due to missing DB connection string or LLM."
        )

    @patch("firebird_sql_agent.create_sql_agent")
    @patch("firebird_sql_agent.SQLDatabaseToolkit")
    @patch("firebird_sql_agent.SQLDatabase")
    @patch("firebird_sql_agent.OpenAIEmbeddings")
    @patch("firebird_sql_agent.FaissDocumentationRetriever")
    def test_query_faiss_mode(
        self,
        MockFaissRetriever,
        MockOpenAIEmbeddings,
        MockSQLDatabase,
        MockSQLToolkit,
        MockCreateAgent,
    ):
        # --- Setup Mocks ---
        # Mock instances that will be created within the agent
        mock_faiss_retriever_instance = MockFaissRetriever.return_value
        mock_sql_agent_instance = MockCreateAgent.return_value

        # Mock the methods of these instances that will be called by the query() method
        mock_faiss_retriever_instance.get_relevant_documents.return_value = [
            Document(page_content="Context doc 1", metadata={"source": "doc1.md"}),
            Document(page_content="Context doc 2", metadata={"source": "doc2.yaml"}),
        ]
        # Simulate the output of sql_agent.invoke. It should be a dictionary.
        # The actual SQL might be in 'intermediate_steps' or part of a more complex output.
        # For this test, we assume 'output' contains the direct result, and we'll mock SQL extraction.
        mock_sql_agent_instance.invoke.return_value = {
            "output": "Dummy SQL Result from agent",
            "intermediate_steps": [
                ("some_action", "SELECT * FROM DUMMY_TABLE;")
            ],  # Example intermediate step
        }

        # --- Instantiate Agent ---
        # Patch _load_and_parse_documentation to provide dummy parsed_docs
        # The other necessary components (FaissRetriever, SQLAgent) are mocked above.
        with patch.object(
            FirebirdDocumentedSQLAgent,
            "_load_and_parse_documentation",
            lambda self: setattr(
                self, "parsed_docs", [Document(page_content="parsed_doc_content")]
            ),
        ):
            agent = FirebirdDocumentedSQLAgent(
                db_connection_string=self.mock_db_conn_str,
                llm=self.mock_llm,  # DummyLLM
                retrieval_mode="faiss",
            )

        # Ensure the mocked instances were assigned
        self.assertIs(agent.active_retriever, mock_faiss_retriever_instance)
        self.assertIs(agent.sql_agent, mock_sql_agent_instance)

        # Mock _generate_textual_responses as its internal logic is tested separately
        # It should return: sql_query, response1, response2, response3
        expected_sql = "SELECT * FROM DUMMY_TABLE;"
        expected_responses = (
            expected_sql,
            "Textual Response 1",
            "Textual Response 2",
            "Textual Response 3",
        )
        with patch.object(
            agent, "_generate_textual_responses", return_value=expected_responses
        ) as mock_generate_responses:
            # --- Call the query method ---
            nl_query = "Find all dummies."
            result_sql, result_r1, result_r2, result_r3 = agent.query(nl_query)

        # --- Assertions ---
        # 1. Check if retriever was called correctly
        mock_faiss_retriever_instance.get_relevant_documents.assert_called_once_with(
            nl_query
        )

        # 2. Check if SQL agent was invoked correctly
        #    The input to the agent should be the enhanced query.
        #    We need to reconstruct what the enhanced_query would look like.
        #    Format: "{context_str}\n\nHuman: {natural_language_query}"
        context_str = "\n\n".join(
            ["Source: doc1.md\nContext doc 1", "Source: doc2.yaml\nContext doc 2"]
        )
        expected_agent_input = f"{context_str}\n\nHuman: {nl_query}"

        mock_sql_agent_instance.invoke.assert_called_once()
        call_args = mock_sql_agent_instance.invoke.call_args[0][
            0
        ]  # Get the first positional argument (the dict)
        self.assertEqual(call_args["input"], expected_agent_input)
        self.assertEqual(call_args["chat_history"], [])

        # 3. Check if _generate_textual_responses was called correctly
        mock_generate_responses.assert_called_once_with(
            natural_language_query=nl_query,
            sql_agent_response=mock_sql_agent_instance.invoke.return_value,  # The raw response from the agent
            retrieved_context_str=context_str,
        )

        # 4. Check the final output of the query method
        self.assertEqual(result_sql, expected_sql)
        self.assertEqual(result_r1, "Textual Response 1")
        self.assertEqual(result_r2, "Textual Response 2")
        self.assertEqual(result_r3, "Textual Response 3")

    @patch("logging.error")  # To check for the error log
    def test_query_no_sql_agent(self, mock_log_error):
        # Instantiate Agent such that sql_agent is None (e.g., no db_conn_str)
        with patch.object(
            FirebirdDocumentedSQLAgent,
            "_load_and_parse_documentation",
            lambda self: setattr(self, "parsed_docs", [Document(page_content="doc1")]),
        ):
            # Patch _initialize_components to ensure active_retriever is set,
            # but sql_agent remains None because db_connection_string is None.
            # The retriever might still be initialized if retrieval_mode is valid.
            with patch.object(
                FirebirdDocumentedSQLAgent,
                "_initialize_components",
                lambda self: setattr(self, "active_retriever", MagicMock()),
            ):
                agent = FirebirdDocumentedSQLAgent(
                    db_connection_string=None,  # This will make self.sql_agent None
                    llm=self.mock_llm,
                    retrieval_mode="faiss",  # Still need a valid mode for retriever setup if not fully mocked
                )

        self.assertIsNone(agent.sql_agent)  # Verify precondition

        # Mock active_retriever's get_relevant_documents to ensure it's not called
        # agent.active_retriever is already a MagicMock from the patch above.
        # We also need to ensure _generate_textual_responses is not called.
        with patch.object(
            agent, "_generate_textual_responses"
        ) as mock_generate_responses:
            nl_query = "Some query"
            sql, r1, r2, r3 = agent.query(nl_query)

        # Assertions
        self.assertEqual(sql, "No SQL generated.")
        self.assertEqual(r1, "SQL Agent not available. Cannot process query.")
        self.assertEqual(r2, "Please check system configuration (DB connection, LLM).")
        self.assertEqual(r3, "-")  # Default empty response

        agent.active_retriever.get_relevant_documents.assert_not_called()
        mock_generate_responses.assert_not_called()
        mock_log_error.assert_called_with(
            "SQL Agent is not initialized. Cannot execute query."
        )

    def test_generate_textual_responses_success(self):
        # Instantiate Agent (some parts might not be fully needed if we only call the method)
        # For simplicity, create a basic agent instance.
        # The LLM used by _generate_textual_responses is self.llm.
        with patch.object(
            FirebirdDocumentedSQLAgent,
            "_load_and_parse_documentation",
            lambda self: None,
        ):
            with patch.object(
                FirebirdDocumentedSQLAgent, "_initialize_components", lambda self: None
            ):
                with patch.object(
                    FirebirdDocumentedSQLAgent, "_setup_sql_agent", lambda self: None
                ):
                    agent = FirebirdDocumentedSQLAgent(
                        db_connection_string=None, llm=self.mock_llm
                    )  # self.mock_llm is DummyLLM

        # Input data for _generate_textual_responses
        nl_query = "What is the dummy data?"
        # Simulate a successful agent response with intermediate steps for SQL extraction
        sql_agent_response = {
            "output": "Dummy SQL Result",
            "intermediate_steps": [
                ("Action", "Tool Input", "Log", "Tool Output"),  # Older format
                (
                    "some_action_step",
                    "Final Answer: Some answer based on SQL",
                ),  # if SQL is not directly in output
            ],
            "sql_query": (
                "SELECT DUMMY_COL FROM DUMMY_TABLE;"  # Assuming SQL is directly available or extracted
            ),
        }
        # For a more robust test, we should rely on the actual SQL extraction logic
        # if it's part of _generate_textual_responses or called before it.
        # The current _generate_textual_responses extracts SQL itself.
        # Let's adjust the mock_sql_agent_response to reflect what the method expects for SQL extraction.
        # The method tries to find SQL in 'intermediate_steps' then 'sql_query' then 'output'.

        # Scenario 1: SQL in intermediate_steps (as per current extraction logic)
        sql_agent_response_intermediate = {
            "output": "Some final answer.",
            "intermediate_steps": [
                (
                    "Action",
                    {"query": "SELECT * FROM DUMMY_INTERMEDIATE;"},
                ),  # Langchain AgentExecutor format
            ],
        }
        retrieved_context_str = "Some retrieved context."

        # Mock the LLM's invoke method for this specific call if DummyLLM isn't sufficient
        # self.mock_llm.invoke is already set up to return specific text for "Variant 1 Text:"

        # Call the method
        sql, r1, r2, r3 = agent._generate_textual_responses(
            natural_language_query=nl_query,
            sql_agent_response=sql_agent_response_intermediate,
            retrieved_context_str=retrieved_context_str,
        )

        # Assertions
        self.assertEqual(sql, "SELECT * FROM DUMMY_INTERMEDIATE;")
        self.assertEqual(r1, "This is a concise dummy answer.")
        self.assertEqual(r2, "This is a more detailed dummy answer based on context.")
        self.assertEqual(r3, "For more info, ask about dummy follow-up.")

        # Scenario 2: SQL in 'sql_query' field
        sql_agent_response_direct_sql = {
            "output": "Some final answer.",
            "sql_query": "SELECT * FROM DUMMY_DIRECT;",
        }
        sql, r1, r2, r3 = agent._generate_textual_responses(
            natural_language_query=nl_query,
            sql_agent_response=sql_agent_response_direct_sql,
            retrieved_context_str=retrieved_context_str,
        )
        self.assertEqual(sql, "SELECT * FROM DUMMY_DIRECT;")
        # Responses r1,r2,r3 will be the same due to DummyLLM's behavior

    @patch("logging.error")
    def test_generate_textual_responses_no_llm(self, mock_log_error):
        # Instantiate Agent with llm=None
        with patch.object(
            FirebirdDocumentedSQLAgent,
            "_load_and_parse_documentation",
            lambda self: None,
        ):
            with patch.object(
                FirebirdDocumentedSQLAgent, "_initialize_components", lambda self: None
            ):
                with patch.object(
                    FirebirdDocumentedSQLAgent, "_setup_sql_agent", lambda self: None
                ):
                    agent = FirebirdDocumentedSQLAgent(
                        db_connection_string=None, llm=None
                    )  # LLM is None

        self.assertIsNone(agent.llm)  # Verify precondition

        # Input data
        nl_query = "Query when LLM is None"
        sql_agent_response = {
            "output": "Some SQL output",
            "sql_query": "SELECT 1;",
        }  # sql_query for SQL extraction
        retrieved_context_str = "Some context"

        # Call the method
        sql, r1, r2, r3 = agent._generate_textual_responses(
            natural_language_query=nl_query,
            sql_agent_response=sql_agent_response,
            retrieved_context_str=retrieved_context_str,
        )

        # Assertions
        self.assertEqual(sql, "SELECT 1;")  # SQL should still be extracted
        self.assertEqual(r1, "LLM not available for generating textual response.")
        # The second response should contain the raw SQL output if available
        self.assertEqual(r2, "Raw SQL query result: Some SQL output")
        self.assertEqual(r3, "-")
        mock_log_error.assert_called_with(
            "LLM is not initialized. Cannot generate textual responses."
        )

    @patch("logging.error")
    def test_generate_textual_responses_agent_failure_case(self, mock_log_error):
        # Instantiate Agent
        with patch.object(
            FirebirdDocumentedSQLAgent,
            "_load_and_parse_documentation",
            lambda self: None,
        ):
            with patch.object(
                FirebirdDocumentedSQLAgent, "_initialize_components", lambda self: None
            ):
                with patch.object(
                    FirebirdDocumentedSQLAgent, "_setup_sql_agent", lambda self: None
                ):
                    agent = FirebirdDocumentedSQLAgent(
                        db_connection_string=None, llm=self.mock_llm
                    )

        # Scenario 1: sql_agent_response is None
        nl_query = "Query with agent failure"
        retrieved_context_str = "Some context"

        sql, r1, r2, r3 = agent._generate_textual_responses(
            natural_language_query=nl_query,
            sql_agent_response=None,  # Agent failed to produce a response
            retrieved_context_str=retrieved_context_str,
        )
        self.assertEqual(sql, "No SQL query available due to agent error.")
        self.assertEqual(r1, "Error during SQL agent execution.")
        self.assertEqual(r2, "Could not retrieve a valid response from the SQL agent.")
        self.assertEqual(r3, "-")
        mock_log_error.assert_called_with(
            "SQL agent response is None. Cannot generate textual responses."
        )

        # Scenario 2: sql_agent_response contains an error message (simulated)
        # This depends on how errors are actually propagated in sql_agent_response.
        # Let's assume an 'error' key might be present.
        sql_agent_error_response = {"error": "Simulated agent error: Query timed out"}

        sql, r1, r2, r3 = agent._generate_textual_responses(
            natural_language_query=nl_query,
            sql_agent_response=sql_agent_error_response,
            retrieved_context_str=retrieved_context_str,
        )
        # SQL extraction might still try and fail, or return a default.
        # Current logic extracts SQL first. If 'error' key exists, it might not have SQL.
        # The method tries 'intermediate_steps', then 'sql_query', then 'output'.
        # If none of these yield SQL, it defaults.
        self.assertEqual(
            sql, "No SQL query extracted from agent response."
        )  # Default if no SQL found
        self.assertEqual(
            r1, "Error reported by SQL agent: Simulated agent error: Query timed out"
        )
        self.assertEqual(r2, "Please check the query or system logs.")
        self.assertEqual(r3, "-")
        # The LLM for textual response should not be called if there's an agent error.
        # The DummyLLM's invoke would not be called with "Variant 1 Text:"
        # We can check if logging.error was called for the error in sql_agent_response
        mock_log_error.assert_any_call(
            "Error found in SQL agent response: {'error': 'Simulated agent error: Query timed out'}"
        )


if __name__ == "__main__":
    unittest.main()
