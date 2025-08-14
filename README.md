# DevAgent CLI

> AI-Powered Command-Line Developer Assistant

DevAgent CLI is a comprehensive AI-powered tool that helps developers generate tests, create documentation, and refactor code using advanced language models.

## 🚀 Features

- **Test Generation**: Automatically generate comprehensive unit tests for your functions and classes
- **Documentation Creation**: Generate professional documentation in multiple formats (Markdown, RST, Docstrings)
- **Code Refactoring**: Intelligent code refactoring while preserving functionality
- **Multi-Language Support**: Python and JavaScript/TypeScript code analysis
- **Context-Aware**: Uses vector storage for semantic code understanding
- **LLM Integration**: Supports OpenAI GPT models and local Ollama models

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Install Dependencies

```bash
# Clone the repository
git clone https://github.com/Shuv13/dev-agent.git
cd dev-agent

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## ⚙️ Configuration

### Set up your LLM provider

```bash
# For OpenAI (recommended)
export OPENAI_API_KEY="your-api-key-here"

# Configure DevAgent
python -m devagent.cli.main config --llm openai --api-key OPENAI_API_KEY
```

## 🎯 Quick Start

### 1. Initialize DevAgent in your project

```bash
python -m devagent.cli.main init .
```

### 2. Generate tests for your code

```bash
# Generate tests for a specific file
python -m devagent.cli.main test --file src/utils.py

# Generate tests for a specific function
python -m devagent.cli.main test --file src/utils.py --function calculate_metrics

# Generate tests for entire directory
python -m devagent.cli.main test --directory src/
```

### 3. Create documentation

```bash
# Generate markdown documentation
python -m devagent.cli.main docs --target src/api.py

# Generate RST documentation
python -m devagent.cli.main docs --target MyClass --format rst

# Generate docstring documentation
python -m devagent.cli.main docs --target src/models.py --format docstring
```

### 4. Refactor your code

```bash
# Preview refactoring changes
python -m devagent.cli.main refactor --file src/legacy.py --type extract-method --preview

# Apply refactoring
python -m devagent.cli.main refactor --file src/utils.py --type optimize
```

## 📚 Commands Reference

### Core Commands

| Command | Description | Example |
|---------|-------------|---------|
| `init` | Initialize DevAgent in project | `devagent init .` |
| `test` | Generate unit tests | `devagent test --file utils.py` |
| `docs` | Generate documentation | `devagent docs --target api.py` |
| `refactor` | Refactor code | `devagent refactor --file old.py --type optimize` |
| `config` | Manage configuration | `devagent config --show` |

### Test Generation Options

```bash
# Basic usage
python -m devagent.cli.main test --file path/to/file.py

# Advanced options
python -m devagent.cli.main test \
  --file src/calculator.py \
  --function add_numbers \
  --coverage 90 \
  --framework pytest
```

### Documentation Options

```bash
# Different formats
python -m devagent.cli.main docs --target Calculator --format markdown
python -m devagent.cli.main docs --target Calculator --format rst
python -m devagent.cli.main docs --target Calculator --format docstring
```

### Refactoring Options

```bash
# Available refactoring types
python -m devagent.cli.main refactor --file code.py --type extract-method
python -m devagent.cli.main refactor --file code.py --type rename-variable
python -m devagent.cli.main refactor --file code.py --type optimize
```

## 🔧 Configuration

### View current configuration

```bash
python -m devagent.cli.main config --show
```

### Update configuration

```bash
# Change LLM provider
python -m devagent.cli.main config --llm openai --model gpt-4

# Update API key environment variable
python -m devagent.cli.main config --api-key OPENAI_API_KEY

# Reset to defaults
python -m devagent.cli.main config --reset
```

## 🏗️ Architecture

DevAgent CLI is built with a modular architecture:

- **CLI Layer**: Typer-based command-line interface with rich output
- **Agent Layer**: Orchestrates different AI agents for specific tasks
- **Analysis Layer**: Code parsing and analysis for Python/JavaScript
- **Context Layer**: Vector storage and semantic code understanding
- **LLM Layer**: Integration with various language model providers



**Made with ❤️ by [Shuv13](https://github.com/Shuv13)**