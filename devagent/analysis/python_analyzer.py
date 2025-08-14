"""Python code analysis using AST"""

import ast
import os
from typing import List, Dict, Any, Optional, Set
from pathlib import Path

from devagent.core.interfaces import CodeAnalyzer
from devagent.core.models import FunctionAnalysis, Parameter, FrameworkInfo


class PythonASTAnalyzer(CodeAnalyzer):
    """Python code analyzer using AST"""
    
    def __init__(self):
        self.builtin_functions = set(dir(__builtins__))
    
    def analyze_function(self, file_path: str, function_name: str) -> FunctionAnalysis:
        """Analyze a specific function in detail"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == function_name:
                return self._analyze_function_node(node, file_path, content)
        
        raise ValueError(f"Function '{function_name}' not found in {file_path}")
    
    def extract_functions(self, file_path: str) -> List[Dict[str, Any]]:
        """Extract all functions from a file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        functions = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_info = self._analyze_function_node(node, file_path, content)
                functions.append({
                    'name': func_info.name,
                    'start_line': func_info.start_line,
                    'end_line': func_info.end_line,
                    'parameters': func_info.parameters,
                    'return_type': func_info.return_type,
                    'docstring': func_info.docstring,
                    'complexity': func_info.complexity_score
                })
        
        return functions
    
    def extract_classes(self, file_path: str) -> List[Dict[str, Any]]:
        """Extract all classes from a file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        classes = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_info = {
                    'name': node.name,
                    'start_line': node.lineno,
                    'end_line': node.end_lineno or node.lineno,
                    'methods': [],
                    'docstring': ast.get_docstring(node),
                    'bases': [self._get_name(base) for base in node.bases]
                }
                
                # Extract methods
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        method_info = self._analyze_function_node(item, file_path, content)
                        class_info['methods'].append({
                            'name': method_info.name,
                            'parameters': method_info.parameters,
                            'return_type': method_info.return_type,
                            'docstring': method_info.docstring
                        })
                
                classes.append(class_info)
        
        return classes
    
    def get_imports(self, file_path: str) -> Dict[str, List[str]]:
        """Extract all imports from a file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        imports = {
            'standard': [],
            'third_party': [],
            'local': []
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_name = alias.name
                    imports[self._classify_import(module_name)].append(module_name)
            
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    module_name = node.module
                    imports[self._classify_import(module_name)].append(module_name)
        
        return imports
    
    def calculate_complexity(self, file_path: str) -> Dict[str, int]:
        """Calculate cyclomatic complexity for functions"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        complexities = {}
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                complexity = self._calculate_cyclomatic_complexity(node)
                complexities[node.name] = complexity
        
        return complexities
    
    def _analyze_function_node(self, node: ast.FunctionDef, file_path: str, content: str) -> FunctionAnalysis:
        """Analyze a function AST node"""
        # Extract parameters
        parameters = []
        for arg in node.args.args:
            param = Parameter(
                name=arg.arg,
                type_hint=self._get_type_annotation(arg.annotation) if arg.annotation else None,
                is_required=True
            )
            parameters.append(param)
        
        # Handle default arguments
        defaults = node.args.defaults
        if defaults:
            num_defaults = len(defaults)
            for i, default in enumerate(defaults):
                param_index = len(parameters) - num_defaults + i
                if param_index >= 0:
                    parameters[param_index].default_value = self._get_default_value(default)
                    parameters[param_index].is_required = False
        
        # Extract return type
        return_type = None
        if node.returns:
            return_type = self._get_type_annotation(node.returns)
        
        # Get docstring
        docstring = ast.get_docstring(node)
        
        # Calculate complexity
        complexity = self._calculate_cyclomatic_complexity(node)
        
        # Find dependencies
        dependencies = self._find_function_dependencies(node)
        
        return FunctionAnalysis(
            name=node.name,
            parameters=parameters,
            return_type=return_type,
            dependencies=dependencies,
            complexity_score=complexity,
            docstring=docstring,
            file_path=file_path,
            start_line=node.lineno,
            end_line=node.end_lineno or node.lineno
        )
    
    def _get_type_annotation(self, annotation) -> str:
        """Extract type annotation as string"""
        if isinstance(annotation, ast.Name):
            return annotation.id
        elif isinstance(annotation, ast.Constant):
            return str(annotation.value)
        elif isinstance(annotation, ast.Attribute):
            return f"{self._get_name(annotation.value)}.{annotation.attr}"
        elif isinstance(annotation, ast.Subscript):
            value = self._get_name(annotation.value)
            slice_val = self._get_name(annotation.slice)
            return f"{value}[{slice_val}]"
        else:
            return ast.unparse(annotation) if hasattr(ast, 'unparse') else str(annotation)
    
    def _get_default_value(self, default) -> str:
        """Extract default value as string"""
        if isinstance(default, ast.Constant):
            return repr(default.value)
        elif isinstance(default, ast.Name):
            return default.id
        else:
            return ast.unparse(default) if hasattr(ast, 'unparse') else str(default)
    
    def _get_name(self, node) -> str:
        """Get name from various AST node types"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Constant):
            return str(node.value)
        else:
            return ast.unparse(node) if hasattr(ast, 'unparse') else str(node)
    
    def _calculate_cyclomatic_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity of a function"""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, (ast.And, ast.Or)):
                complexity += 1
            elif isinstance(child, ast.comprehension):
                complexity += 1
        
        return complexity
    
    def _find_function_dependencies(self, node: ast.FunctionDef) -> List[str]:
        """Find functions and modules that this function depends on"""
        dependencies = set()
        
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    # Direct function call
                    func_name = child.func.id
                    if func_name not in self.builtin_functions:
                        dependencies.add(func_name)
                elif isinstance(child.func, ast.Attribute):
                    # Method call or module function
                    full_name = self._get_name(child.func)
                    dependencies.add(full_name)
            
            elif isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load):
                # Variable usage
                if child.id not in self.builtin_functions:
                    dependencies.add(child.id)
        
        return list(dependencies)
    
    def _classify_import(self, module_name: str) -> str:
        """Classify import as standard, third-party, or local"""
        import sys
        
        # Check if it's a standard library module
        if module_name in sys.stdlib_module_names:
            return 'standard'
        
        # Check if it starts with a dot (relative import)
        if module_name.startswith('.'):
            return 'local'
        
        # Simple heuristic: if it contains no dots or starts with common patterns
        if '.' not in module_name or module_name.split('.')[0] in ['src', 'app', 'lib']:
            return 'local'
        
        return 'third_party'


class PythonFrameworkDetector:
    """Detect Python frameworks and testing libraries"""
    
    TESTING_FRAMEWORKS = {
        'pytest': ['pytest', 'pytest-cov', 'pytest-mock'],
        'unittest': ['unittest'],
        'nose': ['nose', 'nose2'],
        'doctest': ['doctest']
    }
    
    WEB_FRAMEWORKS = {
        'django': ['django', 'Django'],
        'flask': ['flask', 'Flask'],
        'fastapi': ['fastapi', 'FastAPI'],
        'tornado': ['tornado'],
        'pyramid': ['pyramid']
    }
    
    def detect_testing_framework(self, project_path: str) -> FrameworkInfo:
        """Detect the testing framework used in the project"""
        project_dir = Path(project_path)
        
        # Check for configuration files
        config_files = []
        if (project_dir / 'pytest.ini').exists():
            config_files.append('pytest.ini')
            return FrameworkInfo('pytest', config_files=config_files)
        
        if (project_dir / 'pyproject.toml').exists():
            config_files.append('pyproject.toml')
            # Could contain pytest config
            
        if (project_dir / 'setup.cfg').exists():
            config_files.append('setup.cfg')
        
        # Check requirements files
        requirements_files = [
            'requirements.txt', 'requirements-dev.txt', 'dev-requirements.txt',
            'test-requirements.txt', 'requirements/test.txt'
        ]
        
        dependencies = []
        for req_file in requirements_files:
            req_path = project_dir / req_file
            if req_path.exists():
                with open(req_path, 'r') as f:
                    dependencies.extend(f.read().splitlines())
        
        # Check setup.py
        setup_py = project_dir / 'setup.py'
        if setup_py.exists():
            try:
                with open(setup_py, 'r') as f:
                    content = f.read()
                    dependencies.extend(self._extract_dependencies_from_setup(content))
            except Exception:
                pass
        
        # Determine framework based on dependencies
        for framework, indicators in self.TESTING_FRAMEWORKS.items():
            for indicator in indicators:
                if any(indicator in dep for dep in dependencies):
                    return FrameworkInfo(
                        framework, 
                        config_files=config_files,
                        dependencies=dependencies
                    )
        
        # Default to unittest if no specific framework detected
        return FrameworkInfo('unittest', config_files=config_files)
    
    def detect_web_framework(self, project_path: str) -> Optional[FrameworkInfo]:
        """Detect web framework used in the project"""
        project_dir = Path(project_path)
        
        # Check for Django
        if (project_dir / 'manage.py').exists():
            return FrameworkInfo('django', config_files=['manage.py'])
        
        # Check requirements and imports
        dependencies = self._get_project_dependencies(project_dir)
        
        for framework, indicators in self.WEB_FRAMEWORKS.items():
            for indicator in indicators:
                if any(indicator in dep for dep in dependencies):
                    return FrameworkInfo(framework, dependencies=dependencies)
        
        return None
    
    def _extract_dependencies_from_setup(self, content: str) -> List[str]:
        """Extract dependencies from setup.py content"""
        dependencies = []
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    if node.func.id == 'setup':
                        for keyword in node.keywords:
                            if keyword.arg in ['install_requires', 'tests_require', 'extras_require']:
                                if isinstance(keyword.value, ast.List):
                                    for item in keyword.value.elts:
                                        if isinstance(item, ast.Constant):
                                            dependencies.append(item.value)
        except Exception:
            pass
        
        return dependencies
    
    def _get_project_dependencies(self, project_dir: Path) -> List[str]:
        """Get all project dependencies from various sources"""
        dependencies = []
        
        # Check requirements files
        req_files = ['requirements.txt', 'requirements-dev.txt', 'dev-requirements.txt']
        for req_file in req_files:
            req_path = project_dir / req_file
            if req_path.exists():
                try:
                    with open(req_path, 'r') as f:
                        dependencies.extend(f.read().splitlines())
                except Exception:
                    pass
        
        # Check setup.py
        setup_py = project_dir / 'setup.py'
        if setup_py.exists():
            try:
                with open(setup_py, 'r') as f:
                    content = f.read()
                    dependencies.extend(self._extract_dependencies_from_setup(content))
            except Exception:
                pass
        
        return dependencies