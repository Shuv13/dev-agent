"""Code analysis agent implementation"""

from pathlib import Path
from typing import List, Optional, Dict, Any

from devagent.core.interfaces import Agent, Task, TaskResult
from devagent.analysis.analyzer_factory import AnalyzerFactory


class AnalysisAgent(Agent):
    """Agent for analyzing code"""

    def __init__(self, config):
        self.config = config

    def execute_task(self, task: Task) -> TaskResult:
        """Execute code analysis task"""
        try:
            target = task.parameters['target']

            if Path(target).is_file():
                return self._analyze_file(target, task.parameters)
            elif Path(target).is_dir():
                return self._analyze_directory(target, task.parameters)
            else:
                raise ValueError(f"Target '{target}' is not a valid file or directory.")

        except Exception as e:
            return TaskResult(
                success=False,
                generated_files=[],
                modified_files=[],
                output_message=f"Code analysis failed: {str(e)}"
            )

    def _analyze_file(self, file_path: str, parameters: Dict[str, Any]) -> TaskResult:
        """Analyze a single file"""
        analyzer = AnalyzerFactory.create_analyzer(file_path)
        if not analyzer:
            raise ValueError(f"Unsupported file type: {file_path}")

        output = f"Analysis for file: {file_path}\n\n"

        if parameters.get('complexity'):
            complexities = analyzer.calculate_complexity(file_path)
            output += "Cyclomatic Complexity:\n"
            for func, score in complexities.items():
                output += f"  - {func}: {score}\n"
            output += "\n"

        if parameters.get('suggestions'):
            # Placeholder for suggestions
            output += "Improvement Suggestions:\n"
            output += "  - Consider refactoring functions with high complexity.\n"
            output += "  - Add docstrings to public functions.\n"
            output += "\n"

        return TaskResult(
            success=True,
            generated_files=[],
            modified_files=[],
            output_message=output
        )

    def _analyze_directory(self, dir_path: str, parameters: Dict[str, Any]) -> TaskResult:
        """Analyze a directory"""
        output = f"Analysis for directory: {dir_path}\n\n"

        # Placeholder for directory analysis
        output += "Directory analysis is not fully implemented yet.\n"

        return TaskResult(
            success=True,
            generated_files=[],
            modified_files=[],
            output_message=output
        )
