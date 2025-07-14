from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class StoredDocument:
    """Represents a stored document with metadata."""

    doc_id: str
    content: str
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    content_hash: str
    file_path: Optional[str] = None


class DocumentStore(ABC):
    """Abstract base class for document storage implementations."""

    @abstractmethod
    def store_document(
        self, content: str, metadata: Dict[str, Any], file_path: Optional[str] = None
    ) -> str:
        """
        Store a document with its metadata.

        Args:
            content: Document content
            metadata: Document metadata
            file_path: Optional original file path

        Returns:
            Document ID assigned to the stored document
        """
        pass

    @abstractmethod
    def retrieve_document(self, doc_id: str) -> Optional[StoredDocument]:
        """
        Retrieve a document by its ID.

        Args:
            doc_id: Document ID to retrieve

        Returns:
            StoredDocument if found, None otherwise
        """
        pass

    @abstractmethod
    def update_document(
        self,
        doc_id: str,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Update an existing document.

        Args:
            doc_id: Document ID to update
            content: New content (if provided)
            metadata: New metadata (if provided)

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def delete_document(self, doc_id: str) -> bool:
        """
        Delete a document by its ID.

        Args:
            doc_id: Document ID to delete

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def list_documents(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: Optional[str] = None,
    ) -> List[StoredDocument]:
        """
        List documents with optional filtering, pagination, and ordering.

        Args:
            filters: Optional metadata filters
            limit: Maximum number of documents to return
            offset: Number of documents to skip
            order_by: Field to order by (e.g., 'created_at', 'updated_at')

        Returns:
            List of documents matching criteria
        """
        pass

    @abstractmethod
    def search_documents(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
    ) -> List[StoredDocument]:
        """
        Search documents by content or metadata.

        Args:
            query: Search query
            filters: Optional metadata filters
            limit: Maximum number of results

        Returns:
            List of documents matching search criteria
        """
        pass

    @abstractmethod
    def get_document_by_hash(self, content_hash: str) -> Optional[StoredDocument]:
        """
        Retrieve a document by its content hash.

        Args:
            content_hash: Content hash to search for

        Returns:
            StoredDocument if found, None otherwise
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
