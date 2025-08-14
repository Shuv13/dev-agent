# DevAgent CLI

> AI-Powered Command-Line Developer Assistant

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Development Status](https://img.shields.io/badge/status-alpha-orange.svg)](https://github.com/Shuv13/dev-agent)

> **⚠️ Alpha Version Notice**: This is an early alpha version. Core CLI functionality works, but AI features currently return mock responses. Real LLM integration is planned for v2.0.

DevAgent CLI is a comprehensive AI-powered tool that helps developers generate tests, create documentation, and refactor code using advanced language models.

## 🚀 Features

### ✅ **Currently Working**
- **Project Initialization**: Set up DevAgent in any project directory
- **Configuration Management**: Configure LLM providers, API keys, and settings
- **Code Analysis**: Python AST parsing and function/class detection
- **File Operations**: Read, write, and manage project files
- **CLI Interface**: Complete command-line interface with help system
- **Error Handling**: Comprehensive input validation and error messages
- **Multi-Language Support**: Python and JavaScript/TypeScript code analysis (parsing only)

### 🚧 **Partially Working** (Mock Responses)
- **Test Generation**: CLI works, but generates mock tests (needs real LLM integration)
- **Documentation Creation**: CLI works, but generates mock documentation (needs real LLM integration)
- **Code Refactoring**: CLI works, but shows mock refactoring (needs real LLM integration)

### ❌ **Not Yet Implemented**
- **Custom Code Generation**: Placeholder command (shows "coming soon" message)
- **Code Analysis with Insights**: Placeholder command (shows "coming soon" message)
- **Real LLM Integration**: Currently uses mock responses instead of actual AI
- **Vector Storage**: Context engine exists but not fully integrated with LLM workflow

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

> **⚠️ Important**: Currently, the system uses mock responses for AI features. Real LLM integration is planned for future releases.

```bash
# For OpenAI (when implemented)
export OPENAI_API_KEY="your-api-key-here"

# Configure DevAgent
python -m devagent.cli.main config --llm openai --api-key OPENAI_API_KEY

# View current configuration
python -m devagent.cli.main config --show
```

## 🎯 Quick Start

### 1. Initialize DevAgent in your project

```bash
python -m devagent.cli.main init .
```

> **✅ This works perfectly!** Creates project configuration and sets up the workspace.

### 2. Generate tests for your code ⚠️ (Mock responses)

```bash
# Generate tests for a specific file
python -m devagent.cli.main test --file src/utils.py

# Generate tests for a specific function
python -m devagent.cli.main test --file src/utils.py --function calculate_metrics

# Generate tests for entire directory
python -m devagent.cli.main test --directory src/
```

> **Note**: Currently generates mock test templates. Real AI-generated tests coming soon.

### 3. Create documentation ⚠️ (Mock responses)

```bash
# Generate markdown documentation
python -m devagent.cli.main docs --target src/api.py

# Generate RST documentation
python -m devagent.cli.main docs --target MyClass --format rst

# Generate docstring documentation
python -m devagent.cli.main docs --target src/models.py --format docstring
```

> **Note**: Currently generates mock documentation. Real AI-generated docs coming soon.

### 4. Refactor your code ⚠️ (Mock responses)

```bash
# Preview refactoring changes
python -m devagent.cli.main refactor --file src/legacy.py --type extract-method --preview

# Apply refactoring
python -m devagent.cli.main refactor --file src/utils.py --type optimize
```

> **Note**: Currently shows mock refactoring suggestions. Real AI-powered refactoring coming soon.

## 📚 Commands Reference

### Core Commands

| Command | Status | Description | Example |
|---------|--------|-------------|---------|
| `init` | ✅ **Working** | Initialize DevAgent in project | `devagent init .` |
| `test` | ⚠️ **Mock** | Generate unit tests (mock responses) | `devagent test --file utils.py` |
| `docs` | ⚠️ **Mock** | Generate documentation (mock responses) | `devagent docs --target api.py` |
| `refactor` | ⚠️ **Mock** | Refactor code (mock responses) | `devagent refactor --file old.py --type optimize` |
| `config` | ✅ **Working** | Manage configuration | `devagent config --show` |
| `generate` | ❌ **Placeholder** | Custom code generation | `devagent generate --prompt "..."` |
| `analyze` | ❌ **Placeholder** | Code analysis with insights | `devagent analyze file.py` |

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

- **CLI Layer**: ✅ Typer-based command-line interface with rich output
- **Agent Layer**: ✅ Orchestrates different AI agents for specific tasks
- **Analysis Layer**: ✅ Code parsing and analysis for Python/JavaScript
- **Context Layer**: 🚧 Vector storage and semantic code understanding (partially implemented)
- **LLM Layer**: ❌ Integration with various language model providers (mock responses only)

## 🚧 Current Development Status

### What's Fully Implemented
- Complete CLI framework with all commands
- Project initialization and configuration management
- Code analysis and parsing (Python AST, JavaScript Tree-sitter)
- File operations and project structure management
- Error handling and input validation
- Help system and command documentation

### What's Partially Implemented
- Agent orchestration system (framework ready, needs LLM integration)
- Vector storage system (ChromaDB integration exists, needs workflow integration)
- Context engine (indexing works, retrieval needs LLM integration)

### What's Planned
- Real OpenAI GPT integration for test generation
- Real OpenAI GPT integration for documentation generation
- Real OpenAI GPT integration for code refactoring
- Custom code generation with context awareness
- Advanced code analysis with AI insights
- Support for additional LLM providers (Anthropic Claude, local models)

## 🔮 Roadmap

### Version 1.0 (Current)
- ✅ CLI framework and command structure
- ✅ Project initialization and configuration
- ✅ Code analysis and parsing
- ⚠️ Mock responses for AI features

### Version 2.0 (Planned)
- 🎯 Real OpenAI GPT integration
- 🎯 Actual test generation with AI
- 🎯 Real documentation generation
- 🎯 AI-powered code refactoring

### Version 3.0 (Future)
- 🚀 Custom code generation
- 🚀 Advanced code analysis with insights
- 🚀 Multiple LLM provider support
- 🚀 Plugin system for extensibility

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. **Report Issues**: Found a bug? Report it on GitHub Issues
2. **Suggest Features**: Have an idea? Create a feature request
3. **Contribute Code**: 
   - Fork the repository
   - Create a feature branch (`git checkout -b feature/amazing-feature`)
   - Commit your changes (`git commit -m 'Add amazing feature'`)
   - Push to the branch (`git push origin feature/amazing-feature`)
   - Open a Pull Request

### Priority Areas for Contribution
- 🔥 **High Priority**: Real LLM integration (OpenAI, Anthropic)
- 🔥 **High Priority**: Vector storage workflow integration
- 🔥 **High Priority**: Test generation with actual AI
- 🔥 **Medium Priority**: Additional language support
- 🔥 **Medium Priority**: Plugin system architecture

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/Shuv13/dev-agent/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Shuv13/dev-agent/discussions)
- **Feature Requests**: Use GitHub Issues with the "enhancement" label

## 🙏 Acknowledgments

- Built with [Typer](https://typer.tiangolo.com/) for CLI interface
- Uses [ChromaDB](https://www.trychroma.com/) for vector storage
- Powered by [OpenAI](https://openai.com/) for AI capabilities (planned)
- Code analysis with [Tree-sitter](https://tree-sitter.github.io/tree-sitter/)

---

**Made with ❤️ by [Shuv13](https://github.com/Shuv13)**