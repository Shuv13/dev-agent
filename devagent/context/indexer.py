"""Code indexing for context retrieval"""

import os
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from sentence_transformers import SentenceTransformer

from devagent.core.interfaces import CodeChunk
from devagent.analysis.analyzer_factory import AnalyzerFactory


class CodeIndexer:
    """Indexes code files for context retrieval"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.chunk_size = 1000
        self.overlap = 100
    
    def index_project(self, project_path: str, exclude_patterns: List[str] = None) -> List[CodeChunk]:
        """Index entire project directory"""
        if exclude_patterns is None:
            exclude_patterns = ["*.pyc", "__pycache__", ".git", "node_modules", ".venv", "venv"]
        
        project_dir = Path(project_path)
        code_chunks = []
        
        # Find all supported code files
        supported_extensions = AnalyzerFactory.get_supported_extensions()
        
        for file_path in self._find_code_files(project_dir, supported_extensions, exclude_patterns):
            try:
                file_chunks = self.index_file(str(file_path))
                code_chunks.extend(file_chunks)
            except Exception as e:
                print(f"Warning: Failed to index {file_path}: {e}")
                continue
        
        return code_chunks
    
    def index_file(self, file_path: str) -> List[CodeChunk]:
        """Index a single code file"""
        if not AnalyzerFactory.is_supported(file_path):
            return []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"Warning: Could not read {file_path}: {e}")
            return []
        
        chunks = []
        
        # Try to use analyzer for semantic chunking
        analyzer = AnalyzerFactory.create_analyzer(file_path)
        if analyzer:
            chunks.extend(self._create_semantic_chunks(file_path, content, analyzer))
        
        # Also create text-based chunks for broader context
        chunks.extend(self._create_text_chunks(file_path, content))
        
        # Generate embeddings for all chunks
        for chunk in chunks:
            chunk.embedding = self._generate_embedding(chunk.content)
        
        return chunks
    
    def _find_code_files(self, project_dir: Path, extensions: List[str], exclude_patterns: List[str]) -> List[Path]:
        """Find all code files in project directory"""
        code_files = []
        
        for root, dirs, files in os.walk(project_dir):
            # Filter out excluded directories
            dirs[:] = [d for d in dirs if not self._should_exclude(d, exclude_patterns)]
            
            for file in files:
                file_path = Path(root) / file
                
                # Check if file should be excluded
                if self._should_exclude(str(file_path), exclude_patterns):
                    continue
                
                # Check if file has supported extension
                if file_path.suffix in extensions:
                    code_files.append(file_path)
        
        return code_files
    
    def _should_exclude(self, path: str, exclude_patterns: List[str]) -> bool:
        """Check if path should be excluded based on patterns"""
        import fnmatch
        
        for pattern in exclude_patterns:
            if fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(os.path.basename(path), pattern):
                return True
        
        return False
    
    def _create_semantic_chunks(self, file_path: str, content: str, analyzer) -> List[CodeChunk]:
        """Create semantic chunks based on code structure"""
        chunks = []
        
        try:
            # Extract functions
            functions = analyzer.extract_functions(file_path)
            for func in functions:
                start_line = func.get('start_line', 1)
                end_line = func.get('end_line', start_line)
                
                # Extract function content
                lines = content.split('\n')
                func_content = '\n'.join(lines[start_line-1:end_line])
                
                if func_content.strip():
                    chunk = CodeChunk(
                        content=func_content,
                        file_path=file_path,
                        start_line=start_line,
                        end_line=end_line,
                        chunk_type='function',
                        metadata={
                            'name': func['name'],
                            'parameters': func.get('parameters', []),
                            'complexity': func.get('complexity', 1)
                        }
                    )
                    chunks.append(chunk)
            
            # Extract classes
            if hasattr(analyzer, 'extract_classes'):
                classes = analyzer.extract_classes(file_path)
                for cls in classes:
                    start_line = cls.get('start_line', 1)
                    end_line = cls.get('end_line', start_line)
                    
                    # Extract class content
                    lines = content.split('\n')
                    class_content = '\n'.join(lines[start_line-1:end_line])
                    
                    if class_content.strip():
                        chunk = CodeChunk(
                            content=class_content,
                            file_path=file_path,
                            start_line=start_line,
                            end_line=end_line,
                            chunk_type='class',
                            metadata={
                                'name': cls['name'],
                                'methods': cls.get('methods', [])
                            }
                        )
                        chunks.append(chunk)
        
        except Exception as e:
            print(f"Warning: Failed to create semantic chunks for {file_path}: {e}")
        
        return chunks
    
    def _create_text_chunks(self, file_path: str, content: str) -> List[CodeChunk]:
        """Create text-based chunks with overlap"""
        chunks = []
        lines = content.split('\n')
        
        if len(content) <= self.chunk_size:
            # File is small enough to be one chunk
            chunk = CodeChunk(
                content=content,
                file_path=file_path,
                start_line=1,
                end_line=len(lines),
                chunk_type='file',
                metadata={'total_lines': len(lines)}
            )
            chunks.append(chunk)
            return chunks
        
        # Split into overlapping chunks
        start = 0
        chunk_num = 0
        
        while start < len(content):
            end = min(start + self.chunk_size, len(content))
            chunk_content = content[start:end]
            
            # Find line boundaries
            start_line = content[:start].count('\n') + 1
            end_line = content[:end].count('\n') + 1
            
            chunk = CodeChunk(
                content=chunk_content,
                file_path=file_path,
                start_line=start_line,
                end_line=end_line,
                chunk_type='text',
                metadata={
                    'chunk_number': chunk_num,
                    'total_chars': len(chunk_content)
                }
            )
            chunks.append(chunk)
            
            # Move start position with overlap
            start = end - self.overlap
            chunk_num += 1
            
            # Avoid infinite loop
            if start >= end - self.overlap:
                break
        
        return chunks
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text"""
        try:
            embedding = self.model.encode(text, convert_to_tensor=False)
            return embedding.tolist()
        except Exception as e:
            print(f"Warning: Failed to generate embedding: {e}")
            return []
    
    def get_file_hash(self, file_path: str) -> str:
        """Get hash of file content for change detection"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
                return hashlib.md5(content).hexdigest()
        except Exception:
            return ""
    
    def should_reindex_file(self, file_path: str, stored_hash: str) -> bool:
        """Check if file should be reindexed based on content hash"""
        current_hash = self.get_file_hash(file_path)
        return current_hash != stored_hash