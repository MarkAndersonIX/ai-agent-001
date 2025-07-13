import os
import json
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
import threading

from core.base_document_store import DocumentStore, StoredDocument


class FileSystemDocumentStore(DocumentStore):
    """File system implementation of document storage."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize filesystem document store.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.base_path = Path(config.get('path', './data/documents'))
        self.metadata_path = self.base_path / 'metadata'
        self.content_path = self.base_path / 'content'
        
        # Create directories
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.metadata_path.mkdir(exist_ok=True)
        self.content_path.mkdir(exist_ok=True)
        
        self._lock = threading.RLock()
        
        # Load or create index
        self.index_file = self.base_path / 'index.json'
        self._load_index()
    
    def _load_index(self) -> None:
        """Load document index from disk."""
        try:
            if self.index_file.exists():
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    self.index = json.load(f)
            else:
                self.index = {}
        except Exception:
            self.index = {}
    
    def _save_index(self) -> None:
        """Save document index to disk."""
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(self.index, f, indent=2, default=str)
        except Exception:
            pass  # Log error in production
    
    def _generate_doc_id(self, content: str, metadata: Dict[str, Any]) -> str:
        """Generate a unique document ID."""
        # Use content hash + metadata hash for uniqueness
        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]
        metadata_str = json.dumps(metadata, sort_keys=True)
        metadata_hash = hashlib.sha256(metadata_str.encode('utf-8')).hexdigest()[:8]
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"{timestamp}_{content_hash}_{metadata_hash}"
    
    def _calculate_content_hash(self, content: str) -> str:
        """Calculate SHA-256 hash of content."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def _get_content_file_path(self, doc_id: str) -> Path:
        """Get file path for document content."""
        return self.content_path / f"{doc_id}.txt"
    
    def _get_metadata_file_path(self, doc_id: str) -> Path:
        """Get file path for document metadata."""
        return self.metadata_path / f"{doc_id}.json"
    
    def store_document(
        self, 
        content: str, 
        metadata: Dict[str, Any],
        file_path: Optional[str] = None
    ) -> str:
        """Store a document with its metadata."""
        with self._lock:
            doc_id = self._generate_doc_id(content, metadata)
            now = datetime.now()
            content_hash = self._calculate_content_hash(content)
            
            # Check if document with same content hash already exists
            existing_doc = self.get_document_by_hash(content_hash)
            if existing_doc:
                return existing_doc.doc_id
            
            try:
                # Store content
                content_file = self._get_content_file_path(doc_id)
                with open(content_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                # Store metadata
                doc_metadata = {
                    'doc_id': doc_id,
                    'metadata': metadata,
                    'created_at': now.isoformat(),
                    'updated_at': now.isoformat(),
                    'content_hash': content_hash,
                    'file_path': file_path,
                    'content_length': len(content)
                }
                
                metadata_file = self._get_metadata_file_path(doc_id)
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(doc_metadata, f, indent=2)
                
                # Update index
                self.index[doc_id] = {
                    'content_hash': content_hash,
                    'created_at': now.isoformat(),
                    'file_path': file_path,
                    'metadata': metadata
                }
                self._save_index()
                
                return doc_id
                
            except Exception as e:
                # Cleanup on failure
                content_file = self._get_content_file_path(doc_id)
                metadata_file = self._get_metadata_file_path(doc_id)
                content_file.unlink(missing_ok=True)
                metadata_file.unlink(missing_ok=True)
                raise e
    
    def retrieve_document(self, doc_id: str) -> Optional[StoredDocument]:
        """Retrieve a document by its ID."""
        with self._lock:
            try:
                metadata_file = self._get_metadata_file_path(doc_id)
                content_file = self._get_content_file_path(doc_id)
                
                if not metadata_file.exists() or not content_file.exists():
                    return None
                
                # Load metadata
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    doc_metadata = json.load(f)
                
                # Load content
                with open(content_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                return StoredDocument(
                    doc_id=doc_metadata['doc_id'],
                    content=content,
                    metadata=doc_metadata['metadata'],
                    created_at=datetime.fromisoformat(doc_metadata['created_at']),
                    updated_at=datetime.fromisoformat(doc_metadata['updated_at']),
                    content_hash=doc_metadata['content_hash'],
                    file_path=doc_metadata.get('file_path')
                )
                
            except Exception:
                return None
    
    def update_document(
        self, 
        doc_id: str, 
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update an existing document."""
        with self._lock:
            try:
                # Get existing document
                existing_doc = self.retrieve_document(doc_id)
                if not existing_doc:
                    return False
                
                # Update content if provided
                if content is not None:
                    content_file = self._get_content_file_path(doc_id)
                    with open(content_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                    existing_doc.content = content
                    existing_doc.content_hash = self._calculate_content_hash(content)
                
                # Update metadata if provided
                if metadata is not None:
                    existing_doc.metadata.update(metadata)
                
                # Update timestamp
                existing_doc.updated_at = datetime.now()
                
                # Save updated metadata
                doc_metadata = {
                    'doc_id': existing_doc.doc_id,
                    'metadata': existing_doc.metadata,
                    'created_at': existing_doc.created_at.isoformat(),
                    'updated_at': existing_doc.updated_at.isoformat(),
                    'content_hash': existing_doc.content_hash,
                    'file_path': existing_doc.file_path,
                    'content_length': len(existing_doc.content)
                }
                
                metadata_file = self._get_metadata_file_path(doc_id)
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(doc_metadata, f, indent=2)
                
                # Update index
                self.index[doc_id] = {
                    'content_hash': existing_doc.content_hash,
                    'created_at': existing_doc.created_at.isoformat(),
                    'file_path': existing_doc.file_path,
                    'metadata': existing_doc.metadata
                }
                self._save_index()
                
                return True
                
            except Exception:
                return False
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete a document by its ID."""
        with self._lock:
            try:
                content_file = self._get_content_file_path(doc_id)
                metadata_file = self._get_metadata_file_path(doc_id)
                
                # Remove files
                content_file.unlink(missing_ok=True)
                metadata_file.unlink(missing_ok=True)
                
                # Remove from index
                self.index.pop(doc_id, None)
                self._save_index()
                
                return True
                
            except Exception:
                return False
    
    def list_documents(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: Optional[str] = None
    ) -> List[StoredDocument]:
        """List documents with optional filtering, pagination, and ordering."""
        with self._lock:
            documents = []
            
            for doc_id in self.index.keys():
                doc = self.retrieve_document(doc_id)
                if doc:
                    # Apply filters
                    if filters:
                        match = True
                        for key, value in filters.items():
                            if key in doc.metadata and doc.metadata[key] != value:
                                match = False
                                break
                        if not match:
                            continue
                    
                    documents.append(doc)
            
            # Apply ordering
            if order_by:
                reverse = order_by.startswith('-')
                order_field = order_by.lstrip('-')
                
                if order_field == 'created_at':
                    documents.sort(key=lambda d: d.created_at, reverse=reverse)
                elif order_field == 'updated_at':
                    documents.sort(key=lambda d: d.updated_at, reverse=reverse)
            
            # Apply pagination
            if offset:
                documents = documents[offset:]
            if limit:
                documents = documents[:limit]
            
            return documents
    
    def search_documents(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> List[StoredDocument]:
        """Search documents by content or metadata."""
        with self._lock:
            results = []
            query_lower = query.lower()
            
            for doc_id in self.index.keys():
                doc = self.retrieve_document(doc_id)
                if doc:
                    # Apply filters first
                    if filters:
                        match = True
                        for key, value in filters.items():
                            if key in doc.metadata and doc.metadata[key] != value:
                                match = False
                                break
                        if not match:
                            continue
                    
                    # Search in content and metadata
                    if (query_lower in doc.content.lower() or
                        any(query_lower in str(v).lower() for v in doc.metadata.values())):
                        results.append(doc)
            
            # Apply limit
            if limit:
                results = results[:limit]
            
            return results
    
    def get_document_by_hash(self, content_hash: str) -> Optional[StoredDocument]:
        """Retrieve a document by its content hash."""
        with self._lock:
            for doc_id, doc_info in self.index.items():
                if doc_info.get('content_hash') == content_hash:
                    return self.retrieve_document(doc_id)
            return None
    
    def count_documents(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count documents matching the given filters."""
        with self._lock:
            if not filters:
                return len(self.index)
            
            count = 0
            for doc_id in self.index.keys():
                doc = self.retrieve_document(doc_id)
                if doc:
                    match = True
                    for key, value in filters.items():
                        if key in doc.metadata and doc.metadata[key] != value:
                            match = False
                            break
                    if match:
                        count += 1
            
            return count


# Register with factory
from core.component_factory import ComponentFactory
ComponentFactory.register_document_store('filesystem', FileSystemDocumentStore)