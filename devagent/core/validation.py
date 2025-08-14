"""Input validation and data validation utilities"""

import os
import re
from pathlib import Path
from typing import List, Optional, Union, Tuple
import ast


# Import from error_handling module
from .error_handling import ValidationError


class InputValidator:
    """Validates user inputs and command parameters"""
    
    SUPPORTED_EXTENSIONS = {'.py', '.js', '.ts', '.java', '.go', '.rs', '.cs'}
    SUPPORTED_FORMATS = {'markdown', 'rst', 'docstring'}
    SUPPORTED_REFACTOR_TYPES = {'extract-method', 'rename-variable', 'optimize', 'modernize'}
    
    @staticmethod
    def validate_file_path(file_path: str) -> Path:
        """Validate and normalize file path"""
        if not file_path:
            raise ValidationError("File path cannot be empty")
        
        path = Path(file_path)
        
        # Check if file exists
        if not path.exists():
            raise ValidationError(f"File does not exist: {file_path}")
        
        # Check if it's a file (not directory)
        if not path.is_file():
            raise ValidationError(f"Path is not a file: {file_path}")
        
        # Check file extension
        if path.suffix not in InputValidator.SUPPORTED_EXTENSIONS:
            raise ValidationError(
                f"Unsupported file extension: {path.suffix}. "
                f"Supported: {', '.join(InputValidator.SUPPORTED_EXTENSIONS)}"
            )
        
        return path.resolve()
    
    @staticmethod
    def validate_function_name(function_name: str) -> str:
        """Validate function name format"""
        if not function_name:
            raise ValidationError("Function name cannot be empty")
        
        # Check if it's a valid Python identifier
        if not function_name.isidentifier():
            raise ValidationError(f"Invalid function name format: {function_name}")
        
        return function_name
    
    @staticmethod
    def validate_directory_path(dir_path: str) -> Path:
        """Validate directory path"""
        if not dir_path:
            raise ValidationError("Directory path cannot be empty")
        
        path = Path(dir_path)
        
        if not path.exists():
            raise ValidationError(f"Directory does not exist: {dir_path}")
        
        if not path.is_dir():
            raise ValidationError(f"Path is not a directory: {dir_path}")
        
        return path.resolve()
    
    @staticmethod
    def validate_output_format(format_name: str) -> str:
        """Validate output format"""
        if not format_name:
            raise ValidationError("Output format cannot be empty")
        
        format_name = format_name.lower()
        if format_name not in InputValidator.SUPPORTED_FORMATS:
            raise ValidationError(
                f"Unsupported format: {format_name}. "
                f"Supported: {', '.join(InputValidator.SUPPORTED_FORMATS)}"
            )
        
        return format_name
    
    @staticmethod
    def validate_refactor_type(refactor_type: str) -> str:
        """Validate refactoring type"""
        if not refactor_type:
            raise ValidationError("Refactor type cannot be empty")
        
        refactor_type = refactor_type.lower()
        if refactor_type not in InputValidator.SUPPORTED_REFACTOR_TYPES:
            raise ValidationError(
                f"Unsupported refactor type: {refactor_type}. "
                f"Supported: {', '.join(InputValidator.SUPPORTED_REFACTOR_TYPES)}"
            )
        
        return refactor_type
    
    @staticmethod
    def validate_project_path(project_path: str) -> Path:
        """Validate project root path"""
        path = InputValidator.validate_directory_path(project_path)
        
        # Check if it looks like a code project (has common files/directories)
        common_indicators = [
            'setup.py', 'pyproject.toml', 'package.json', 'Cargo.toml',
            'pom.xml', 'build.gradle', '.git', 'src', 'lib'
        ]
        
        has_indicator = any((path / indicator).exists() for indicator in common_indicators)
        if not has_indicator:
            raise ValidationError(
                f"Directory does not appear to be a code project: {project_path}"
            )
        
        return path


class CodeValidator:
    """Validates generated code and syntax"""
    
    @staticmethod
    def validate_python_syntax(code: str) -> Tuple[bool, List[str]]:
        """Validate Python code syntax"""
        errors = []
        
        try:
            ast.parse(code)
            return True, errors
        except SyntaxError as e:
            errors.append(f"Syntax error at line {e.lineno}: {e.msg}")
            return False, errors
        except Exception as e:
            errors.append(f"Parse error: {str(e)}")
            return False, errors
    
    @staticmethod
    def validate_javascript_syntax(code: str) -> Tuple[bool, List[str]]:
        """Basic JavaScript syntax validation"""
        errors = []
        
        # Basic checks for common syntax issues
        if code.count('{') != code.count('}'):
            errors.append("Mismatched curly braces")
        
        if code.count('(') != code.count(')'):
            errors.append("Mismatched parentheses")
        
        if code.count('[') != code.count(']'):
            errors.append("Mismatched square brackets")
        
        # Check for unterminated strings
        single_quotes = code.count("'") - code.count("\\'")
        double_quotes = code.count('"') - code.count('\\"')
        
        if single_quotes % 2 != 0:
            errors.append("Unterminated single-quoted string")
        
        if double_quotes % 2 != 0:
            errors.append("Unterminated double-quoted string")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_code_syntax(code: str, language: str) -> Tuple[bool, List[str]]:
        """Validate code syntax based on language"""
        language = language.lower()
        
        if language == 'python':
            return CodeValidator.validate_python_syntax(code)
        elif language in ['javascript', 'typescript']:
            return CodeValidator.validate_javascript_syntax(code)
        else:
            # For unsupported languages, just check basic structure
            return True, []
    
    @staticmethod
    def check_code_style(code: str, language: str) -> Tuple[bool, List[str]]:
        """Basic code style checking"""
        warnings = []
        
        if language == 'python':
            # Check for basic PEP 8 violations
            lines = code.split('\n')
            for i, line in enumerate(lines, 1):
                if len(line) > 88:  # Line too long
                    warnings.append(f"Line {i}: Line too long ({len(line)} > 88 characters)")
                
                if line.endswith(' '):  # Trailing whitespace
                    warnings.append(f"Line {i}: Trailing whitespace")
                
                if '\t' in line:  # Tabs instead of spaces
                    warnings.append(f"Line {i}: Use spaces instead of tabs")
        
        return len(warnings) == 0, warnings


class ConfigValidator:
    """Validates configuration values"""
    
    @staticmethod
    def validate_llm_provider(provider: str) -> str:
        """Validate LLM provider"""
        supported_providers = {'openai', 'ollama', 'anthropic'}
        
        if not provider:
            raise ValidationError("LLM provider cannot be empty")
        
        provider = provider.lower()
        if provider not in supported_providers:
            raise ValidationError(
                f"Unsupported LLM provider: {provider}. "
                f"Supported: {', '.join(supported_providers)}"
            )
        
        return provider
    
    @staticmethod
    def validate_api_key_env(env_var: str) -> str:
        """Validate API key environment variable"""
        if not env_var:
            raise ValidationError("API key environment variable cannot be empty")
        
        if not re.match(r'^[A-Z_][A-Z0-9_]*$', env_var):
            raise ValidationError(
                f"Invalid environment variable name: {env_var}. "
                "Should contain only uppercase letters, numbers, and underscores"
            )
        
        return env_var
    
    @staticmethod
    def validate_model_name(model: str) -> str:
        """Validate model name"""
        if not model:
            raise ValidationError("Model name cannot be empty")
        
        # Basic validation - model names should be reasonable strings
        if len(model) > 100:
            raise ValidationError("Model name too long")
        
        return model