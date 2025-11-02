# 🤖 Cobalt - Autonomous AI Coding Agent

An intelligent coding assistant that autonomously creates files, runs commands, and completes multi-step tasks through natural language conversations with LM Studio or Ollama.

## ✨ Features

- **🔥 Autonomous Tool Calling** - AI decides what files to create and commands to run
- **💬 Multi-Turn Conversations** - Agent keeps working until task is complete
- **✅ User Confirmation** - Review and approve each action before execution
- **🔧 File Operations** - Create, read, write, and manage files
- **⚡ Command Execution** - Run terminal commands, compile code, execute scripts
- **🧠 LM Studio Integration** - Works with local LLMs via LiteLLM
- **🎯 Smart Parsing** - Handles multiple response formats from different models
- **🔄 Error Recovery** - Tries different approaches when commands fail

## 🚀 Quick Start

### Installation

```bash
pip install litellm requests
```

### Setup LM Studio

1. Open LM Studio
2. Load a model (e.g., Mistral, CodeLlama, Llama)
3. Start the local server (default: http://localhost:1234)

### Run Cobalt

```bash
python main.py
```

## 📖 Usage

### Basic Commands

```bash
cobalt> agent create a calculator in Python and run it
cobalt> agent make a todo list app with tests
cobalt> agent create a C++ program that prints hello world and compile it
```

### Agent Commands

- `agent <task>` - Execute an autonomous task
- `provider` - Switch between ollama/lmstudio
- `model` - List available models
- `model <name>` - Change to specific model
- `test` - Test LLM connection
- `status` - Show agent status
- `tools` - List available tools
- `exit` - Quit

### Example Session

```
cobalt> agent create and run a file in python that is a basic calculator

[Turn 1/10]
>> AI wants to: create_file
   Parameters:
   - filepath: calculator.py
   - content: def add(a,b): return a+b...
   
>> Execute? [y/n/v]: y
>> Success!

[Turn 2/10]
>> AI wants to: run_command
   Parameters:
   - command: python calculator.py
   
>> Execute? [y/n/v]: y
>> Success!
Add 2+3: 5
Subtract 5-1: 4
```

## 🛠️ Available Tools

### Autonomous Tools (Require Confirmation)
- **create_file** - AI creates files with self-chosen names
- **write_file** - Modify existing files
- **run_command** - Execute terminal commands

### Information Tools (Auto-execute)
- **read_file** - Read file contents
- **list_files** - List files with patterns
- **search_code** - Search for text in files
- **analyze_code** - Code statistics
- **get_tree** - Directory tree view
- **file_info** - File metadata

## 🎯 How It Works

1. **You give a task** - "create a web scraper and run it"
2. **AI plans actions** - Decides to create file, then run command
3. **You approve each step** - Review before execution
4. **Agent continues** - Keeps going until task complete
5. **Multi-turn conversation** - AI adapts based on results

## 🔧 Configuration

### Command Line Options

```bash
# Use LM Studio (default)
python main.py --provider lmstudio

# Use Ollama
python main.py --provider ollama

# Custom model
python main.py --model mistral

# Custom workspace
python main.py --workspace /path/to/project

# Enable safe mode (restrict commands)
python main.py --safe-mode
```

### In-Session Configuration

```
cobalt> provider          # Toggle between ollama/lmstudio
cobalt> model llama       # Change model
cobalt> model             # List available models
```

## 📁 Project Structure

```
cobalt/
├── cobalt/
│   ├── agent.py          # Multi-turn agent orchestration
│   ├── tools.py          # Tool implementations
│   ├── llm.py            # LiteLLM client
│   ├── cli.py            # Command-line interface
│   ├── config.py         # Configuration management
│   ├── workspace.py      # File operations
│   └── ui.py             # User interface utilities
├── main.py               # Entry point
├── requirements.txt      # Dependencies
└── README.md            # This file
```

## 🎨 Features in Detail

### Multi-Turn Conversations

The agent doesn't just execute one action - it keeps going until the task is complete:

```
Task: Create a calculator with tests and run them

Turn 1: Creates calculator.py
Turn 2: Creates test_calculator.py
Turn 3: Runs pytest
Turn 4: Shows results and says "Task completed"
```

### Smart Error Handling

When something fails, the agent tries alternatives:

```
Turn 1: Tries g++ main.cpp -o main
        ❌ Failed: g++ not found
        
Turn 2: Tries cl.exe main.cpp
        ❌ Failed: cl.exe not found
        
Turn 3: Suggests installing MinGW
        ✅ Success!
```

### Cross-Platform Support

Works on Windows, Linux, and macOS:
- Automatically detects OS
- Uses appropriate commands (python vs python3, .exe vs no extension)
- Handles path differences

## 🔒 Security

- **User confirmation** required for all file creation and command execution
- **Safe mode** available to restrict command execution
- **Private workspace** - operates only in specified directory
- **View before execute** - [v] option to see full file content

## 🤝 Contributing

This is a private repository. If you have access and want to contribute:

1. Create a feature branch
2. Make your changes
3. Test thoroughly
4. Submit a pull request

## 📝 Requirements

- Python 3.8+
- LM Studio or Ollama
- litellm
- requests

## 🐛 Troubleshooting

### AI doesn't generate tool calls

- Try a different model (Mistral, CodeLlama work well)
- Increase `--max-tokens 8192`
- Be more explicit: "create a file called app.py with..."

### Commands fail on Windows

- Use Windows-style commands: `dir` instead of `ls`
- Or let the AI figure it out - it usually adapts

### Model responds slowly

- This is normal - local LLMs take 2-5+ seconds
- Use smaller models for faster responses
- Enable GPU acceleration in LM Studio

## 📊 Performance

- **Startup**: < 100ms
- **LLM Response**: 2-5 seconds (model dependent)
- **File Operations**: < 50ms
- **Command Execution**: Varies by command

## 🎯 Use Cases

- **Quick Scripts**: "create a script that renames all .txt files"
- **Learning**: "create a simple neural network and train it"
- **Prototyping**: "make a REST API with authentication"
- **Code Generation**: "generate test cases for this function"
- **Automation**: "create a backup script that runs daily"

## 📜 License

MIT License - See LICENSE file

## 🙏 Acknowledgments

- LiteLLM for unified LLM API
- LM Studio for local model serving
- Ollama for easy model management

---

**Built with ❤️ for autonomous coding assistance**
