"""Main CLI application entry point"""

import typer
from typing import Optional
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.text import Text

from devagent.core.config import ConfigManager
from devagent.core.validation import InputValidator, ValidationError
from devagent.cli.commands import ConfigCommand

# Initialize console for rich output
console = Console()

# Create the main Typer app
app = typer.Typer(
    name="devagent",
    help="AI-Powered Command-Line Developer Assistant",
    add_completion=False,
    rich_markup_mode="rich"
)

# Initialize config manager
config_manager = ConfigManager()


def version_callback(value: bool):
    """Show version information"""
    if value:
        from devagent import __version__
        console.print(f"DevAgent version: {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None, "--version", "-v", callback=version_callback, is_eager=True,
        help="Show version and exit"
    )
):
    """
    DevAgent - AI-Powered Command-Line Developer Assistant
    
    Automate developer tasks using local codebase context:
    • Generate comprehensive unit tests
    • Create API documentation  
    • Perform intelligent code refactoring
    """
    pass


@app.command()
def init(
    project_path: str = typer.Argument(".", help="Project directory to initialize"),
    force: bool = typer.Option(False, "--force", "-f", help="Force initialization even if already initialized")
):
    """
    Initialize DevAgent in a project directory.
    
    This will:
    • Create configuration directory
    • Index the codebase for context
    • Set up default configuration
    """
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Initializing DevAgent...", total=None)
            
            # Validate project path
            project_dir = InputValidator.validate_project_path(project_path)
            progress.update(task, description="Validating project structure...")
            
            # Check if already initialized
            devagent_dir = project_dir / ".devagent"
            if devagent_dir.exists() and not force:
                console.print("[yellow]DevAgent already initialized in this project.[/yellow]")
                console.print("Use --force to reinitialize.")
                raise typer.Exit(1)
            
            # Create .devagent directory
            progress.update(task, description="Creating configuration directory...")
            devagent_dir.mkdir(exist_ok=True)
            
            # Create default config
            progress.update(task, description="Setting up configuration...")
            config_path = devagent_dir / "config.yaml"
            config = config_manager.config
            config.save_to_file(str(config_path))
            
            # Create index directory
            progress.update(task, description="Preparing index directory...")
            (devagent_dir / "index").mkdir(exist_ok=True)
            
            progress.update(task, description="Initialization complete!")
        
        console.print(Panel.fit(
            "[green]SUCCESS: DevAgent initialized successfully![/green]\n\n"
            "Next steps:\n"
            "• Configure your LLM provider: [cyan]devagent config --llm=openai[/cyan]\n"
            "• Generate tests: [cyan]devagent test --file=src/utils.py[/cyan]\n"
            "• Create docs: [cyan]devagent docs --file=src/api.py[/cyan]",
            title="Initialization Complete",
            border_style="green"
        ))
        
    except ValidationError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def test(
    file: Optional[str] = typer.Option(None, "--file", "-f", help="Target file path"),
    function: Optional[str] = typer.Option(None, "--function", help="Specific function name"),
    directory: Optional[str] = typer.Option(None, "--directory", "-d", help="Target directory"),
    coverage: int = typer.Option(80, "--coverage", help="Target test coverage percentage"),
    framework: Optional[str] = typer.Option(None, "--framework", help="Testing framework to use")
):
    """
    Generate comprehensive unit tests for functions or files.
    
    Examples:
    • devagent test --file=src/utils.py --function=calculate_metrics
    • devagent test --file=src/utils.py
    • devagent test --directory=src/core
    """
    try:
        from devagent.agent.orchestrator import AgentOrchestrator
        from devagent.core.interfaces import Task
        
        orchestrator = AgentOrchestrator(config_manager)
        
        task = Task(
            command="test",
            target_file=file,
            target_function=function,
            parameters={
                'directory': directory,
                'coverage': coverage,
                'framework': framework
            },
            context_requirements=[]
        )
        
        result = orchestrator.execute_task(task)
        
        if result.success:
            console.print(f"[green]SUCCESS:[/green] {result.output_message}")
            if result.generated_files:
                console.print(f"Generated files: {', '.join(result.generated_files)}")
        else:
            console.print(f"[red]ERROR:[/red] {result.output_message}")
            raise typer.Exit(1)
    except ValidationError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def docs(
    target: str = typer.Option(..., "--target", "-t", help="Target file, class, or function"),
    format: str = typer.Option("markdown", "--format", "-f", help="Output format (markdown, rst, docstring)"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file or directory"),
    include_examples: bool = typer.Option(True, "--examples/--no-examples", help="Include usage examples")
):
    """
    Generate comprehensive documentation for code elements.
    
    Examples:
    • devagent docs --target=src/api.py --format=markdown
    • devagent docs --target=UserManager --output=docs/
    • devagent docs --target=src/utils.py --format=rst
    """
    try:
        from devagent.agent.orchestrator import AgentOrchestrator
        from devagent.core.interfaces import Task
        from devagent.context.context_engine import DevAgentContextEngine
        from pathlib import Path

        orchestrator = AgentOrchestrator(config_manager)
        
        target_file = None
        target_function = None

        if Path(target).exists() and Path(target).is_file():
            target_file = target
        else:
            # Assume it's a symbol and search for it
            console.print(f"Searching for symbol '{target}' in the codebase...")
            context_engine = DevAgentContextEngine(project_path=".")
            results = context_engine.search_by_text(target, k=1)
            if results:
                target_file = results[0].file_path
                target_function = target
                console.print(f"Found symbol '{target}' in file: {target_file}")
            else:
                console.print(f"[red]Error: Could not find file or symbol '{target}'[/red]")
                raise typer.Exit(1)

        task = Task(
            command="docs",
            target_file=target_file,
            target_function=target_function,
            parameters={
                'target': target,
                'format': format,
                'output': output,
                'include_examples': include_examples
            },
            context_requirements=[]
        )
        
        result = orchestrator.execute_task(task)
        
        if result.success:
            console.print(f"[green]SUCCESS:[/green] {result.output_message}")
            if result.generated_files:
                console.print(f"Generated files: {', '.join(result.generated_files)}")
        else:
            console.print(f"[red]ERROR:[/red] {result.output_message}")
            raise typer.Exit(1)
    except ValidationError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def refactor(
    file: str = typer.Option(..., "--file", "-f", help="Target file path"),
    type: str = typer.Option(..., "--type", "-t", help="Refactoring type"),
    function: Optional[str] = typer.Option(None, "--function", help="Specific function to refactor"),
    preview: bool = typer.Option(False, "--preview", "-p", help="Preview changes without applying"),
    backup: bool = typer.Option(True, "--backup/--no-backup", help="Create backup before refactoring")
):
    """
    Perform intelligent code refactoring while preserving functionality.
    
    Refactoring types:
    • extract-method: Extract code into separate methods
    • rename-variable: Rename variables consistently
    • optimize: Optimize code performance
    • modernize: Update to modern language features
    
    Examples:
    • devagent refactor --file=legacy.py --type=modernize
    • devagent refactor --file=utils.py --type=extract-method --function=complex_method
    """
    try:
        from devagent.agent.orchestrator import AgentOrchestrator
        from devagent.core.interfaces import Task
        
        orchestrator = AgentOrchestrator(config_manager)
        
        task = Task(
            command="refactor",
            target_file=file,
            target_function=function,
            parameters={
                'type': type,
                'function': function,
                'preview': preview,
                'backup': backup
            },
            context_requirements=[]
        )
        
        result = orchestrator.execute_task(task)
        
        if result.success:
            console.print(f"[green]SUCCESS:[/green] {result.output_message}")
            if result.modified_files:
                console.print(f"Modified files: {', '.join(result.modified_files)}")
        else:
            console.print(f"[red]ERROR:[/red] {result.output_message}")
            raise typer.Exit(1)
    except ValidationError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def config(
    llm: Optional[str] = typer.Option(None, "--llm", help="LLM provider (openai, ollama, anthropic)"),
    model: Optional[str] = typer.Option(None, "--model", help="Model name"),
    api_key: Optional[str] = typer.Option(None, "--api-key", help="API key environment variable"),
    show: bool = typer.Option(False, "--show", help="Show current configuration"),
    reset: bool = typer.Option(False, "--reset", help="Reset to default configuration")
):
    """
    Configure DevAgent settings.
    
    Examples:
    • devagent config --llm=openai --api-key=OPENAI_API_KEY
    • devagent config --llm=ollama --model=llama3.1:8b
    • devagent config --show
    """
    try:
        config_cmd = ConfigCommand(config_manager)
        config_cmd.execute(llm, model, api_key, show, reset)
    except ValidationError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def generate(
    prompt: str = typer.Option(..., "--prompt", "-p", help="Custom generation prompt"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path"),
    context: Optional[str] = typer.Option(None, "--context", "-c", help="Additional context file")
):
    """
    Generate code using custom prompts with codebase context.
    
    Examples:
    • devagent generate --prompt="Create a FastAPI endpoint for user management"
    • devagent generate --prompt="Add error handling to this function" --context=src/utils.py
    """
    try:
        from devagent.agent.orchestrator import AgentOrchestrator
        from devagent.core.interfaces import Task

        orchestrator = AgentOrchestrator(config_manager)

        task = Task(
            command="generate",
            target_file=None,
            target_function=None,
            parameters={
                'prompt': prompt,
                'output': output,
                'context': context
            },
            context_requirements=[]
        )

        result = orchestrator.execute_task(task)

        if result.success:
            console.print(f"[green]SUCCESS:[/green] {result.output_message}")
            if result.generated_files:
                console.print(f"Generated files: {', '.join(result.generated_files)}")
        else:
            console.print(f"[red]ERROR:[/red] {result.output_message}")
            raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def index(
    project_path: str = typer.Argument(".", help="Project directory to index"),
    force: bool = typer.Option(False, "--force", "-f", help="Force re-indexing")
):
    """Index the codebase to build context for the agents."""
    try:
        from devagent.context.context_engine import DevAgentContextEngine

        console.print(f"Indexing codebase at '{project_path}'...")
        context_engine = DevAgentContextEngine(project_path)
        context_engine.index_codebase(force_reindex=force)
        console.print("[green]Codebase indexed successfully![/green]")

    except Exception as e:
        console.print(f"[red]Indexing failed: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def analyze(
    target: str = typer.Argument(".", help="Target file or directory to analyze"),
    complexity: bool = typer.Option(False, "--complexity", help="Show complexity metrics"),
    coverage: bool = typer.Option(False, "--coverage", help="Show test coverage"),
    suggestions: bool = typer.Option(False, "--suggestions", help="Show improvement suggestions")
):
    """
    Analyze code quality and provide insights.
    
    Examples:
    • devagent analyze src/ --complexity --coverage
    • devagent analyze utils.py --suggestions
    """
    try:
        from devagent.agent.orchestrator import AgentOrchestrator
        from devagent.core.interfaces import Task

        orchestrator = AgentOrchestrator(config_manager)

        task = Task(
            command="analyze",
            target_file=None,
            target_function=None,
            parameters={
                'target': target,
                'complexity': complexity,
                'coverage': coverage,
                'suggestions': suggestions
            },
            context_requirements=[]
        )

        result = orchestrator.execute_task(task)

        if result.success:
            console.print(f"[green]ANALYSIS RESULTS:[/green]\n{result.output_message}")
        else:
            console.print(f"[red]ERROR:[/red] {result.output_message}")
            raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()