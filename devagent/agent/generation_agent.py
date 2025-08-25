"""Code generation agent implementation"""

from pathlib import Path
from typing import List, Optional, Dict, Any

from devagent.core.interfaces import Agent, Task, TaskResult
from devagent.context.context_engine import DevAgentContextEngine
from devagent.llm.providers import LLMProviderFactory
from devagent.llm.prompts import GeneralPrompts


class GenerationAgent(Agent):
    """Agent for generating code from a prompt"""

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
        """Execute code generation task"""
        try:
            prompt = task.parameters['prompt']
            output_path = task.parameters.get('output')
            context_file = task.parameters.get('context')

            # Initialize context engine
            project_path = self._find_project_root(output_path or ".")
            self.context_engine = DevAgentContextEngine(project_path)

            # Get context
            context = []
            if context_file:
                context = self.context_engine.get_file_context(context_file)

            # Generate code
            generated_code = self.llm_provider.generate_code(prompt, context=self._format_context(context))

            # Save generated code
            if output_path:
                with open(output_path, 'w') as f:
                    f.write(generated_code)
                generated_files = [output_path]
                output_message = f"Generated code saved to {output_path}"
            else:
                generated_files = []
                output_message = f"Generated code:\n\n{generated_code}"

            return TaskResult(
                success=True,
                generated_files=generated_files,
                modified_files=[],
                output_message=output_message
            )

        except Exception as e:
            return TaskResult(
                success=False,
                generated_files=[],
                modified_files=[],
                output_message=f"Code generation failed: {str(e)}"
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

    def _format_context(self, context: List[Dict[str, Any]]) -> str:
        """Format context for the LLM prompt"""
        if not context:
            return ""

        context_str = "Relevant context from the codebase:\n\n"
        for chunk in context:
            context_str += f"File: {chunk.file_path}\n"
            context_str += f"```\n{chunk.content}\n```\n\n"

        return context_str
