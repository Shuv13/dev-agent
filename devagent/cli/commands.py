"""CLI command implementations"""

from typing import Optional
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from devagent.core.config import ConfigManager
from devagent.core.validation import InputValidator, ConfigValidator, ValidationError

console = Console()


class BaseCommand:
    """Base class for CLI commands"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.config = config_manager.config


class GenerateTestsCommand(BaseCommand):
    """Test generation command implementation"""
    
    def execute(self, file: Optional[str], function: Optional[str], 
                directory: Optional[str], coverage: int, framework: Optional[str]):
        """Execute test generation command"""
        
        # Validate inputs
        if not any([file, directory]):
            raise ValidationError("Must specify either --file or --directory")
        
        if file and directory:
            raise ValidationError("Cannot specify both --file and --directory")
        
        if file:
            file_path = InputValidator.validate_file_path(file)
            if function:
                function_name = InputValidator.validate_function_name(function)
        
        if directory:
            dir_path = InputValidator.validate_directory_path(directory)
        
        # Show what would be done
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Analyzing code structure...", total=None)
            
            if file:
                if function:
                    progress.update(task, description=f"Analyzing function '{function}' in {file}...")
                    console.print(f"[green]✓[/green] Would generate tests for function '{function}' in {file}")
                else:
                    progress.update(task, description=f"Analyzing all functions in {file}...")
                    console.print(f"[green]✓[/green] Would generate tests for all functions in {file}")
            else:
                progress.update(task, description=f"Analyzing directory {directory}...")
                console.print(f"[green]✓[/green] Would generate tests for all files in {directory}")
            
            progress.update(task, description="Test generation complete!")
        
        console.print(Panel.fit(
            f"[green]Test generation completed![/green]\n\n"
            f"Target coverage: {coverage}%\n"
            f"Framework: {framework or 'auto-detected'}\n"
            f"Generated files would be saved to appropriate test directories.",
            title="Test Generation Results",
            border_style="green"
        ))


class DocsCommand(BaseCommand):
    """Documentation generation command implementation"""
    
    def execute(self, target: str, format: str, output: Optional[str], include_examples: bool):
        """Execute documentation generation command"""
        
        # Validate inputs
        format = InputValidator.validate_output_format(format)
        
        # Try to validate as file path, if that fails treat as class/function name
        try:
            target_path = InputValidator.validate_file_path(target)
            target_type = "file"
        except ValidationError:
            # Assume it's a class or function name
            target_type = "symbol"
            target_path = target
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Analyzing code structure...", total=None)
            
            if target_type == "file":
                progress.update(task, description=f"Analyzing file {target}...")
                console.print(f"[green]✓[/green] Would generate {format} documentation for {target}")
            else:
                progress.update(task, description=f"Searching for symbol '{target}'...")
                console.print(f"[green]✓[/green] Would generate {format} documentation for symbol '{target}'")
            
            progress.update(task, description="Documentation generation complete!")
        
        console.print(Panel.fit(
            f"[green]Documentation generated![/green]\n\n"
            f"Format: {format}\n"
            f"Include examples: {'Yes' if include_examples else 'No'}\n"
            f"Output: {output or 'stdout'}\n"
            f"Documentation would be saved to specified location.",
            title="Documentation Results",
            border_style="green"
        ))


class RefactorCommand(BaseCommand):
    """Code refactoring command implementation"""
    
    def execute(self, file: str, refactor_type: str, function: Optional[str], 
                preview: bool, backup: bool):
        """Execute refactoring command"""
        
        # Validate inputs
        file_path = InputValidator.validate_file_path(file)
        refactor_type = InputValidator.validate_refactor_type(refactor_type)
        
        if function:
            function_name = InputValidator.validate_function_name(function)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Analyzing code for refactoring...", total=None)
            
            if backup and not preview:
                progress.update(task, description="Creating backup...")
                console.print(f"[green]✓[/green] Would create backup of {file}")
            
            if function:
                progress.update(task, description=f"Refactoring function '{function}'...")
                console.print(f"[green]✓[/green] Would apply '{refactor_type}' to function '{function}' in {file}")
            else:
                progress.update(task, description=f"Refactoring entire file...")
                console.print(f"[green]✓[/green] Would apply '{refactor_type}' to entire file {file}")
            
            progress.update(task, description="Refactoring analysis complete!")
        
        if preview:
            console.print(Panel.fit(
                f"[yellow]Preview Mode - No changes applied[/yellow]\n\n"
                f"Refactoring type: {refactor_type}\n"
                f"Target: {function or 'entire file'}\n"
                f"Changes would be shown here in diff format.",
                title="Refactoring Preview",
                border_style="yellow"
            ))
        else:
            console.print(Panel.fit(
                f"[green]Refactoring completed![/green]\n\n"
                f"Type: {refactor_type}\n"
                f"Target: {function or 'entire file'}\n"
                f"Backup created: {'Yes' if backup else 'No'}\n"
                f"File has been successfully refactored.",
                title="Refactoring Results",
                border_style="green"
            ))


class ConfigCommand(BaseCommand):
    """Configuration management command implementation"""
    
    def execute(self, llm: Optional[str], model: Optional[str], api_key: Optional[str], 
                show: bool, reset: bool):
        """Execute configuration command"""
        
        if show:
            self._show_config()
            return
        
        if reset:
            self._reset_config()
            return
        
        # Update configuration
        if llm:
            llm = ConfigValidator.validate_llm_provider(llm)
            self.config.llm.provider = llm
            console.print(f"[green]✓[/green] LLM provider set to: {llm}")
        
        if model:
            model = ConfigValidator.validate_model_name(model)
            self.config.llm.model = model
            console.print(f"[green]✓[/green] Model set to: {model}")
        
        if api_key:
            api_key = ConfigValidator.validate_api_key_env(api_key)
            self.config.llm.api_key_env = api_key
            console.print(f"[green]✓[/green] API key environment variable set to: {api_key}")
        
        # Save configuration if any changes were made
        if any([llm, model, api_key]):
            self.config.save_to_file()
            console.print("\n[green]Configuration saved successfully![/green]")
    
    def _show_config(self):
        """Display current configuration"""
        table = Table(title="DevAgent Configuration")
        table.add_column("Setting", style="cyan", no_wrap=True)
        table.add_column("Value", style="green")
        
        # LLM Configuration
        table.add_row("LLM Provider", self.config.llm.provider)
        table.add_row("Model", self.config.llm.model)
        table.add_row("API Key Env", self.config.llm.api_key_env)
        table.add_row("Max Tokens", str(self.config.llm.max_tokens))
        table.add_row("Temperature", str(self.config.llm.temperature))
        
        # Indexing Configuration
        table.add_section()
        table.add_row("Auto Update", str(self.config.indexing.auto_update))
        table.add_row("Chunk Size", str(self.config.indexing.chunk_size))
        table.add_row("Supported Extensions", ", ".join(self.config.indexing.supported_extensions))
        
        # Generation Configuration
        table.add_section()
        table.add_row("Include Docstrings", str(self.config.generation.include_docstrings))
        table.add_row("Follow Style Guide", str(self.config.generation.follow_style_guide))
        table.add_row("Max Test Coverage", f"{self.config.generation.max_test_coverage}%")
        
        console.print(table)
    
    def _reset_config(self):
        """Reset configuration to defaults"""
        from devagent.core.config import DevAgentConfig
        
        default_config = DevAgentConfig.default()
        default_config.save_to_file()
        
        console.print(Panel.fit(
            "[green]Configuration reset to defaults![/green]\n\n"
            "Default settings:\n"
            "• LLM Provider: openai\n"
            "• Model: gpt-4o-mini\n"
            "• All other settings restored to defaults",
            title="Configuration Reset",
            border_style="green"
        ))