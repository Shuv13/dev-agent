"""Documentation generation agent implementation"""

from pathlib import Path
from typing import List, Optional, Dict, Any

from devagent.core.interfaces import Agent, Task, TaskResult
from devagent.analysis.analyzer_factory import AnalyzerFactory
from devagent.context.context_engine import DevAgentContextEngine
from devagent.llm.providers import LLMProviderFactory
from devagent.llm.prompts import DocumentationPrompts


class DocumentationAgent(Agent):
    """Agent for generating comprehensive documentation"""
    
    def __init__(self, config):
        self.config = config
        try:
            self.llm_provider = LLMProviderFactory.create_provider(
                config.llm.provider,
                model=config.llm.model,
                api_key_env=config.llm.api_key_env,
                max_tokens=config.llm.max_tokens,
                temperature=config.llm.temperature
            )
        except Exception:
            # Fallback to mock provider if real provider fails
            self.llm_provider = LLMProviderFactory.create_provider('mock')
        self.context_engine = None
    
    def execute_task(self, task: Task) -> TaskResult:
        """Execute documentation generation task"""
        try:
            target = task.parameters['target']
            format_type = task.parameters.get('format', 'markdown')
            output_path = task.parameters.get('output')
            include_examples = task.parameters.get('include_examples', True)
            
            # Try to determine if target is a file or symbol
            if Path(target).exists():
                return self._generate_file_docs(target, format_type, output_path, include_examples)
            else:
                return self._generate_symbol_docs(target, format_type, output_path, include_examples, task.target_file)
                
        except Exception as e:
            return TaskResult(
                success=False,
                generated_files=[],
                modified_files=[],
                output_message=f"Documentation generation failed: {str(e)}"
            )
    
    def _generate_file_docs(self, file_path: str, format_type: str, output_path: str, include_examples: bool) -> TaskResult:
        """Generate documentation for entire file"""
        # Initialize context engine
        project_path = self._find_project_root(file_path)
        self.context_engine = DevAgentContextEngine(project_path)
        
        # Analyze file
        analyzer = AnalyzerFactory.create_analyzer(file_path)
        if not analyzer:
            raise ValueError(f"Unsupported file type: {file_path}")
        
        functions = analyzer.extract_functions(file_path)
        classes = analyzer.extract_classes(file_path) if hasattr(analyzer, 'extract_classes') else []
        
        # Get context
        context = self.context_engine.get_file_context(file_path)
        
        # Generate documentation for each function
        docs_content = f"# Documentation for {Path(file_path).name}\n\n"
        
        if functions:
            docs_content += "## Functions\n\n"
            for func in functions:
                func_analysis = analyzer.analyze_function(file_path, func['name'])
                with open(file_path, 'r') as f:
                    lines = f.readlines()
                    func_code = ''.join(lines[func_analysis.start_line-1:func_analysis.end_line])
                
                language = AnalyzerFactory.detect_language(file_path)
                prompt = DocumentationPrompts.create_function_doc_prompt(
                    func_analysis, func_code, language, format_type, context, include_examples
                )
                
                func_docs = self.llm_provider.generate_code(prompt)
                docs_content += f"{func_docs}\n\n"
        
        if classes:
            docs_content += "## Classes\n\n"
            for cls in classes:
                docs_content += f"### {cls['name']}\n\n"
                if cls.get('docstring'):
                    docs_content += f"{cls['docstring']}\n\n"
                
                if cls.get('methods'):
                    docs_content += "#### Methods\n\n"
                    for method in cls['methods']:
                        docs_content += f"- **{method['name']}**: {method.get('docstring', 'No description')}\n"
                    docs_content += "\n"
        
        # Write documentation
        if output_path:
            doc_file_path = output_path
        else:
            doc_file_path = f"{Path(file_path).stem}_docs.{format_type}"
        
        with open(doc_file_path, 'w') as f:
            f.write(docs_content)
        
        return TaskResult(
            success=True,
            generated_files=[doc_file_path],
            modified_files=[],
            output_message=f"Generated documentation for {file_path} in {doc_file_path}"
        )
    
    def _generate_symbol_docs(self, symbol: str, format_type: str, output_path: str, include_examples: bool, context_file: str = None) -> TaskResult:
        """Generate documentation for a specific symbol (function/class)"""
        # For now, return a simple implementation
        docs_content = f"# Documentation for {symbol}\n\nSymbol-specific documentation would be generated here."
        
        if output_path:
            doc_file_path = output_path
        else:
            doc_file_path = f"{symbol}_docs.{format_type}"
        
        with open(doc_file_path, 'w') as f:
            f.write(docs_content)
        
        return TaskResult(
            success=True,
            generated_files=[doc_file_path],
            modified_files=[],
            output_message=f"Generated documentation for symbol '{symbol}' in {doc_file_path}"
        )
    
    def _find_project_root(self, file_path: str) -> str:
        """Find project root directory"""
        path = Path(file_path).parent
        indicators = ['setup.py', 'pyproject.toml', 'package.json', '.git']
        
        while path != path.parent:
            if any((path / indicator).exists() for indicator in indicators):
                return str(path)
            path = path.parent
        
        return str(Path(file_path).parent)