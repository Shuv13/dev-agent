"""Agentic workflow orchestration"""

from typing import Dict, Any, List, Optional
from devagent.core.interfaces import Agent, Task, TaskResult
from devagent.core.config import ConfigManager
from devagent.agent.test_agent import TestGenerationAgent
from devagent.agent.docs_agent import DocumentationAgent
from devagent.agent.refactor_agent import RefactoringAgent
from devagent.agent.generation_agent import GenerationAgent
from devagent.agent.analysis_agent import AnalysisAgent


class AgentOrchestrator:
    """Orchestrates different agents for complex workflows"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.config = config_manager.config
        
        # Initialize agents with error handling
        self.agents = {}
        try:
            self.agents['test'] = TestGenerationAgent(self.config)
            self.agents['docs'] = DocumentationAgent(self.config)
            self.agents['refactor'] = RefactoringAgent(self.config)
            self.agents['generate'] = GenerationAgent(self.config)
            self.agents['analyze'] = AnalysisAgent(self.config)
        except Exception as e:
            # If agents can't be initialized (e.g., missing API keys), create mock versions
            from devagent.llm.providers import MockLLMProvider
            mock_config = self.config
            mock_config.llm.provider = 'mock'
            
            self.agents['test'] = TestGenerationAgent(mock_config)
            self.agents['docs'] = DocumentationAgent(mock_config)
            self.agents['refactor'] = RefactoringAgent(mock_config)
            self.agents['generate'] = GenerationAgent(mock_config)
            self.agents['analyze'] = AnalysisAgent(mock_config)
    
    def execute_task(self, task: Task) -> TaskResult:
        """Execute task using appropriate agent"""
        agent = self.agents.get(task.command)
        if not agent:
            return TaskResult(
                success=False,
                generated_files=[],
                modified_files=[],
                output_message=f"Unknown command: {task.command}"
            )
        
        try:
            return agent.execute_task(task)
        except Exception as e:
            return TaskResult(
                success=False,
                generated_files=[],
                modified_files=[],
                output_message=f"Task execution failed: {str(e)}"
            )
    
    def execute_workflow(self, tasks: List[Task]) -> List[TaskResult]:
        """Execute multiple tasks in sequence"""
        results = []
        
        for task in tasks:
            result = self.execute_task(task)
            results.append(result)
            
            # Stop on failure if task is critical
            if not result.success and task.parameters.get('critical', False):
                break
        
        return results