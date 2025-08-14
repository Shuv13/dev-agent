"""Prompt templates for different tasks"""

from typing import Dict, Any, List, Optional
from devagent.core.interfaces import CodeChunk
from devagent.core.models import FunctionAnalysis, TestPatterns


class PromptTemplate:
    """Base class for prompt templates"""
    
    def __init__(self, template: str):
        self.template = template
    
    def format(self, **kwargs) -> str:
        """Format template with provided arguments"""
        return self.template.format(**kwargs)


class TestGenerationPrompts:
    """Prompts for test generation"""
    
    FUNCTION_TEST_TEMPLATE = """
Generate comprehensive unit tests for the following function:

Function to test:
```{language}
{function_code}
```

Function Analysis:
- Name: {function_name}
- Parameters: {parameters}
- Return Type: {return_type}
- Complexity: {complexity}
- Dependencies: {dependencies}

Existing Test Patterns (for reference):
{test_patterns}

Context from codebase:
{context}

Requirements:
1. Generate tests that achieve >80% code coverage
2. Include happy path, edge cases, and error conditions
3. Mock external dependencies appropriately
4. Follow the existing test patterns and naming conventions
5. Use the detected testing framework: {framework}
6. Include appropriate setup/teardown if needed

Generate complete, runnable test code:
"""

    DIRECTORY_TEST_TEMPLATE = """
Generate comprehensive unit tests for all functions in the following directory:

Files and Functions:
{files_and_functions}

Testing Framework: {framework}
Test Patterns: {test_patterns}

Context from codebase:
{context}

Requirements:
1. Generate tests for all public functions
2. Organize tests in appropriate test files
3. Include integration tests where appropriate
4. Follow existing patterns and conventions
5. Mock external dependencies
6. Achieve high test coverage

Generate complete test suite:
"""

    @staticmethod
    def create_function_test_prompt(
        function_analysis: FunctionAnalysis,
        function_code: str,
        language: str,
        framework: str,
        test_patterns: List[CodeChunk],
        context: List[CodeChunk]
    ) -> str:
        """Create prompt for function test generation"""
        
        # Format parameters
        params_str = ", ".join([
            f"{p.name}: {p.type_hint or 'Any'}" + (f" = {p.default_value}" if p.default_value else "")
            for p in function_analysis.parameters
        ])
        
        # Format dependencies
        deps_str = ", ".join(function_analysis.dependencies) if function_analysis.dependencies else "None"
        
        # Format test patterns
        patterns_str = "\n\n".join([
            f"Pattern from {chunk.file_path}:\n```{language}\n{chunk.content}\n```"
            for chunk in test_patterns[:3]  # Limit to 3 patterns
        ]) if test_patterns else "No existing test patterns found"
        
        # Format context
        context_str = "\n\n".join([
            f"From {chunk.file_path}:\n```{language}\n{chunk.content}\n```"
            for chunk in context[:5]  # Limit to 5 context chunks
        ]) if context else "No additional context"
        
        return TestGenerationPrompts.FUNCTION_TEST_TEMPLATE.format(
            language=language,
            function_code=function_code,
            function_name=function_analysis.name,
            parameters=params_str,
            return_type=function_analysis.return_type or "Unknown",
            complexity=function_analysis.complexity_score,
            dependencies=deps_str,
            test_patterns=patterns_str,
            context=context_str,
            framework=framework
        )


class DocumentationPrompts:
    """Prompts for documentation generation"""
    
    FUNCTION_DOC_TEMPLATE = """
Generate comprehensive documentation for the following function:

Function:
```{language}
{function_code}
```

Function Analysis:
- Name: {function_name}
- Parameters: {parameters}
- Return Type: {return_type}
- Complexity: {complexity}

Context from codebase:
{context}

Requirements:
1. Generate documentation in {format} format
2. Include clear description of functionality
3. Document all parameters with types and descriptions
4. Document return value
5. Include practical usage examples
6. Add any relevant notes about complexity or performance
7. Follow the project's documentation standards

Generate complete documentation:
"""

    MODULE_DOC_TEMPLATE = """
Generate comprehensive documentation for the following module:

Module: {module_name}
File: {file_path}

Functions:
{functions}

Classes:
{classes}

Context from codebase:
{context}

Requirements:
1. Generate documentation in {format} format
2. Include module overview and purpose
3. Document all public functions and classes
4. Include usage examples
5. Add installation/import instructions if relevant
6. Follow documentation best practices

Generate complete module documentation:
"""

    @staticmethod
    def create_function_doc_prompt(
        function_analysis: FunctionAnalysis,
        function_code: str,
        language: str,
        format: str,
        context: List[CodeChunk],
        include_examples: bool = True
    ) -> str:
        """Create prompt for function documentation"""
        
        # Format parameters
        params_str = "\n".join([
            f"- {p.name} ({p.type_hint or 'Any'}): {p.default_value if p.default_value else 'Required'}"
            for p in function_analysis.parameters
        ]) if function_analysis.parameters else "None"
        
        # Format context
        context_str = "\n\n".join([
            f"From {chunk.file_path}:\n```{language}\n{chunk.content}\n```"
            for chunk in context[:3]  # Limit to 3 context chunks
        ]) if context else "No additional context"
        
        return DocumentationPrompts.FUNCTION_DOC_TEMPLATE.format(
            language=language,
            function_code=function_code,
            function_name=function_analysis.name,
            parameters=params_str,
            return_type=function_analysis.return_type or "Unknown",
            complexity=function_analysis.complexity_score,
            context=context_str,
            format=format
        )


