"""LLM provider implementations"""

import os
import time
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod

import openai
from openai import OpenAI

from devagent.core.interfaces import LLMProvider


class BaseLLMProvider(LLMProvider):
    """Base class for LLM providers"""
    
    def __init__(self, model: str, max_tokens: int = 4000, temperature: float = 0.1):
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.retry_attempts = 3
        self.retry_delay = 1.0
    
    def _retry_with_backoff(self, func, *args, **kwargs):
        """Retry function with exponential backoff"""
        for attempt in range(self.retry_attempts):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == self.retry_attempts - 1:
                    raise e
                
                wait_time = self.retry_delay * (2 ** attempt)
                print(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)


class OpenAIProvider(BaseLLMProvider):
    """OpenAI API provider"""
    
    def __init__(self, model: str = "gpt-4o-mini", api_key_env: str = "OPENAI_API_KEY", 
                 max_tokens: int = 4000, temperature: float = 0.1):
        super().__init__(model, max_tokens, temperature)
        
        api_key = os.getenv(api_key_env)
        if not api_key:
            raise ValueError(f"API key not found in environment variable: {api_key_env}")
        
        self.client = OpenAI(api_key=api_key)
    
    def generate_code(self, prompt: str, context: str = "", max_tokens: int = None) -> str:
        """Generate code using OpenAI API"""
        if max_tokens is None:
            max_tokens = self.max_tokens
        
        # Construct the full prompt
        full_prompt = self._construct_prompt(prompt, context)
        
        def _make_request():
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert software developer. Generate clean, well-documented code that follows best practices."},
                    {"role": "user", "content": full_prompt}
                ],
                max_tokens=max_tokens,
                temperature=self.temperature
            )
            return response.choices[0].message.content
        
        return self._retry_with_backoff(_make_request)
    
    def analyze_code(self, code: str, task: str) -> Dict[str, Any]:
        """Analyze code for specific task requirements"""
        prompt = f"""
Analyze the following code for the task: {task}

Code:
```
{code}
```

Please provide analysis in the following format:
- Functionality: Brief description of what the code does
- Complexity: Estimated complexity level (1-10)
- Dependencies: List of external dependencies
- Potential Issues: Any potential problems or improvements
- Test Coverage: Estimated test coverage needs
"""
        
        def _make_request():
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a code analysis expert. Provide detailed, structured analysis."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.1
            )
            return response.choices[0].message.content
        
        analysis_text = self._retry_with_backoff(_make_request)
        
        # Parse the response into structured format
        return {
            "analysis": analysis_text,
            "model_used": self.model,
            "timestamp": time.time()
        }
    
    def _construct_prompt(self, prompt: str, context: str) -> str:
        """Construct full prompt with context"""
        if context:
            return f"""
Context (relevant code from the project):
{context}

Task:
{prompt}

Please generate code that integrates well with the existing codebase shown in the context.
"""
        else:
            return prompt


