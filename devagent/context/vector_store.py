"""Vector storage using ChromaDB"""

import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
import json
import os
from pathlib import Path

from devagent.core.interfaces import CodeChunk


class VectorStore:
    """Vector storage and retrieval using ChromaDB"""
    
    def __init__(self, persist_directory: str = ".devagent/index"):
        self.persist_directory = persist_directory
        
        # Ensure directory exists
        Path(persist_directory).mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="code_chunks",
            metadata={"description": "Code chunks for context retrieval"}
        )
    
    def add_chunks(self, chunks: List[CodeChunk]) -> None:
        """Add code chunks to vector store"""
        if not chunks:
            return
        
        # Prepare data for ChromaDB
        ids = []
        embeddings = []
        documents = []
        metadatas = []
        
        for i, chunk in enumerate(chunks):
            if not chunk.embedding:
                continue
            
            # Create unique ID
            chunk_id = f"{chunk.file_path}:{chunk.start_line}:{chunk.end_line}:{i}"
            ids.append(chunk_id)
            
            # Add embedding
            embeddings.append(chunk.embedding)
            
            # Add document content
            documents.append(chunk.content)
            
            # Add metadata
            metadata = {
                "file_path": chunk.file_path,
                "start_line": chunk.start_line,
                "end_line": chunk.end_line,
                "chunk_type": chunk.chunk_type,
                **chunk.metadata
            }
            
            # Convert non-primitive values to JSON strings for ChromaDB
            for key, value in metadata.items():
                if not isinstance(value, (str, int, float, bool)):
                    try:
                        metadata[key] = json.dumps(value)
                    except TypeError:
                        # Fallback for complex objects that are not directly serializable
                        if hasattr(value, '__dict__'):
                            metadata[key] = json.dumps(value.__dict__)
                        else:
                            metadata[key] = str(value)
            
            metadatas.append(metadata)
        
        if ids:
            # Add to collection
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
    
    def search_similar(self, query_embedding: List[float], k: int = 5, 
                      file_filter: Optional[str] = None,
                      chunk_type_filter: Optional[str] = None) -> List[CodeChunk]:
        """Search for similar code chunks"""
        
        # Build where clause for filtering
        where_clause = None
        if file_filter and chunk_type_filter:
            where_clause = {"$and": [
                {"file_path": {"$eq": file_filter}},
                {"chunk_type": {"$eq": chunk_type_filter}}
            ]}
        elif file_filter:
            where_clause = {"file_path": {"$eq": file_filter}}
        elif chunk_type_filter:
            where_clause = {"chunk_type": {"$eq": chunk_type_filter}}
        
        # Perform search
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            where=where_clause
        )
        
        # Convert results back to CodeChunk objects
        chunks = []
        if results['documents'] and results['documents'][0]:
            for i in range(len(results['documents'][0])):
                metadata = results['metadatas'][0][i]
                
                # Parse JSON metadata back to original types
                parsed_metadata = {}
                for key, value in metadata.items():
                    if key in ['file_path', 'chunk_type']:
                        parsed_metadata[key] = value
                    elif key in ['start_line', 'end_line']:
                        parsed_metadata[key] = int(value)
                    else:
                        try:
                            parsed_metadata[key] = json.loads(value)
                        except (json.JSONDecodeError, TypeError):
                            parsed_metadata[key] = value
                
                chunk = CodeChunk(
                    content=results['documents'][0][i],
                    file_path=parsed_metadata['file_path'],
                    start_line=parsed_metadata['start_line'],
                    end_line=parsed_metadata['end_line'],
                    chunk_type=parsed_metadata['chunk_type'],
                    metadata={k: v for k, v in parsed_metadata.items() 
                             if k not in ['file_path', 'start_line', 'end_line', 'chunk_type']},
                    embedding=results['embeddings'][0][i] if results['embeddings'] else None
                )
                chunks.append(chunk)
        
        return chunks
    
    def search_by_text(self, query_text: str, k: int = 5,
                      file_filter: Optional[str] = None,
                      chunk_type_filter: Optional[str] = None) -> List[CodeChunk]:
        """Search using text query (ChromaDB will handle embedding)"""
        
        # Build where clause for filtering
        where_clause = None
        if file_filter and chunk_type_filter:
            where_clause = {"$and": [
                {"file_path": {"$eq": file_filter}},
                {"chunk_type": {"$eq": chunk_type_filter}}
            ]}
        elif file_filter:
            where_clause = {"file_path": {"$eq": file_filter}}
        elif chunk_type_filter:
            where_clause = {"chunk_type": {"$eq": chunk_type_filter}}
        
        # Perform search
        results = self.collection.query(
            query_texts=[query_text],
            n_results=k,
            where=where_clause
        )
        
        # Convert results back to CodeChunk objects
        chunks = []
        if results['documents'] and results['documents'][0]:
            for i in range(len(results['documents'][0])):
                metadata = results['metadatas'][0][i]
                
                # Parse JSON metadata back to original types
                parsed_metadata = {}
                for key, value in metadata.items():
                    if key in ['file_path', 'chunk_type']:
                        parsed_metadata[key] = value
                    elif key in ['start_line', 'end_line']:
                        parsed_metadata[key] = int(value)
                    else:
                        try:
                            parsed_metadata[key] = json.loads(value)
                        except (json.JSONDecodeError, TypeError):
                            parsed_metadata[key] = value
                
                chunk = CodeChunk(
                    content=results['documents'][0][i],
                    file_path=parsed_metadata['file_path'],
                    start_line=parsed_metadata['start_line'],
                    end_line=parsed_metadata['end_line'],
                    chunk_type=parsed_metadata['chunk_type'],
                    metadata={k: v for k, v in parsed_metadata.items() 
                             if k not in ['file_path', 'start_line', 'end_line', 'chunk_type']},
                    embedding=results['embeddings'][0][i] if results['embeddings'] else None
                )
                chunks.append(chunk)
        
        return chunks
    
    def delete_file_chunks(self, file_path: str) -> None:
        """Delete all chunks for a specific file"""
        # Get all chunks for the file
        results = self.collection.get(
            where={"file_path": {"$eq": file_path}}
        )
        
        if results['ids']:
            self.collection.delete(ids=results['ids'])
    
    def get_file_chunks(self, file_path: str) -> List[CodeChunk]:
        """Get all chunks for a specific file"""
        results = self.collection.get(
            where={"file_path": {"$eq": file_path}}
        )
        
        chunks = []
        if results['documents']:
            for i in range(len(results['documents'])):
                metadata = results['metadatas'][i]
                
                # Parse JSON metadata back to original types
                parsed_metadata = {}
                for key, value in metadata.items():
                    if key in ['file_path', 'chunk_type']:
                        parsed_metadata[key] = value
                    elif key in ['start_line', 'end_line']:
                        parsed_metadata[key] = int(value)
                    else:
                        try:
                            parsed_metadata[key] = json.loads(value)
                        except (json.JSONDecodeError, TypeError):
                            parsed_metadata[key] = value
                
                chunk = CodeChunk(
                    content=results['documents'][i],
                    file_path=parsed_metadata['file_path'],
                    start_line=parsed_metadata['start_line'],
                    end_line=parsed_metadata['end_line'],
                    chunk_type=parsed_metadata['chunk_type'],
                    metadata={k: v for k, v in parsed_metadata.items() 
                             if k not in ['file_path', 'start_line', 'end_line', 'chunk_type']},
                    embedding=results['embeddings'][i] if results['embeddings'] else None
                )
                chunks.append(chunk)
        
        return chunks
    
    def count_chunks(self) -> int:
        """Get total number of chunks in store"""
        return self.collection.count()
    
    def list_files(self) -> List[str]:
        """List all files that have chunks in the store"""
        results = self.collection.get()
        
        files = set()
        if results['metadatas']:
            for metadata in results['metadatas']:
                files.add(metadata['file_path'])
        
        return list(files)
    
    def clear(self) -> None:
        """Clear all chunks from store"""
        self.collection.delete()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store"""
        results = self.collection.get()
        
        stats = {
            'total_chunks': len(results['ids']) if results['ids'] else 0,
            'total_files': len(self.list_files()),
            'chunk_types': {},
            'files': {}
        }
        
        if results['metadatas']:
            for metadata in results['metadatas']:
                # Count chunk types
                chunk_type = metadata.get('chunk_type', 'unknown')
                stats['chunk_types'][chunk_type] = stats['chunk_types'].get(chunk_type, 0) + 1
                
                # Count chunks per file
                file_path = metadata.get('file_path', 'unknown')
                stats['files'][file_path] = stats['files'].get(file_path, 0) + 1
        
        return stats
    
    def close(self):
        """Close the vector store and clean up resources"""
        try:
            if hasattr(self, 'client') and self.client:
                # Reset the client to release file handles
                self.client.reset()
                self.client = None
                self.collection = None
        except Exception as e:
            print(f"Warning: Error closing vector store: {e}")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()