class RefactoringPrompts:
    """Prompts for code refactoring"""
    
    EXTRACT_METHOD_TEMPLATE = """
Refactor the following code by extracting methods to improve readability and maintainability:

Original Code:
```{language}
{original_code}
```

Function Analysis:
- Name: {function_name}
- Complexity: {complexity}
- Lines of Code: {lines_of_code}

Context from codebase:
{context}

Requirements:
1. Extract logical blocks into separate methods
2. Maintain the same functionality and behavior
3. Improve code readability and maintainability
4. Follow {language} best practices and naming conventions
5. Preserve all existing functionality
6. Add appropriate docstrings to new methods
7. Ensure backward compatibility

Generate refactored code:
"""

    OPTIMIZE_TEMPLATE = """
Optimize the following code for better performance and maintainability:

Original Code:
```{language}
{original_code}
```

Function Analysis:
- Name: {function_name}
- Complexity: {complexity}
- Current Issues: {issues}

Context from codebase:
{context}

Requirements:
1. Improve performance where possible
2. Reduce complexity and improve readability
3. Follow {language} best practices
4. Maintain the same functionality
5. Add comments explaining optimizations
6. Ensure backward compatibility
7. Consider memory usage and efficiency

Generate optimized code:
"""

    MODERNIZE_TEMPLATE = """
Modernize the following code to use current {language} features and best practices:

Original Code:
```{language}
{original_code}
```

Context from codebase:
{context}

Requirements:
1. Update to modern {language} syntax and features
2. Improve type hints and annotations
3. Use current best practices and patterns
4. Maintain backward compatibility where possible
5. Improve error handling
6. Add appropriate documentation
7. Follow current style guidelines

Generate modernized code:
"""

    @staticmethod
    def create_refactor_prompt(
        refactor_type: str,
        original_code: str,
        language: str,
        function_name: str,
        complexity: int,
        context: List[CodeChunk],
        **kwargs
    ) -> str:
        """Create prompt for code refactoring"""
        
        # Format context
        context_str = "\n\n".join([
            f"From {chunk.file_path}:\n```{language}\n{chunk.content}\n```"
            for chunk in context[:3]  # Limit to 3 context chunks
        ]) if context else "No additional context"
        
        if refactor_type == "extract-method":
            return RefactoringPrompts.EXTRACT_METHOD_TEMPLATE.format(
                language=language,
                original_code=original_code,
                function_name=function_name,
                complexity=complexity,
                lines_of_code=len(original_code.split('\n')),
                context=context_str
            )
        elif refactor_type == "optimize":
            issues = kwargs.get('issues', 'High complexity, potential performance issues')
            return RefactoringPrompts.OPTIMIZE_TEMPLATE.format(
                language=language,
                original_code=original_code,
                function_name=function_name,
                complexity=complexity,
                issues=issues,
                context=context_str
            )
        elif refactor_type == "modernize":
            return RefactoringPrompts.MODERNIZE_TEMPLATE.format(
                language=language,
                original_code=original_code,
                context=context_str
            )
        else:
            raise ValueError(f"Unknown refactor type: {refactor_type}")


class GeneralPrompts:
    """General purpose prompts"""
    
    CODE_EXPLANATION_TEMPLATE = """
Explain the following code in detail:

Code:
```{language}
{code}
```

Context:
{context}

Please provide:
1. High-level overview of what the code does
2. Step-by-step explanation of the logic
3. Purpose of each major section
4. Any notable patterns or techniques used
5. Potential improvements or concerns

Explanation:
"""

    CODE_REVIEW_TEMPLATE = """
Perform a code review of the following code:

Code:
```{language}
{code}
```

Context from codebase:
{context}

Please review for:
1. Code quality and best practices
2. Potential bugs or issues
3. Performance considerations
4. Security concerns
5. Maintainability and readability
6. Consistency with codebase patterns

Provide detailed feedback with specific suggestions for improvement:
"""

    @staticmethod
    def create_explanation_prompt(code: str, language: str, context: List[CodeChunk]) -> str:
        """Create prompt for code explanation"""
        context_str = "\n\n".join([
            f"From {chunk.file_path}:\n```{language}\n{chunk.content}\n```"
            for chunk in context[:3]
        ]) if context else "No additional context"
        
        return GeneralPrompts.CODE_EXPLANATION_TEMPLATE.format(
            language=language,
            code=code,
            context=context_str
        )
    
    @staticmethod
    def create_review_prompt(code: str, language: str, context: List[CodeChunk]) -> str:
        """Create prompt for code review"""
        context_str = "\n\n".join([
            f"From {chunk.file_path}:\n```{language}\n{chunk.content}\n```"
            for chunk in context[:3]
        ]) if context else "No additional context"
        
        return GeneralPrompts.CODE_REVIEW_TEMPLATE.format(
            language=language,
            code=code,
            context=context_str
        )