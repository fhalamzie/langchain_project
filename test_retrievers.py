import unittest
from typing import List
from langchain_core.documents import Document

from retrievers import BaseDocumentationRetriever, FaissDocumentationRetriever
from unittest.mock import patch, MagicMock
# We might need to mock FAISS and OpenAIEmbeddings
# from langchain_community.vectorstores import FAISS (mocked via patch)
# from langchain_openai import OpenAIEmbeddings (mocked via patch)


class DummyRetriever(BaseDocumentationRetriever):
    """
    A dummy implementation of BaseDocumentationRetriever for testing purposes.
    """
    def __init__(self, dummy_docs: List[Document] = None):
        self.dummy_docs = dummy_docs if dummy_docs is not None else []

    def get_relevant_documents(self, query: str) -> List[Document]:
        """
        Returns dummy documents if the query matches a certain condition,
        otherwise an empty list.
        """
        if "test_query" in query:
            return self.dummy_docs
        return []

class TestBaseDocumentationRetriever(unittest.TestCase):

    def test_base_retriever_interface_existence(self):
        """
        Tests that a class can inherit from BaseDocumentationRetriever
        and implement its abstract method.
        """
        dummy_doc_content = "This is a dummy document."
        dummy_metadata = {"source": "dummy_source"}
        
        retriever = DummyRetriever(dummy_docs=[
            Document(page_content=dummy_doc_content, metadata=dummy_metadata)
        ])
        self.assertIsNotNone(retriever)
        
        # Test the abstract method implementation
        docs = retriever.get_relevant_documents("some_query")
        self.assertIsInstance(docs, list)
        
        docs_with_match = retriever.get_relevant_documents("test_query for content")
        self.assertEqual(len(docs_with_match), 1)
        if docs_with_match:
            self.assertEqual(docs_with_match[0].page_content, dummy_doc_content)
            self.assertEqual(docs_with_match[0].metadata, dummy_metadata)

    def test_create_langchain_document_helper(self):
        """
        Tests the _create_langchain_document helper method.
        """
        # We need an instance of a concrete class to test the helper method
        retriever = DummyRetriever()
        page_content = "Test content for document."
        metadata = {"source": "test_source", "page": 1}
        
        # Accessing protected member for testing purposes
        # pylint: disable=protected-access 
        created_doc = retriever._create_langchain_document(page_content, metadata)
        
        self.assertIsInstance(created_doc, Document)
        self.assertEqual(created_doc.page_content, page_content)
        self.assertEqual(created_doc.metadata, metadata)
        self.assertEqual(created_doc.metadata["source"], "test_source")


class TestFaissDocumentationRetriever(unittest.TestCase):

    def setUp(self):
        self.sample_docs = [
            Document(page_content="This is document 1 about apples.", metadata={"source": "doc1.txt"}),
            Document(page_content="Document 2 discusses bananas.", metadata={"source": "doc2.txt"}),
            Document(page_content="The third document is about oranges and apples.", metadata={"source": "doc3.txt"})
        ]
        self.mock_embeddings_model = MagicMock() # Represents an instance of OpenAIEmbeddings

    @patch('retrievers.FAISS') # Mock the FAISS class from langchain_community.vectorstores
    @patch('retrievers.OpenAIEmbeddings') # Mock OpenAIEmbeddings if it's instantiated inside
    def test_faiss_retriever_initialization_success(self, MockOpenAIEmbeddings, MockFAISS):
        # If embeddings_model is passed, MockOpenAIEmbeddings might not be needed here,
        # unless FaissDocumentationRetriever creates its own if None is passed.
        # Assuming embeddings_model is required and passed.
        
        mock_faiss_instance = MockFAISS.from_documents.return_value
        
        retriever = FaissDocumentationRetriever(
            documents=self.sample_docs,
            embeddings_model=self.mock_embeddings_model
        )

        MockFAISS.from_documents.assert_called_once_with(
            self.sample_docs,
            self.mock_embeddings_model,
            # Add other potential default arguments for FAISS.from_documents if necessary
            # e.g. distance_strategy=DistanceStrategy.EUCLIDEAN_DISTANCE (if it's a default)
        )
        self.assertIsNotNone(retriever.faiss_vectorstore)
        self.assertIs(retriever.faiss_vectorstore, mock_faiss_instance)

    def test_faiss_retriever_initialization_no_embeddings(self):
        with self.assertRaises(ValueError) as context:
            FaissDocumentationRetriever(documents=self.sample_docs, embeddings_model=None)
        self.assertIn("Embeddings model cannot be None", str(context.exception))

    @patch('retrievers.FAISS')
    def test_faiss_retriever_initialization_no_documents(self, MockFAISS):
        # Test how it handles empty documents list.
        # The current FAISS.from_documents might raise an error or handle it.
        # If FAISS raises an error for empty docs, the retriever should propagate or handle it.
        # Let's assume FAISS.from_documents would be called and might raise an error.
        # Or, the retriever might have a check.
        # Based on typical FAISS usage, it might raise an error if docs are empty.
        
        # If FaissDocumentationRetriever has a check *before* calling FAISS.from_documents:
        with self.assertRaises(ValueError) as context:
             FaissDocumentationRetriever(documents=[], embeddings_model=self.mock_embeddings_model)
        self.assertIn("Documents list cannot be empty", str(context.exception))
        MockFAISS.from_documents.assert_not_called()


    @patch('retrievers.FAISS') # To control the FAISS instance
    def test_faiss_retriever_get_relevant_documents(self, MockFAISS):
        # Setup a mock FAISS vectorstore instance
        mock_vectorstore_instance = MagicMock()
        # Configure FAISS.from_documents to return our mock vectorstore instance
        MockFAISS.from_documents.return_value = mock_vectorstore_instance

        retriever = FaissDocumentationRetriever(
            documents=self.sample_docs,
            embeddings_model=self.mock_embeddings_model
        )
        
        # Ensure the retriever is using the mocked vectorstore
        self.assertIs(retriever.faiss_vectorstore, mock_vectorstore_instance)

        query_text = "Tell me about apples"
        expected_retrieved_docs = [
            Document(page_content="This is document 1 about apples.", metadata={"source": "doc1.txt"}),
            Document(page_content="The third document is about oranges and apples.", metadata={"source": "doc3.txt"})
        ]
        
        # Configure the similarity_search method of our mock vectorstore
        mock_vectorstore_instance.similarity_search.return_value = expected_retrieved_docs
        
        retrieved_docs = retriever.get_relevant_documents(query_text)
        
        mock_vectorstore_instance.similarity_search.assert_called_once_with(query_text, k=5) # k=5 is the default in FaissDocumentationRetriever
        self.assertEqual(len(retrieved_docs), 2)
        self.assertEqual(retrieved_docs, expected_retrieved_docs)

    @patch('retrievers.FAISS')
    def test_faiss_retriever_get_relevant_documents_custom_k(self, MockFAISS):
        mock_vectorstore_instance = MagicMock()
        MockFAISS.from_documents.return_value = mock_vectorstore_instance

        retriever = FaissDocumentationRetriever(
            documents=self.sample_docs,
            embeddings_model=self.mock_embeddings_model,
            k_results=3 # Custom k
        )
        
        query_text = "Tell me about bananas"
        mock_vectorstore_instance.similarity_search.return_value = [self.sample_docs[1]] # Dummy return

        retriever.get_relevant_documents(query_text)
        
        mock_vectorstore_instance.similarity_search.assert_called_once_with(query_text, k=3)


if __name__ == '__main__':
    unittest.main()