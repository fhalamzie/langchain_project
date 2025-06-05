from typing import List, Optional, Any
from abc import ABC
from langchain_core.retrievers import BaseRetriever
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
# Optional Neo4j imports
try:
    from neo4j import GraphDatabase
    from neo4j_graphrag.retrievers import VectorRetriever
    from neo4j_graphrag.embeddings import OpenAIEmbeddings as Neo4jOpenAIEmbeddings
    from neo4j_graphrag.llm import OpenAILLM
    from neo4j_graphrag.generation import GraphRAG
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    print("⚠️ Neo4j not available - Neo4j retriever will be disabled")

class BaseDocumentationRetriever(BaseRetriever, ABC):
    """Base class for documentation retrievers."""
    pass

class FaissDocumentationRetriever(BaseDocumentationRetriever):
    vector_store: Optional[FAISS] = None
    retriever: Optional[Any] = None
    
    def __init__(self, documents: List[Document], embeddings_model: OpenAIEmbeddings, **kwargs):
        super().__init__(**kwargs)
        self.vector_store = FAISS.from_documents(documents, embeddings_model)
        self.retriever = self.vector_store.as_retriever()
    
    def _get_relevant_documents(self, query: str) -> List[Document]:
        return self.retriever.get_relevant_documents(query)

# Neo4j retriever only available if Neo4j is installed
if NEO4J_AVAILABLE:
    class Neo4jDocumentationRetriever(BaseDocumentationRetriever):
        def __init__(self, uri: str, user: str, password: str, index_name: str):
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            self.embedder = Neo4jOpenAIEmbeddings(model="text-embedding-3-large")
            self.retriever = VectorRetriever(
                self.driver,
                index_name,
                self.embedder,
                return_properties=["content", "source"]
            )
            self.llm = OpenAILLM(model_name="gpt-4o", model_params={"temperature": 0})
            self.graph_rag = GraphRAG(retriever=self.retriever, llm=self.llm)
        
        def _get_relevant_documents(self, query: str) -> List[Document]:
            """Retrieve documents relevant to the query using Neo4j GraphRAG"""
            response = self.graph_rag.search(
                query_text=query,
                retriever_config={"top_k": 5}
            )
            return [Document(
                page_content=response.answer,
                metadata={"source": "Neo4j GraphRAG"}
            )]
        
        def close(self):
            """Close the Neo4j driver connection"""
            self.driver.close()
else:
    # Placeholder class when Neo4j is not available
    class Neo4jDocumentationRetriever:
        def __init__(self, *args, **kwargs):
            raise ImportError("Neo4j is not available. Please install neo4j and neo4j-graphrag packages.")
        
        def _get_relevant_documents(self, query: str) -> List[Document]:
            raise ImportError("Neo4j is not available.")
        
        def close(self):
            pass