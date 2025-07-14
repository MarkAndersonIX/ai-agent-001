"""
Unit tests for base vector store functionality.
"""

import pytest

from core.base_vector_store import Document, SearchResult, VectorStore


class TestDocument:
    """Test Document class."""

    def test_document_creation(self):
        """Test creating a document."""
        doc = Document(
            content="Test content", metadata={"type": "test"}, doc_id="test_id"
        )

        assert doc.content == "Test content"
        assert doc.metadata == {"type": "test"}
        assert doc.doc_id == "test_id"

    def test_document_without_id(self):
        """Test creating a document without ID."""
        doc = Document(content="Test content", metadata={"type": "test"})

        assert doc.content == "Test content"
        assert doc.metadata == {"type": "test"}
        assert doc.doc_id is None


class TestSearchResult:
    """Test SearchResult class."""

    def test_search_result_creation(self):
        """Test creating a search result."""
        doc = Document("Test", {}, "id1")
        result = SearchResult(document=doc, score=0.85)

        assert result.document == doc
        assert result.score == 0.85


class TestVectorStoreAbstract:
    """Test VectorStore abstract interface."""

    def test_cannot_instantiate_abstract_class(self):
        """Test that VectorStore cannot be instantiated directly."""
        with pytest.raises(TypeError):
            VectorStore()


class TestMockVectorStore:
    """Test MockVectorStore implementation."""

    def test_add_documents(self, mock_vector_store, sample_documents):
        """Test adding documents to vector store."""
        doc_ids = mock_vector_store.add_documents(sample_documents)

        assert len(doc_ids) == 3
        assert all(isinstance(doc_id, str) for doc_id in doc_ids)
        assert mock_vector_store.count_documents() == 3

    def test_similarity_search(self, mock_vector_store, sample_documents):
        """Test similarity search functionality."""
        # Add documents first
        mock_vector_store.add_documents(sample_documents)

        # Search for Python-related content
        results = mock_vector_store.similarity_search("Python", k=2)

        assert len(results) <= 2
        assert all(isinstance(result, SearchResult) for result in results)
        assert all(0 <= result.score <= 1 for result in results)

        # Results should be sorted by score (highest first)
        if len(results) > 1:
            assert results[0].score >= results[1].score

    def test_similarity_search_with_filters(self, mock_vector_store, sample_documents):
        """Test similarity search with metadata filters."""
        mock_vector_store.add_documents(sample_documents)

        # Search with type filter
        results = mock_vector_store.similarity_search(
            "test", filters={"type": "programming"}
        )

        # Should only return documents matching the filter
        for result in results:
            assert result.document.metadata.get("type") == "programming"

    def test_get_document(self, mock_vector_store, sample_documents):
        """Test retrieving specific documents."""
        doc_ids = mock_vector_store.add_documents(sample_documents)

        # Get first document
        retrieved_doc = mock_vector_store.get_document(doc_ids[0])

        assert retrieved_doc is not None
        assert retrieved_doc.doc_id == doc_ids[0]
        assert retrieved_doc.content == sample_documents[0].content

    def test_get_nonexistent_document(self, mock_vector_store):
        """Test retrieving non-existent document."""
        result = mock_vector_store.get_document("nonexistent_id")
        assert result is None

    def test_delete_documents(self, mock_vector_store, sample_documents):
        """Test deleting documents."""
        doc_ids = mock_vector_store.add_documents(sample_documents)
        initial_count = mock_vector_store.count_documents()

        # Delete first document
        success = mock_vector_store.delete_documents([doc_ids[0]])

        assert success is True
        assert mock_vector_store.count_documents() == initial_count - 1
        assert mock_vector_store.get_document(doc_ids[0]) is None

    def test_list_documents(self, mock_vector_store, sample_documents):
        """Test listing documents."""
        mock_vector_store.add_documents(sample_documents)

        # List all documents
        all_docs = mock_vector_store.list_documents()
        assert len(all_docs) == 3

        # List with limit
        limited_docs = mock_vector_store.list_documents(limit=2)
        assert len(limited_docs) == 2

        # List with offset
        offset_docs = mock_vector_store.list_documents(offset=1)
        assert len(offset_docs) == 2

    def test_list_documents_with_filters(self, mock_vector_store, sample_documents):
        """Test listing documents with filters."""
        mock_vector_store.add_documents(sample_documents)

        # Filter by type
        filtered_docs = mock_vector_store.list_documents(
            filters={"type": "programming"}
        )

        assert len(filtered_docs) == 1
        assert filtered_docs[0].metadata["type"] == "programming"

    def test_count_documents(self, mock_vector_store, sample_documents):
        """Test counting documents."""
        assert mock_vector_store.count_documents() == 0

        mock_vector_store.add_documents(sample_documents)
        assert mock_vector_store.count_documents() == 3

        # Count with filters
        programming_count = mock_vector_store.count_documents(
            filters={"type": "programming"}
        )
        assert programming_count == 1

    def test_empty_vector_store(self, mock_vector_store):
        """Test operations on empty vector store."""
        assert mock_vector_store.count_documents() == 0
        assert mock_vector_store.list_documents() == []

        results = mock_vector_store.similarity_search("test")
        assert results == []


# Alternative unittest.TestCase version (commented out)
"""
import unittest
from unittest.mock import Mock

class TestVectorStoreUnittest(unittest.TestCase):
    '''Example of how the same tests would look with unittest.TestCase'''

    def setUp(self):
        '''Set up test fixtures before each test method.'''
        from tests.conftest import MockVectorStore
        self.vector_store = MockVectorStore()
        self.sample_docs = [
            Document("Python content", {"type": "programming"}, "doc1"),
            Document("ML content", {"type": "ml"}, "doc2")
        ]

    def tearDown(self):
        '''Clean up after each test method.'''
        self.vector_store = None

    def test_add_documents(self):
        '''Test adding documents to vector store.'''
        doc_ids = self.vector_store.add_documents(self.sample_docs)

        self.assertEqual(len(doc_ids), 2)
        self.assertIsInstance(doc_ids[0], str)
        self.assertEqual(self.vector_store.count_documents(), 2)

    def test_similarity_search(self):
        '''Test similarity search functionality.'''
        self.vector_store.add_documents(self.sample_docs)

        results = self.vector_store.similarity_search("Python", k=1)

        self.assertLessEqual(len(results), 1)
        self.assertIsInstance(results[0], SearchResult)
        self.assertGreaterEqual(results[0].score, 0)
        self.assertLessEqual(results[0].score, 1)

if __name__ == '__main__':
    unittest.main()
"""
