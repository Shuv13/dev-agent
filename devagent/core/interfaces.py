"""Core interfaces and abstract base classes"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class CodeChunk:
    """Represents a chunk of code with metadata"""
    content: str
    file_path: str
    start_line: int
    end_line: int
    chunk_type: str  # 'function', 'class', 'module'
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None


@dataclass
class Task:
    """Represents a user task to be executed"""
    command: str
    target_file: Optional[str]
    target_function: Optional[str]
    parameters: Dict[str, Any]
    context_requirements: List[str]


@dataclass
class TaskResult:
    """Result of task execution"""
    success: bool
    generated_files: List[str]
    modified_files: List[str]
    output_message: str
    validation_results: Optional[Dict[str, Any]] = None


class CodeAnalyzer(ABC):
    """Abstract base class for code analyzers"""
    
    @abstractmethod
    def analyze_function(self, file_path: str, function_name: str) -> Dict[str, Any]:
        """Analyze a specific function"""
        pass
    
    @abstractmethod
    def extract_functions(self, file_path: str) -> List[Dict[str, Any]]:
        """Extract all functions from a file"""
        pass


class ContextEngine(ABC):
    """Abstract base class for context engines"""
    
    @abstractmethod
    def index_codebase(self, project_path: str) -> None:
        """Index the entire codebase"""
        pass
    
    @abstractmethod
    def get_relevant_context(self, query: str, k: int = 5) -> List[CodeChunk]:
        """Get relevant code chunks for a query"""
        pass


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    @abstractmethod
    def generate_code(self, prompt: str, context: str, max_tokens: int = 4000) -> str:
        """Generate code with given prompt and context"""
        pass
    
    @abstractmethod
    def analyze_code(self, code: str, task: str) -> Dict[str, Any]:
        """Analyze code for specific task requirements"""
        pass


class Agent(ABC):
    """Abstract base class for agents"""
    
    @abstractmethod
    def execute_task(self, task: Task) -> TaskResult:
        """Execute a given task"""
        pass