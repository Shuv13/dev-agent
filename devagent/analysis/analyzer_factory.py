"""Factory for creating appropriate code analyzers"""

from pathlib import Path
from typing import Optional

from devagent.core.interfaces import CodeAnalyzer
from .python_analyzer import PythonASTAnalyzer, PythonFrameworkDetector
from .javascript_analyzer import JavaScriptAnalyzer, JavaScriptFrameworkDetector


class AnalyzerFactory:
    """Factory for creating code analyzers based on file type"""
    
    ANALYZER_MAP = {
        '.py': PythonASTAnalyzer,
        '.js': JavaScriptAnalyzer,
        '.ts': JavaScriptAnalyzer,
        '.jsx': JavaScriptAnalyzer,
        '.tsx': JavaScriptAnalyzer,
    }
    
    FRAMEWORK_DETECTOR_MAP = {
        'python': PythonFrameworkDetector,
        'javascript': JavaScriptFrameworkDetector,
        'typescript': JavaScriptFrameworkDetector,
    }
    
    @classmethod
    def create_analyzer(cls, file_path: str) -> Optional[CodeAnalyzer]:
        """Create appropriate analyzer for file type"""
        path = Path(file_path)
        extension = path.suffix.lower()
        
        analyzer_class = cls.ANALYZER_MAP.get(extension)
        if analyzer_class:
            # For JavaScript/TypeScript, check if tree-sitter is available
            if analyzer_class == JavaScriptAnalyzer:
                try:
                    return analyzer_class()
                except ImportError:
                    print(f"Warning: Tree-sitter not available for {file_path}, skipping JavaScript analysis")
                    return None
            else:
                return analyzer_class()
        
        return None
    
    @classmethod
    def create_framework_detector(cls, language: str):
        """Create appropriate framework detector for language"""
        detector_class = cls.FRAMEWORK_DETECTOR_MAP.get(language.lower())
        if detector_class:
            return detector_class()
        
        return None
    
    @classmethod
    def get_supported_extensions(cls) -> list:
        """Get list of supported file extensions"""
        return list(cls.ANALYZER_MAP.keys())
    
    @classmethod
    def is_supported(cls, file_path: str) -> bool:
        """Check if file type is supported"""
        path = Path(file_path)
        extension = path.suffix.lower()
        
        if extension not in cls.ANALYZER_MAP:
            return False
        
        # For JavaScript/TypeScript, check if tree-sitter is available
        if cls.ANALYZER_MAP[extension] == JavaScriptAnalyzer:
            try:
                import tree_sitter_javascript
                import tree_sitter_typescript
                return True
            except ImportError:
                return False
        
        return True
    
    @classmethod
    def detect_language(cls, file_path: str) -> Optional[str]:
        """Detect programming language from file extension"""
        path = Path(file_path)
        extension = path.suffix.lower()
        
        if extension == '.py':
            return 'python'
        elif extension in ['.js', '.jsx']:
            return 'javascript'
        elif extension in ['.ts', '.tsx']:
            return 'typescript'
        
        return None