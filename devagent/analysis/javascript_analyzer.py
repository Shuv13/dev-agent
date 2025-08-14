"""JavaScript/TypeScript code analysis using Tree-sitter"""

try:
    import tree_sitter_javascript as ts_js
    import tree_sitter_typescript as ts_ts
    from tree_sitter import Language, Parser, Node
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False
from typing import List, Dict, Any, Optional
from pathlib import Path

from devagent.core.interfaces import CodeAnalyzer
from devagent.core.models import FunctionAnalysis, Parameter, FrameworkInfo


class JavaScriptAnalyzer(CodeAnalyzer):
    """JavaScript/TypeScript code analyzer using Tree-sitter"""
    
    def __init__(self):
        if not TREE_SITTER_AVAILABLE:
            raise ImportError("Tree-sitter JavaScript/TypeScript parsers not available")
        
        # Initialize Tree-sitter languages
        try:
            # Try the new API first
            self.js_language = ts_js.language()
            self.ts_language = ts_ts.language()
        except Exception as e:
            try:
                # Try with Language wrapper
                self.js_language = Language(ts_js.language())
                self.ts_language = Language(ts_ts.language())
            except Exception:
                raise ImportError(f"Could not initialize tree-sitter languages: {e}")
        
        self.js_parser = Parser()
        self.ts_parser = Parser()
        
        try:
            self.js_parser.set_language(self.js_language)
            self.ts_parser.set_language(self.ts_language)
        except:
            # Fallback for older API
            self.js_parser = Parser(self.js_language)
            self.ts_parser = Parser(self.ts_language)
    
    def analyze_function(self, file_path: str, function_name: str) -> FunctionAnalysis:
        """Analyze a specific function in detail"""
        with open(file_path, 'rb') as f:
            content = f.read()
        
        parser = self._get_parser(file_path)
        tree = parser.parse(content)
        
        function_node = self._find_function_node(tree.root_node, function_name)
        if not function_node:
            raise ValueError(f"Function '{function_name}' not found in {file_path}")
        
        return self._analyze_function_node(function_node, file_path, content.decode('utf-8'))
    
    def extract_functions(self, file_path: str) -> List[Dict[str, Any]]:
        """Extract all functions from a file"""
        with open(file_path, 'rb') as f:
            content = f.read()
        
        parser = self._get_parser(file_path)
        tree = parser.parse(content)
        
        functions = []
        self._extract_functions_recursive(tree.root_node, functions, content.decode('utf-8'))
        
        return functions
    
    def extract_classes(self, file_path: str) -> List[Dict[str, Any]]:
        """Extract all classes from a file"""
        with open(file_path, 'rb') as f:
            content = f.read()
        
        parser = self._get_parser(file_path)
        tree = parser.parse(content)
        
        classes = []
        self._extract_classes_recursive(tree.root_node, classes, content.decode('utf-8'))
        
        return classes
    
    def get_imports(self, file_path: str) -> Dict[str, List[str]]:
        """Extract all imports from a file"""
        with open(file_path, 'rb') as f:
            content = f.read()
        
        parser = self._get_parser(file_path)
        tree = parser.parse(content)
        
        imports = {
            'standard': [],
            'third_party': [],
            'local': []
        }
        
        self._extract_imports_recursive(tree.root_node, imports, content.decode('utf-8'))
        
        return imports
    
    def _get_parser(self, file_path: str) -> Parser:
        """Get appropriate parser based on file extension"""
        if file_path.endswith('.ts') or file_path.endswith('.tsx'):
            return self.ts_parser
        else:
            return self.js_parser
    
    def _find_function_node(self, node: Node, function_name: str) -> Optional[Node]:
        """Find a function node by name"""
        if node.type in ['function_declaration', 'method_definition', 'arrow_function']:
            name_node = self._get_function_name_node(node)
            if name_node and self._get_node_text(name_node).decode('utf-8') == function_name:
                return node
        
        for child in node.children:
            result = self._find_function_node(child, function_name)
            if result:
                return result
        
        return None
    
    def _extract_functions_recursive(self, node: Node, functions: List[Dict[str, Any]], content: str):
        """Recursively extract functions from AST"""
        if node.type in ['function_declaration', 'method_definition', 'arrow_function']:
            func_info = self._analyze_function_node(node, "", content)
            functions.append({
                'name': func_info.name,
                'start_line': func_info.start_line,
                'end_line': func_info.end_line,
                'parameters': [{'name': p.name, 'type': p.type_hint} for p in func_info.parameters],
                'return_type': func_info.return_type,
                'complexity': func_info.complexity_score
            })
        
        for child in node.children:
            self._extract_functions_recursive(child, functions, content)
    
    def _extract_classes_recursive(self, node: Node, classes: List[Dict[str, Any]], content: str):
        """Recursively extract classes from AST"""
        if node.type == 'class_declaration':
            class_info = {
                'name': self._get_class_name(node, content),
                'start_line': node.start_point[0] + 1,
                'end_line': node.end_point[0] + 1,
                'methods': [],
                'extends': self._get_class_extends(node, content)
            }
            
            # Extract methods
            for child in node.children:
                if child.type == 'class_body':
                    for method_node in child.children:
                        if method_node.type == 'method_definition':
                            method_info = self._analyze_function_node(method_node, "", content)
                            class_info['methods'].append({
                                'name': method_info.name,
                                'parameters': [{'name': p.name, 'type': p.type_hint} for p in method_info.parameters],
                                'return_type': method_info.return_type
                            })
            
            classes.append(class_info)
        
        for child in node.children:
            self._extract_classes_recursive(child, classes, content)
    
    def _extract_imports_recursive(self, node: Node, imports: Dict[str, List[str]], content: str):
        """Recursively extract imports from AST"""
        if node.type == 'import_statement':
            import_path = self._get_import_path(node, content)
            if import_path:
                imports[self._classify_import(import_path)].append(import_path)
        
        elif node.type == 'import_clause':
            # Handle ES6 imports
            import_path = self._get_import_path(node.parent, content)
            if import_path:
                imports[self._classify_import(import_path)].append(import_path)
        
        for child in node.children:
            self._extract_imports_recursive(child, imports, content)
    
    def _analyze_function_node(self, node: Node, file_path: str, content: str) -> FunctionAnalysis:
        """Analyze a function node"""
        # Get function name
        name_node = self._get_function_name_node(node)
        name = self._get_node_text(name_node).decode('utf-8') if name_node else 'anonymous'
        
        # Extract parameters
        parameters = []
        params_node = self._get_parameters_node(node)
        if params_node:
            for param_node in params_node.children:
                if param_node.type in ['identifier', 'required_parameter', 'optional_parameter']:
                    param_name = self._get_node_text(param_node).decode('utf-8')
                    param_type = self._get_parameter_type(param_node, content)
                    
                    parameters.append(Parameter(
                        name=param_name,
                        type_hint=param_type,
                        is_required=param_node.type != 'optional_parameter'
                    ))
        
        # Get return type (for TypeScript)
        return_type = self._get_return_type(node, content)
        
        # Calculate complexity
        complexity = self._calculate_complexity(node)
        
        # Find dependencies
        dependencies = self._find_dependencies(node, content)
        
        return FunctionAnalysis(
            name=name,
            parameters=parameters,
            return_type=return_type,
            dependencies=dependencies,
            complexity_score=complexity,
            docstring=None,  # JS/TS doesn't have docstrings like Python
            file_path=file_path,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1
        )
    
    def _get_function_name_node(self, node: Node) -> Optional[Node]:
        """Get the name node of a function"""
        if node.type == 'function_declaration':
            for child in node.children:
                if child.type == 'identifier':
                    return child
        elif node.type == 'method_definition':
            for child in node.children:
                if child.type == 'property_identifier':
                    return child
        elif node.type == 'arrow_function':
            # Arrow functions might not have names
            return None
        
        return None
    
    def _get_parameters_node(self, node: Node) -> Optional[Node]:
        """Get the parameters node of a function"""
        for child in node.children:
            if child.type == 'formal_parameters':
                return child
        return None
    
    def _get_parameter_type(self, param_node: Node, content: str) -> Optional[str]:
        """Get parameter type annotation (TypeScript)"""
        for child in param_node.children:
            if child.type == 'type_annotation':
                return self._get_node_text(child).decode('utf-8')
        return None
    
    def _get_return_type(self, node: Node, content: str) -> Optional[str]:
        """Get return type annotation (TypeScript)"""
        for child in node.children:
            if child.type == 'type_annotation':
                return self._get_node_text(child).decode('utf-8')
        return None
    
    def _get_class_name(self, node: Node, content: str) -> str:
        """Get class name"""
        for child in node.children:
            if child.type == 'type_identifier':
                return self._get_node_text(child).decode('utf-8')
        return 'anonymous'
    
    def _get_class_extends(self, node: Node, content: str) -> Optional[str]:
        """Get class extends clause"""
        for child in node.children:
            if child.type == 'class_heritage':
                for heritage_child in child.children:
                    if heritage_child.type == 'extends_clause':
                        for extends_child in heritage_child.children:
                            if extends_child.type == 'identifier':
                                return self._get_node_text(extends_child).decode('utf-8')
        return None
    
    def _get_import_path(self, node: Node, content: str) -> Optional[str]:
        """Get import path from import statement"""
        for child in node.children:
            if child.type == 'string':
                # Remove quotes
                path = self._get_node_text(child).decode('utf-8')
                return path.strip('"\'')
        return None
    
    def _calculate_complexity(self, node: Node) -> int:
        """Calculate cyclomatic complexity"""
        complexity = 1  # Base complexity
        
        def count_complexity(n: Node):
            nonlocal complexity
            if n.type in ['if_statement', 'while_statement', 'for_statement', 'for_in_statement']:
                complexity += 1
            elif n.type in ['catch_clause', 'case_clause']:
                complexity += 1
            elif n.type in ['conditional_expression', 'binary_expression']:
                # Check for logical operators
                text = self._get_node_text(n).decode('utf-8')
                if '&&' in text or '||' in text:
                    complexity += 1
            
            for child in n.children:
                count_complexity(child)
        
        count_complexity(node)
        return complexity
    
    def _find_dependencies(self, node: Node, content: str) -> List[str]:
        """Find function dependencies"""
        dependencies = set()
        
        def find_calls(n: Node):
            if n.type == 'call_expression':
                # Get function name being called
                for child in n.children:
                    if child.type == 'identifier':
                        dependencies.add(self._get_node_text(child).decode('utf-8'))
                        break
                    elif child.type == 'member_expression':
                        dependencies.add(self._get_node_text(child).decode('utf-8'))
                        break
            
            for child in n.children:
                find_calls(child)
        
        find_calls(node)
        return list(dependencies)
    
    def _classify_import(self, import_path: str) -> str:
        """Classify import as standard, third-party, or local"""
        if import_path.startswith('.'):
            return 'local'
        elif import_path.startswith('@') or '/' not in import_path:
            return 'third_party'
        else:
            return 'local'
    
    def _get_node_text(self, node: Node) -> bytes:
        """Get text content of a node"""
        return node.text


