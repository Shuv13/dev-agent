"""Configuration management system"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class LLMConfig:
    """LLM provider configuration"""
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    api_key_env: str = "OPENAI_API_KEY"
    max_tokens: int = 4000
    temperature: float = 0.1


@dataclass
class IndexingConfig:
    """Indexing configuration"""
    auto_update: bool = True
    exclude_patterns: list = None
    chunk_size: int = 1000
    overlap: int = 100
    supported_extensions: list = None
    
    def __post_init__(self):
        if self.exclude_patterns is None:
            self.exclude_patterns = ["*.pyc", "__pycache__", ".git", "node_modules"]
        if self.supported_extensions is None:
            self.supported_extensions = [".py", ".js", ".ts", ".java", ".go"]


@dataclass
class GenerationConfig:
    """Code generation configuration"""
    include_docstrings: bool = True
    follow_style_guide: bool = True
    max_test_coverage: int = 90
    include_edge_cases: bool = True


@dataclass
class PerformanceConfig:
    """Performance configuration"""
    max_memory_mb: int = 2048
    index_batch_size: int = 100
    retrieval_top_k: int = 5


@dataclass
class DevAgentConfig:
    """Main configuration class"""
    llm: LLMConfig
    indexing: IndexingConfig
    generation: GenerationConfig
    performance: PerformanceConfig
    
    @classmethod
    def load_from_file(cls, config_path: Optional[str] = None) -> 'DevAgentConfig':
        """Load configuration from file"""
        if config_path is None:
            config_path = os.path.expanduser("~/.devagent/config.yaml")
        
        config_file = Path(config_path)
        if not config_file.exists():
            return cls.default()
        
        with open(config_file, 'r') as f:
            data = yaml.safe_load(f)
        
        return cls(
            llm=LLMConfig(**data.get('llm', {})),
            indexing=IndexingConfig(**data.get('indexing', {})),
            generation=GenerationConfig(**data.get('generation', {})),
            performance=PerformanceConfig(**data.get('performance', {}))
        )
    
    @classmethod
    def default(cls) -> 'DevAgentConfig':
        """Create default configuration"""
        return cls(
            llm=LLMConfig(),
            indexing=IndexingConfig(),
            generation=GenerationConfig(),
            performance=PerformanceConfig()
        )
    
    def save_to_file(self, config_path: Optional[str] = None) -> None:
        """Save configuration to file"""
        if config_path is None:
            config_path = os.path.expanduser("~/.devagent/config.yaml")
        
        config_file = Path(config_path)
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_file, 'w') as f:
            yaml.dump(asdict(self), f, default_flow_style=False)


class ConfigManager:
    """Configuration manager"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path
        self._config = None
    
    @property
    def config(self) -> DevAgentConfig:
        """Get current configuration"""
        if self._config is None:
            self._config = DevAgentConfig.load_from_file(self.config_path)
        return self._config
    
    def reload(self) -> None:
        """Reload configuration from file"""
        self._config = None
    
    def update_llm_config(self, provider: str, model: str = None, api_key_env: str = None) -> None:
        """Update LLM configuration"""
        config = self.config
        config.llm.provider = provider
        if model:
            config.llm.model = model
        if api_key_env:
            config.llm.api_key_env = api_key_env
        config.save_to_file(self.config_path)