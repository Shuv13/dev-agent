"""Main context engine implementation"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer

from devagent.core.interfaces import ContextEngine, CodeChunk
from .indexer import CodeIndexer
from .vector_store import VectorStore


class DevAgentContextEngine(ContextEngine):
    """Main context engine for DevAgent"""
    
    def __init__(self, project_path: str, persist_directory: str = None):
        self.project_path = Path(project_path)
        
        if persist_directory is None:
            persist_directory = str(self.project_path / ".devagent" / "index")
        
        self.persist_directory = persist_directory
        self.indexer = CodeIndexer()
        self.vector_store = VectorStore(persist_directory)
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        
        # File hash tracking for incremental updates
        self.hash_file = Path(persist_directory) / "file_hashes.json"
        self.file_hashes = self._load_file_hashes()
    
    def index_codebase(self, project_path: str = None, force_reindex: bool = False) -> None:
        """Index the entire codebase"""
        if project_path:
            self.project_path = Path(project_path)
        
        if force_reindex:
            self.vector_store.clear()
            self.file_hashes = {}
        
        print(f"Indexing codebase at {self.project_path}...")
        
        # Get exclude patterns from config or use defaults
        exclude_patterns = [
            "*.pyc", "__pycache__", ".git", "node_modules", ".venv", "venv",
            "*.egg-info", "dist", "build", ".pytest_cache", ".coverage",
            "*.log", "*.tmp", ".DS_Store", "Thumbs.db"
        ]
        
        # Index project
        chunks = self.indexer.index_project(str(self.project_path), exclude_patterns)
        
        if chunks:
            print(f"Adding {len(chunks)} chunks to vector store...")
            self.vector_store.add_chunks(chunks)
            
            # Update file hashes
            for chunk in chunks:
                file_hash = self.indexer.get_file_hash(chunk.file_path)
                self.file_hashes[chunk.file_path] = file_hash
            
            self._save_file_hashes()
            print("Indexing complete!")
        else:
            print("No code chunks found to index.")
    
    def update_index(self, changed_files: List[str] = None) -> None:
        """Incrementally update index for changed files"""
        if changed_files is None:
            changed_files = self._find_changed_files()
        
        if not changed_files:
            print("No files need updating.")
            return
        
        print(f"Updating index for {len(changed_files)} changed files...")
        
        for file_path in changed_files:
            try:
                # Remove old chunks for this file
                self.vector_store.delete_file_chunks(file_path)
                
                # Re-index the file
                chunks = self.indexer.index_file(file_path)
                if chunks:
                    self.vector_store.add_chunks(chunks)
                
                # Update hash
                file_hash = self.indexer.get_file_hash(file_path)
                self.file_hashes[file_path] = file_hash
                
                print(f"Updated: {file_path}")
                
            except Exception as e:
                print(f"Warning: Failed to update {file_path}: {e}")
        
        self._save_file_hashes()
        print("Index update complete!")
    
    def get_relevant_context(self, query: str, k: int = 5, 
                           file_filter: Optional[str] = None,
                           chunk_type_filter: Optional[str] = None) -> List[CodeChunk]:
        """Get relevant code chunks for a query"""
        
        # Generate query embedding
        query_embedding = self.model.encode(query, convert_to_tensor=False).tolist()
        
        # Search for similar chunks
        chunks = self.vector_store.search_similar(
            query_embedding, 
            k=k, 
            file_filter=file_filter,
            chunk_type_filter=chunk_type_filter
        )
        
        return chunks
    
    def get_function_context(self, file_path: str, function_name: str, k: int = 3) -> List[CodeChunk]:
        """Get context for a specific function"""
        
        # First, try to find the exact function
        query = f"function {function_name}"
        chunks = self.get_relevant_context(
            query, 
            k=k*2,  # Get more results to filter
            file_filter=file_path,
            chunk_type_filter="function"
        )
        
        # Filter for the specific function
        function_chunks = []
        other_chunks = []
        
        for chunk in chunks:
            if chunk.metadata.get('name') == function_name:
                function_chunks.append(chunk)
            else:
                other_chunks.append(chunk)
        
        # Return function chunks first, then related chunks
        result = function_chunks + other_chunks[:k-len(function_chunks)]
        return result[:k]
    
    def get_file_context(self, file_path: str) -> List[CodeChunk]:
        """Get all chunks for a specific file"""
        return self.vector_store.get_file_chunks(file_path)
    
    def search_by_text(self, query: str, k: int = 5) -> List[CodeChunk]:
        """Search using text query"""
        return self.vector_store.search_by_text(query, k=k)
    
    def get_related_functions(self, function_name: str, k: int = 5) -> List[CodeChunk]:
        """Find functions related to the given function"""
        query = f"function calls {function_name} dependencies"
        return self.get_relevant_context(query, k=k, chunk_type_filter="function")
    
    def get_test_patterns(self, file_path: str = None) -> List[CodeChunk]:
        """Get existing test patterns from the codebase"""
        query = "test function unittest pytest assert"
        
        chunks = self.get_relevant_context(query, k=10)
        
        # Filter for test-related chunks
        test_chunks = []
        for chunk in chunks:
            content_lower = chunk.content.lower()
            if any(keyword in content_lower for keyword in ['test_', 'def test', 'it(', 'describe(', 'assert']):
                test_chunks.append(chunk)
        
        return test_chunks[:5]  # Return top 5 test patterns
    
    def get_stats(self) -> Dict[str, Any]:
        """Get context engine statistics"""
        vector_stats = self.vector_store.get_stats()
        
        stats = {
            'project_path': str(self.project_path),
            'total_indexed_files': len(self.file_hashes),
            'vector_store_stats': vector_stats,
            'model_name': self.model.get_sentence_embedding_dimension()
        }
        
        return stats
    
    def _find_changed_files(self) -> List[str]:
        """Find files that have changed since last indexing"""
        changed_files = []
        
        # Check existing indexed files
        for file_path, stored_hash in self.file_hashes.items():
            if os.path.exists(file_path):
                if self.indexer.should_reindex_file(file_path, stored_hash):
                    changed_files.append(file_path)
            else:
                # File was deleted, remove from vector store
                self.vector_store.delete_file_chunks(file_path)
                del self.file_hashes[file_path]
        
        # Check for new files
        from devagent.analysis.analyzer_factory import AnalyzerFactory
        supported_extensions = AnalyzerFactory.get_supported_extensions()
        
        for root, dirs, files in os.walk(self.project_path):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__']]
            
            for file in files:
                file_path = str(Path(root) / file)
                
                if Path(file_path).suffix in supported_extensions:
                    if file_path not in self.file_hashes:
                        changed_files.append(file_path)
        
        return changed_files
    
    def _load_file_hashes(self) -> Dict[str, str]:
        """Load file hashes from disk"""
        if self.hash_file.exists():
            try:
                with open(self.hash_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load file hashes: {e}")
        
        return {}
    
    def _save_file_hashes(self) -> None:
        """Save file hashes to disk"""
        try:
            self.hash_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.hash_file, 'w') as f:
                json.dump(self.file_hashes, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save file hashes: {e}")