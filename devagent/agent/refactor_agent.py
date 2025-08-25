"""Code refactoring agent implementation"""

import shutil
from pathlib import Path
from typing import List, Optional, Dict, Any

from devagent.core.interfaces import Agent, Task, TaskResult
from devagent.analysis.analyzer_factory import AnalyzerFactory
from devagent.context.context_engine import DevAgentContextEngine
from devagent.llm.providers import LLMProviderFactory
from devagent.llm.prompts import RefactoringPrompts
from devagent.core.validation import CodeValidator


class RefactoringAgent(Agent):
    """Agent for intelligent code refactoring"""
    
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
        self.code_validator = CodeValidator()
    
    def execute_task(self, task: Task) -> TaskResult:
        """Execute refactoring task"""
        try:
            file_path = task.target_file
            refactor_type = task.parameters['type']
            function_name = task.parameters.get('function')
            preview = task.parameters.get('preview', False)
            backup = task.parameters.get('backup', True)
            
            # Initialize context engine
            project_path = self._find_project_root(file_path)
            self.context_engine = DevAgentContextEngine(project_path)
            
            # Create backup if requested and not in preview mode
            if backup and not preview:
                self._create_backup(file_path)
            
            if function_name:
                return self._refactor_function(file_path, function_name, refactor_type, preview)
            else:
                return self._refactor_file(file_path, refactor_type, preview)
                
        except Exception as e:
            return TaskResult(
                success=False,
                generated_files=[],
                modified_files=[],
                output_message=f"Refactoring failed: {str(e)}"
            )
    
    def _refactor_function(self, file_path: str, function_name: str, refactor_type: str, preview: bool) -> TaskResult:
        """Refactor a specific function"""
        # Analyze the function
        analyzer = AnalyzerFactory.create_analyzer(file_path)
        if not analyzer:
            raise ValueError(f"Unsupported file type: {file_path}")
        
        function_analysis = analyzer.analyze_function(file_path, function_name)
        
        # Get function code
        with open(file_path, 'r') as f:
            lines = f.readlines()
            original_code = ''.join(lines[function_analysis.start_line-1:function_analysis.end_line])
        
        # Get context
        context = self.context_engine.get_function_context(file_path, function_name, k=5)
        
        # Generate refactoring prompt
        language = AnalyzerFactory.detect_language(file_path)
        prompt = RefactoringPrompts.create_refactor_prompt(
            refactor_type=refactor_type,
            original_code=original_code,
            language=language,
            function_name=function_name,
            complexity=function_analysis.complexity_score,
            context=context
        )
        
        # Generate refactored code
        refactored_code = self.llm_provider.generate_code(prompt)
        
        # Validate refactored code
        is_valid, errors = self.code_validator.validate_code_syntax(refactored_code, language)
        if not is_valid:
            # Try to fix issues
            fix_prompt = f"Fix syntax errors in refactored code:\n\nErrors: {errors}\n\nCode:\n{refactored_code}\n\nGenerate corrected code:"
            refactored_code = self.llm_provider.generate_code(fix_prompt)
        
        if preview:
            return TaskResult(
                success=True,
                generated_files=[],
                modified_files=[],
                output_message=f"Preview of refactored function '{function_name}':\n\n{refactored_code}",
                validation_results={
                    'original_code': original_code,
                    'refactored_code': refactored_code,
                    'refactor_type': refactor_type
                }
            )
        else:
            # Apply refactoring
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            # Replace the function in the file using line numbers
            start_line = function_analysis.start_line - 1
            end_line = function_analysis.end_line

            new_lines = lines[:start_line]
            new_lines.extend(refactored_code.splitlines(True))
            new_lines.extend(lines[end_line:])
            
            with open(file_path, 'w') as f:
                f.writelines(new_lines)
            
            return TaskResult(
                success=True,
                generated_files=[],
                modified_files=[file_path],
                output_message=f"Refactored function '{function_name}' in {file_path}",
                validation_results={
                    'refactor_type': refactor_type,
                    'syntax_valid': is_valid
                }
            )
    
    def _refactor_file(self, file_path: str, refactor_type: str, preview: bool) -> TaskResult:
        """Refactor entire file"""
        with open(file_path, 'r') as f:
            original_code = f.read()
        
        # Get context
        context = self.context_engine.get_file_context(file_path)
        
        # Generate refactoring prompt
        language = AnalyzerFactory.detect_language(file_path)
        prompt = RefactoringPrompts.create_refactor_prompt(
            refactor_type=refactor_type,
            original_code=original_code,
            language=language,
            function_name="entire_file",
            complexity=10,  # Assume high complexity for entire file
            context=context
        )
        
        # Generate refactored code
        refactored_code = self.llm_provider.generate_code(prompt)
        
        # Validate refactored code
        is_valid, errors = self.code_validator.validate_code_syntax(refactored_code, language)
        
        if preview:
            return TaskResult(
                success=True,
                generated_files=[],
                modified_files=[],
                output_message=f"Preview of refactored file:\n\n{refactored_code[:1000]}...",
                validation_results={
                    'original_code': original_code,
                    'refactored_code': refactored_code,
                    'refactor_type': refactor_type
                }
            )
        else:
            # Apply refactoring
            with open(file_path, 'w') as f:
                f.write(refactored_code)
            
            return TaskResult(
                success=True,
                generated_files=[],
                modified_files=[file_path],
                output_message=f"Refactored entire file {file_path}",
                validation_results={
                    'refactor_type': refactor_type,
                    'syntax_valid': is_valid
                }
            )
    
    def _create_backup(self, file_path: str) -> str:
        """Create backup of file before refactoring"""
        backup_path = f"{file_path}.backup"
        shutil.copy2(file_path, backup_path)
        return backup_path
    
    def _find_project_root(self, file_path: str) -> str:
        """Find project root directory"""
        path = Path(file_path).parent
        indicators = ['setup.py', 'pyproject.toml', 'package.json', '.git']
        
        while path != path.parent:
            if any((path / indicator).exists() for indicator in indicators):
                return str(path)
            path = path.parent
        
        return str(Path(file_path).parent)