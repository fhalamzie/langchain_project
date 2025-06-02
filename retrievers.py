from abc import ABC, abstractmethod
from typing import List, Any # Imported Any
from langchain_core.documents import Document # Using langchain_core for Document

class BaseDocumentationRetriever(ABC):
    """
    Abstract base class for documentation retrievers.
    Defines the interface for retrieving relevant documents based on a query.
    """

    @abstractmethod
    def get_relevant_documents(self, query: str) -> List[Document]:
        """
        Retrieves documents relevant to the given query.

        Args:
            query: The natural language query.

        Returns:
            A list of Langchain Document objects relevant to the query.
        """
        pass

    def _create_langchain_document(self, page_content: str, metadata: dict) -> Document:
        """
        Helper method to create a Langchain Document object.
        Ensures consistent document creation.
        """
        return Document(page_content=page_content, metadata=metadata)


class FaissDocumentationRetriever(BaseDocumentationRetriever):
    """
    A retriever that uses a FAISS index for document retrieval.
    """
    def __init__(self, documents: List[Document], embeddings_model: Any): # Any for now, will be OpenAIEmbeddings
        """
        Initializes the FaissDocumentationRetriever.

        Args:
            documents: A list of Langchain Document objects to be indexed.
            embeddings_model: The embeddings model to use (e.g., OpenAIEmbeddings).
        """
        if not documents:
            raise ValueError("Cannot initialize FaissDocumentationRetriever with an empty list of documents.")
        
        self.embeddings_model = embeddings_model
        
        # Langchain's FAISS expects texts and metadatas separately if using from_texts,
        # or a list of Document objects if using from_documents.
        # We already have Document objects from _load_and_parse_documentation.
        try:
            # Dynamically import FAISS here to keep the dependency optional if not used.
            from langchain_community.vectorstores import FAISS as LangchainFAISS
            # The FAISS class itself is imported from langchain_community.vectorstores
            # OpenAIEmbeddings would be imported where this class is instantiated.
            
            print(f"Initializing FAISS index with {len(documents)} documents...")
            self.vectorstore = LangchainFAISS.from_documents(documents, self.embeddings_model)
            print("FAISS index initialized successfully.")
            self._retriever = self.vectorstore.as_retriever() # Default retriever
        except ImportError:
            raise ImportError("FAISS library not found. Please install it with `pip install faiss-cpu` or `pip install faiss-gpu`.")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize FAISS vector store: {e}")

    def get_relevant_documents(self, query: str, k: int = 5) -> List[Document]:
        """
        Retrieves relevant documents from the FAISS index.

        Args:
            query: The natural language query.
            k: The number of top documents to retrieve. Defaults to 5.

        Returns:
            A list of Langchain Document objects relevant to the query.
        """
        if not self._retriever:
            raise RuntimeError("FAISS retriever is not initialized.")
        
        # Update search_kwargs for the retriever if k is different from default
        # This assumes the retriever instance can have its search_kwargs updated,
        # or we re-create it. For simplicity, let's assume it can be updated or
        # we create a new one for this specific query if k needs to change often.
        # A more robust way might be to pass k to as_retriever() if it's fixed,
        # or handle it within the invoke/get_relevant_documents call if supported.
        # Langchain's BaseRetriever.get_relevant_documents takes **kwargs.
        # The FAISS retriever's as_retriever() method can take search_kwargs.
        
        # For now, let's assume the retriever uses a default k or we adjust it if possible.
        # The `invoke` method on a retriever created by `as_retriever()` takes the query.
        # The number of documents returned is often configured when `as_retriever` is called.
        # Let's adjust the retriever for this call if k is specified.
        
        current_retriever = self.vectorstore.as_retriever(search_kwargs={"k": k})
        return current_retriever.invoke(query)