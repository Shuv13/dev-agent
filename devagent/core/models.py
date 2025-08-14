"""Extended data models for DevAgent"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
import ast


@dataclass
class Parameter:
    """Function parameter information"""
    name: str
    type_hint: Optional[str] = None
    default_value: Optional[str] = None
    is_required: bool = True


@dataclass
class FunctionAnalysis:
    """Detailed function analysis results"""
    name: str
    parameters: List[Parameter]
    return_type: Optional[str]
    dependencies: List[str]
    complexity_score: int
    docstring: Optional[str]
    test_coverage: float = 0.0
    file_path: str = ""
    start_line: int = 0
    end_line: int = 0


@dataclass
class TestPatterns:
    """Test patterns detected in project"""
    framework: str  # pytest, unittest, jest, etc.
    naming_convention: str  # test_*, *_test, etc.
    directory_structure: str  # tests/, test/, __tests__/
    fixture_patterns: List[str] = field(default_factory=list)
    mock_patterns: List[str] = field(default_factory=list)
    assertion_style: str = "assert"  # assert, expect, should


@dataclass
class FrameworkInfo:
    """Detected framework information"""
    name: str
    version: Optional[str] = None
    config_files: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)


@dataclass
class ValidationResults:
    """Results of code validation"""
    syntax_valid: bool
    style_compliant: bool
    tests_pass: bool
    coverage_achieved: float
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class CodeMetrics:
    """Code quality metrics"""
    complexity: int
    maintainability_index: float
    lines_of_code: int
    test_coverage: float
    duplication_ratio: float = 0.0


@dataclass
class RefactoringResult:
    """Result of refactoring operation"""
    original_code: str
    refactored_code: str
    improvements: List[str]
    metrics_before: CodeMetrics
    metrics_after: CodeMetrics
    backward_compatible: bool = True


@dataclass
class DocumentationResult:
    """Result of documentation generation"""
    content: str
    format: str  # markdown, rst, docstring
    accuracy_score: float
    includes_examples: bool
    api_coverage: float