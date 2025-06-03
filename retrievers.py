from typing import List
from abc import ABC
from langchain_core.retrievers import BaseRetriever
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from neo4j import GraphDatabase
from neo4j_graphrag.retrievers import VectorRetriever
from neo4j_graphrag.embeddings import OpenAIEmbeddings as Neo4jOpenAIEmbeddings
from neo4j_graphrag.llm import OpenAILLM
from neo4j_graphrag.generation import GraphRAG

class BaseDocumentationRetriever(BaseRetriever, ABC):
    """Base class for documentation retrievers."""
    pass

class FaissDocumentationRetriever(BaseDocumentationRetriever):
    def __init__(self, documents: List[Document], embeddings_model: OpenAIEmbeddings):
        self.vector_store = FAISS.from_documents(documents, embeddings_model)
        self.retriever = self.vector_store.as_retriever()
    
    def _get_relevant_documents(self, query: str) -> List[Document]:
        return self.retriever.get_relevant_documents(query)

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