from typing import List

from langchain_core.documents import Document
from neo4j import GraphDatabase
from neo4j_graphrag.embeddings import OpenAIEmbeddings
from neo4j_graphrag.indexes import upsert_vectors


class Neo4jImporter:
    def __init__(self, uri: str, user: str, password: str, index_name: str):
        """
        Initializes the Neo4j importer with connection details.

        Args:
            uri: Neo4j connection URI (e.g., "bolt://localhost:7687")
            user: Neo4j username
            password: Neo4j password
            index_name: Name of the vector index to create
        """
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.index_name = index_name
        self.embedder = OpenAIEmbeddings(model="text-embedding-3-large")

    def create_index(self, dimension: int = 1536):
        """
        Creates a vector index in Neo4j if it doesn't exist.

        Args:
            dimension: Dimension of the embedding vectors
        """
        with self.driver.session() as session:
            session.run(
                f"CREATE VECTOR INDEX {self.index_name} IF NOT EXISTS "
                "FOR (d:Document) ON d.embedding "
                "OPTIONS {indexConfig: {"
                "  `vector.dimensions`: $dimension, "
                "  `vector.similarity`: 'cosine'"
                "}}",
                dimension=dimension,
            )
        print(f"Vector index '{self.index_name}' created or already exists")

    def import_documents(self, docs: List[Document]):
        """
        Imports documents into Neo4j with embeddings.

        Args:
            docs: List of Document objects to import
        """
        embeddings = self.embedder.embed_documents([doc.page_content for doc in docs])

        with self.driver.session() as session:
            # Create nodes and embeddings
            for i, doc in enumerate(docs):
                session.run(
                    "MERGE (d:Document {id: $id}) "
                    "SET d.content = $content, "
                    "d.metadata = $metadata, "
                    "d.embedding = $embedding",
                    id=f"doc_{i}",
                    content=doc.page_content,
                    metadata=str(doc.metadata),
                    embedding=embeddings[i],
                )

            # Create relationships between similar documents
            # This is a placeholder for more advanced relationship logic
            session.run(
                "MATCH (d1:Document), (d2:Document) WHERE d1.id < d2.id "
                "CREATE (d1)-[:SIMILAR_TO]->(d2)"
            )

        print(f"Imported {len(docs)} documents into Neo4j")

    def close(self):
        """Closes the Neo4j driver connection"""
        self.driver.close()