class OllamaProvider(BaseLLMProvider):
    """Ollama local LLM provider"""
    
    def __init__(self, model: str = "llama3.1:8b", base_url: str = "http://localhost:11434",
                 max_tokens: int = 4000, temperature: float = 0.1):
        super().__init__(model, max_tokens, temperature)
        self.base_url = base_url
        
        # Try to import ollama
        try:
            import ollama
            self.ollama = ollama
        except ImportError:
            raise ImportError("ollama package not installed. Install with: pip install ollama")
    
    def generate_code(self, prompt: str, context: str = "", max_tokens: int = None) -> str:
        """Generate code using Ollama"""
        if max_tokens is None:
            max_tokens = self.max_tokens
        
        # Construct the full prompt
        full_prompt = self._construct_prompt(prompt, context)
        
        def _make_request():
            response = self.ollama.generate(
                model=self.model,
                prompt=full_prompt,
                options={
                    'num_predict': max_tokens,
                    'temperature': self.temperature
                }
            )
            return response['response']
        
        return self._retry_with_backoff(_make_request)
    
    def analyze_code(self, code: str, task: str) -> Dict[str, Any]:
        """Analyze code for specific task requirements"""
        prompt = f"""
Analyze the following code for the task: {task}

Code:
```
{code}
```

Please provide analysis covering:
- Functionality
- Complexity
- Dependencies
- Potential Issues
- Test Coverage needs
"""
        
        def _make_request():
            response = self.ollama.generate(
                model=self.model,
                prompt=prompt,
                options={
                    'num_predict': 1000,
                    'temperature': 0.1
                }
            )
            return response['response']
        
        analysis_text = self._retry_with_backoff(_make_request)
        
        return {
            "analysis": analysis_text,
            "model_used": self.model,
            "timestamp": time.time()
        }
    
    def _construct_prompt(self, prompt: str, context: str) -> str:
        """Construct full prompt with context"""
        if context:
            return f"""
You are an expert software developer. Use the following context from the project to inform your response:

Context:
{context}

Task:
{prompt}

Generate clean, well-documented code that integrates with the existing codebase.
"""
        else:
            return f"You are an expert software developer. {prompt}"


class MockLLMProvider(BaseLLMProvider):
    """Mock LLM provider for testing"""
    
    def __init__(self, model: str = "mock-model", **kwargs):
        super().__init__(model)
        self.responses = {}
        self.set_default_responses()
    
    def set_response(self, prompt_key: str, response: str):
        """Set mock response for a prompt"""
        self.responses[prompt_key] = response
    
    def set_default_responses(self):
        """Set default responses for common operations"""
        self.responses.update({
            'test': '''
def test_function():
    """Test the function"""
    assert function() == expected_result
    
def test_function_edge_cases():
    """Test edge cases"""
    assert function(None) is None
    assert function("") == ""
''',
            'docs': '''
# Function Documentation

## Overview
This function performs the specified operation.

## Parameters
- param1: Description of parameter 1
- param2: Description of parameter 2

## Returns
Returns the result of the operation.

## Examples
```python
result = function(param1, param2)
```
''',
            'refactor': '''
def refactored_function(param):
    """Refactored version of the function"""
    # Extracted helper method
    helper_result = _helper_method(param)
    return process_result(helper_result)

def _helper_method(param):
    """Helper method extracted from original function"""
    return param.processed()
'''
        })
    
    def generate_code(self, prompt: str, context: str = "", max_tokens: int = None) -> str:
        """Generate mock code response"""
        # Look for matching response
        for key, response in self.responses.items():
            if key in prompt.lower():
                return response
        
        # Default mock response
        return f"""
# Generated code for: {prompt[:50]}...
def mock_function():
    '''Mock function generated for testing'''
    return "mock_result"
"""
    
    def analyze_code(self, code: str, task: str) -> Dict[str, Any]:
        """Mock code analysis"""
        return {
            "analysis": f"Mock analysis for task: {task}",
            "functionality": "Mock functionality description",
            "complexity": 5,
            "dependencies": ["mock_dependency"],
            "model_used": self.model,
            "timestamp": time.time()
        }


class LLMProviderFactory:
    """Factory for creating LLM providers"""
    
    PROVIDERS = {
        'openai': OpenAIProvider,
        'ollama': OllamaProvider,
        'mock': MockLLMProvider
    }
    
    @classmethod
    def create_provider(cls, provider_name: str, **kwargs) -> LLMProvider:
        """Create LLM provider instance"""
        provider_class = cls.PROVIDERS.get(provider_name.lower())
        if not provider_class:
            raise ValueError(f"Unknown provider: {provider_name}. Available: {list(cls.PROVIDERS.keys())}")
        
        return provider_class(**kwargs)
    
    @classmethod
    def get_available_providers(cls) -> List[str]:
        """Get list of available providers"""
        return list(cls.PROVIDERS.keys())