class JavaScriptFrameworkDetector:
    """Detect JavaScript/TypeScript frameworks and testing libraries"""
    
    TESTING_FRAMEWORKS = {
        'jest': ['jest', '@types/jest'],
        'mocha': ['mocha', '@types/mocha'],
        'jasmine': ['jasmine', '@types/jasmine'],
        'vitest': ['vitest'],
        'cypress': ['cypress'],
        'playwright': ['@playwright/test']
    }
    
    WEB_FRAMEWORKS = {
        'react': ['react', '@types/react'],
        'vue': ['vue', '@vue/cli'],
        'angular': ['@angular/core', '@angular/cli'],
        'svelte': ['svelte'],
        'next': ['next'],
        'nuxt': ['nuxt'],
        'express': ['express', '@types/express'],
        'fastify': ['fastify'],
        'koa': ['koa', '@types/koa']
    }
    
    def detect_testing_framework(self, project_path: str) -> FrameworkInfo:
        """Detect the testing framework used in the project"""
        project_dir = Path(project_path)
        
        # Check for configuration files
        config_files = []
        test_configs = [
            'jest.config.js', 'jest.config.ts', 'jest.config.json',
            'vitest.config.js', 'vitest.config.ts',
            'cypress.config.js', 'cypress.config.ts',
            'playwright.config.js', 'playwright.config.ts'
        ]
        
        for config in test_configs:
            if (project_dir / config).exists():
                config_files.append(config)
                framework_name = config.split('.')[0]
                return FrameworkInfo(framework_name, config_files=config_files)
        
        # Check package.json
        package_json = project_dir / 'package.json'
        dependencies = []
        
        if package_json.exists():
            try:
                import json
                with open(package_json, 'r') as f:
                    data = json.load(f)
                    
                    deps = data.get('dependencies', {})
                    dev_deps = data.get('devDependencies', {})
                    dependencies = list(deps.keys()) + list(dev_deps.keys())
            except Exception:
                pass
        
        # Determine framework based on dependencies
        for framework, indicators in self.TESTING_FRAMEWORKS.items():
            for indicator in indicators:
                if indicator in dependencies:
                    return FrameworkInfo(
                        framework,
                        config_files=config_files,
                        dependencies=dependencies
                    )
        
        # Default to jest if no specific framework detected
        return FrameworkInfo('jest', config_files=config_files)
    
    def detect_web_framework(self, project_path: str) -> Optional[FrameworkInfo]:
        """Detect web framework used in the project"""
        project_dir = Path(project_path)
        
        # Check package.json
        package_json = project_dir / 'package.json'
        dependencies = []
        
        if package_json.exists():
            try:
                import json
                with open(package_json, 'r') as f:
                    data = json.load(f)
                    
                    deps = data.get('dependencies', {})
                    dev_deps = data.get('devDependencies', {})
                    dependencies = list(deps.keys()) + list(dev_deps.keys())
            except Exception:
                pass
        
        # Check for framework-specific files
        if (project_dir / 'angular.json').exists():
            return FrameworkInfo('angular', config_files=['angular.json'])
        
        if (project_dir / 'next.config.js').exists():
            return FrameworkInfo('next', config_files=['next.config.js'])
        
        if (project_dir / 'nuxt.config.js').exists():
            return FrameworkInfo('nuxt', config_files=['nuxt.config.js'])
        
        # Determine framework based on dependencies
        for framework, indicators in self.WEB_FRAMEWORKS.items():
            for indicator in indicators:
                if indicator in dependencies:
                    return FrameworkInfo(framework, dependencies=dependencies)
        
        return None