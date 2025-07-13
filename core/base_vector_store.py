from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass


@dataclass
class Document:
    """Represents a document with content and metadata."""
    content: str
    metadata: Dict[str, Any]
    doc_id: Optional[str] = None


@dataclass
class SearchResult:
    """Represents a search result with similarity score."""
    document: Document
    score: float


class VectorStore(ABC):
    """Abstract base class for vector storage implementations."""
    
    @abstractmethod
    def add_documents(self, documents: List[Document]) -> List[str]:
        """
        Add documents to the vector store.
        
        Args:
            documents: List of documents to add
            
        Returns:
            List of document IDs assigned to the documents
        """
        pass
    
    @abstractmethod
    def similarity_search(
        self, 
        query: str, 
        k: int = 5, 
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """
        Perform similarity search on the vector store.
        
        Args:
            query: Search query string
            k: Number of results to return
            filters: Optional metadata filters
            
        Returns:
            List of search results with similarity scores
        """
        pass
    
    @abstractmethod
    def delete_documents(self, doc_ids: List[str]) -> bool:
        """
        Delete documents from the vector store.
        
        Args:
            doc_ids: List of document IDs to delete
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_document(self, doc_id: str) -> Optional[Document]:
        """
        Retrieve a specific document by ID.
        
        Args:
            doc_id: Document ID to retrieve
            
        Returns:
            Document if found, None otherwise
        """
        pass
    
    @abstractmethod
    def list_documents(
        self, 
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Document]:
        """
        List documents with optional filtering and pagination.
        
        Args:
            filters: Optional metadata filters
            limit: Maximum number of documents to return
            offset: Number of documents to skip
            
        Returns:
            List of documents matching criteria
        """
        pass
    
    @abstractmethod
    def count_documents(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count documents matching the given filters.
        
        Args:
            filters: Optional metadata filters
            
        Returns:
            Number of documents matching criteria
        """
        pass