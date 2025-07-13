from typing import List, Dict, Any, Optional
import os
from pathlib import Path

from core.base_vector_store import VectorStore, Document, SearchResult


class ChromaVectorStore(VectorStore):
    """ChromaDB implementation for local vector storage."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize ChromaDB vector store.
        
        Args:
            config: Configuration dictionary
        """
        try:
            import chromadb
            from chromadb.config import Settings
        except ImportError:
            raise ImportError(
                "ChromaDB is required for ChromaVectorStore. "
                "Install with: pip install chromadb"
            )
        
        self.config = config
        self.collection_name = config.get('collection_name', 'ai_agents')
        
        # Setup persistent directory
        persist_directory = config.get('path', './data/vectors')
        Path(persist_directory).mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                allow_reset=config.get('allow_reset', False),
                anonymized_telemetry=config.get('anonymized_telemetry', False)
            )
        )
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(name=self.collection_name)
        except Exception:
            # Collection doesn't exist, create it
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "AI Agent documents and embeddings"}
            )
        
        # Initialize embedding function if provided
        self.embedding_function = None
        if 'embedding_function' in config:
            self.embedding_function = config['embedding_function']
    
    def add_documents(self, documents: List[Document]) -> List[str]:
        """Add documents to the vector store."""
        if not documents:
            return []
        
        # Prepare data for ChromaDB
        doc_ids = []
        doc_contents = []
        doc_metadatas = []
        doc_embeddings = []
        
        for i, doc in enumerate(documents):
            # Generate ID if not provided
            doc_id = doc.doc_id or f"doc_{len(doc_ids)}_{hash(doc.content) % 10000}"
            doc_ids.append(doc_id)
            doc_contents.append(doc.content)
            doc_metadatas.append(doc.metadata)
            
            # Use provided embeddings if available
            if hasattr(doc, 'embedding') and doc.embedding:
                doc_embeddings.append(doc.embedding)
        
        try:
            # Add to collection
            if doc_embeddings and len(doc_embeddings) == len(documents):
                # Use provided embeddings
                self.collection.add(
                    ids=doc_ids,
                    documents=doc_contents,
                    metadatas=doc_metadatas,
                    embeddings=doc_embeddings
                )
            else:
                # Let ChromaDB generate embeddings
                self.collection.add(
                    ids=doc_ids,
                    documents=doc_contents,
                    metadatas=doc_metadatas
                )
            
            return doc_ids
            
        except Exception as e:
            raise RuntimeError(f"Failed to add documents to ChromaDB: {str(e)}")
    
    def similarity_search(
        self, 
        query: str, 
        k: int = 5, 
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Perform similarity search on the vector store."""
        try:
            # Convert filters to ChromaDB format
            where_clause = None
            if filters:
                # ChromaDB uses specific filter syntax
                where_clause = {}
                for key, value in filters.items():
                    where_clause[key] = {"$eq": value}
            
            # Perform search
            results = self.collection.query(
                query_texts=[query],
                n_results=k,
                where=where_clause
            )
            
            # Convert results to SearchResult objects
            search_results = []
            if results and results['documents'] and results['documents'][0]:
                documents = results['documents'][0]
                metadatas = results['metadatas'][0] or []
                distances = results['distances'][0] if results['distances'] else []
                ids = results['ids'][0] if results['ids'] else []
                
                for i, content in enumerate(documents):
                    metadata = metadatas[i] if i < len(metadatas) else {}
                    doc_id = ids[i] if i < len(ids) else None
                    distance = distances[i] if i < len(distances) else 0.0
                    
                    # Convert distance to similarity score (higher is more similar)
                    similarity_score = 1.0 - distance if distance <= 1.0 else 1.0 / (1.0 + distance)
                    
                    document = Document(
                        content=content,
                        metadata=metadata,
                        doc_id=doc_id
                    )
                    
                    search_results.append(SearchResult(
                        document=document,
                        score=similarity_score
                    ))
            
            return search_results
            
        except Exception as e:
            raise RuntimeError(f"Failed to search ChromaDB: {str(e)}")
    
    def delete_documents(self, doc_ids: List[str]) -> bool:
        """Delete documents from the vector store."""
        try:
            self.collection.delete(ids=doc_ids)
            return True
        except Exception:
            return False
    
    def get_document(self, doc_id: str) -> Optional[Document]:
        """Retrieve a specific document by ID."""
        try:
            results = self.collection.get(
                ids=[doc_id],
                include=['documents', 'metadatas']
            )
            
            if results and results['documents'] and results['documents'][0]:
                content = results['documents'][0]
                metadata = results['metadatas'][0] if results['metadatas'] else {}
                
                return Document(
                    content=content,
                    metadata=metadata,
                    doc_id=doc_id
                )
            
            return None
            
        except Exception:
            return None
    
    def list_documents(
        self, 
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Document]:
        """List documents with optional filtering and pagination."""
        try:
            # Convert filters to ChromaDB format
            where_clause = None
            if filters:
                where_clause = {}
                for key, value in filters.items():
                    where_clause[key] = {"$eq": value}
            
            # Get documents
            kwargs = {
                'include': ['documents', 'metadatas'],
                'where': where_clause
            }
            
            if limit:
                kwargs['limit'] = limit
            if offset:
                kwargs['offset'] = offset
            
            results = self.collection.get(**kwargs)
            
            documents = []
            if results and results['documents']:
                for i, content in enumerate(results['documents']):
                    metadata = results['metadatas'][i] if results['metadatas'] and i < len(results['metadatas']) else {}
                    doc_id = results['ids'][i] if results['ids'] and i < len(results['ids']) else None
                    
                    documents.append(Document(
                        content=content,
                        metadata=metadata,
                        doc_id=doc_id
                    ))
            
            return documents
            
        except Exception:
            return []
    
    def count_documents(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count documents matching the given filters."""
        try:
            # Convert filters to ChromaDB format
            where_clause = None
            if filters:
                where_clause = {}
                for key, value in filters.items():
                    where_clause[key] = {"$eq": value}
            
            # Get count
            results = self.collection.get(
                where=where_clause,
                include=[]  # Don't include content, just count
            )
            
            return len(results['ids']) if results and results['ids'] else 0
            
        except Exception:
            return 0
    
    def reset_collection(self) -> bool:
        """Reset the collection (delete all documents)."""
        try:
            self.client.delete_collection(name=self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "AI Agent documents and embeddings"}
            )
            return True
        except Exception:
            return False
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the collection."""
        try:
            count = self.collection.count()
            return {
                'name': self.collection_name,
                'count': count,
                'metadata': self.collection.metadata
            }
        except Exception:
            return {
                'name': self.collection_name,
                'count': 0,
                'metadata': {}
            }


# Register with factory
from core.component_factory import ComponentFactory
ComponentFactory.register_vector_store('chroma', ChromaVectorStore)