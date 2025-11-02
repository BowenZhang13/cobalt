"""
Tool implementations for the agent with autonomous tool-calling
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from pathlib import Path
import subprocess
import json


@dataclass
class ToolCall:
    """Represents a tool call request from AI"""
    tool_name: str
    parameters: Dict[str, Any]
    reasoning: str = ""  # Why the AI wants to call this tool


@dataclass
class ToolResult:
    """Result from tool execution"""
    success: bool
    output: str
    error: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class Tool(ABC):
    """Base class for all tools"""
    
    def __init__(self, name: str, description: str, parameters: Dict[str, Any], 
                 requires_confirmation: bool = True):
        """
        Initialize tool
        
        Args:
            name: Tool name
            description: Tool description
            parameters: Parameter descriptions with types
            requires_confirmation: Whether this tool requires user confirmation
        """
        self.name = name
        self.description = description
        self.parameters = parameters
        self.requires_confirmation = requires_confirmation
    
    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """Execute the tool"""
        pass
    
    def to_openai_tool(self) -> Dict[str, Any]:
        """Convert tool to OpenAI function calling format"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": self.parameters,
                    "required": [k for k, v in self.parameters.items() 
                                if v.get("required", True)]
                }
            }
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert tool to dictionary for LLM"""
        return {
            'name': self.name,
            'description': self.description,
            'parameters': self.parameters
        }


class ReadFileTool(Tool):
    """Tool to read file contents"""
    
    def __init__(self, workspace):
        super().__init__(
            name="read_file",
            description="Read the contents of a file",
            parameters={
                "filepath": {
                    "type": "string",
                    "description": "Path to the file to read (relative to workspace)"
                }
            },
            requires_confirmation=False
        )
        self.workspace = workspace
    
    def execute(self, filepath: str) -> ToolResult:
        """Read file content"""
        content = self.workspace.read_file(filepath)
        
        if content is not None:
            return ToolResult(
                success=True,
                output=content,
                metadata={'filepath': filepath, 'size': len(content)}
            )
        else:
            return ToolResult(
                success=False,
                output="",
                error=f"Failed to read file: {filepath}"
            )


class CreateFileTool(Tool):
    """Tool to create new files (AI decides the name)"""
    
    def __init__(self, workspace):
        super().__init__(
            name="create_file",
            description="Create a new file with specified content. AI determines the filename.",
            parameters={
                "filepath": {
                    "type": "string",
                    "description": "Path for the new file (relative to workspace, e.g., 'src/calculator.py')"
                },
                "content": {
                    "type": "string",
                    "description": "Complete content to write to the file"
                },
                "reason": {
                    "type": "string",
                    "description": "Brief explanation of why this file is being created"
                }
            },
            requires_confirmation=True
        )
        self.workspace = workspace
    
    def execute(self, filepath: str, content: str, reason: str = "") -> ToolResult:
        """Create new file"""
        success = self.workspace.write_file(filepath, content)
        
        if success:
            return ToolResult(
                success=True,
                output=f"Created {filepath} ({len(content)} bytes)\nReason: {reason}",
                metadata={'filepath': filepath, 'bytes': len(content), 'reason': reason}
            )
        else:
            return ToolResult(
                success=False,
                output="",
                error=f"Failed to create file: {filepath}"
            )


class WriteFileTool(Tool):
    """Tool to write/modify file contents"""
    
    def __init__(self, workspace):
        super().__init__(
            name="write_file",
            description="Write or modify content in an existing file",
            parameters={
                "filepath": {
                    "type": "string",
                    "description": "Path to the file to write (relative to workspace)"
                },
                "content": {
                    "type": "string",
                    "description": "Content to write to the file"
                }
            },
            requires_confirmation=True
        )
        self.workspace = workspace
    
    def execute(self, filepath: str, content: str) -> ToolResult:
        """Write file content"""
        success = self.workspace.write_file(filepath, content)
        
        if success:
            return ToolResult(
                success=True,
                output=f"Successfully wrote {len(content)} bytes to {filepath}",
                metadata={'filepath': filepath, 'bytes': len(content)}
            )
        else:
            return ToolResult(
                success=False,
                output="",
                error=f"Failed to write file: {filepath}"
            )


class ListFilesTool(Tool):
    """Tool to list files in workspace"""
    
    def __init__(self, workspace):
        super().__init__(
            name="list_files",
            description="List files in the workspace matching a pattern",
            parameters={
                "pattern": "Glob pattern to match files (default: *.py)",
                "recursive": "Search recursively (default: true)"
            }
        )
        self.workspace = workspace
    
    def execute(self, pattern: str = "*.py", recursive: bool = True) -> ToolResult:
        """List files"""
        files = self.workspace.list_files(pattern, recursive)
        
        output_lines = []
        for f in files:
            rel_path = f.relative_to(self.workspace.root)
            output_lines.append(str(rel_path))
        
        return ToolResult(
            success=True,
            output="\n".join(output_lines),
            metadata={'count': len(files), 'pattern': pattern}
        )


class SearchCodeTool(Tool):
    """Tool to search code"""
    
    def __init__(self, workspace):
        super().__init__(
            name="search_code",
            description="Search for text patterns in code files",
            parameters={
                "pattern": "Text or regex pattern to search for",
                "file_pattern": "File pattern to search in (default: *.py)",
                "regex": "Use regex matching (default: false)"
            }
        )
        self.workspace = workspace
    
    def execute(self, pattern: str, file_pattern: str = "*.py", 
               regex: bool = False) -> ToolResult:
        """Search for pattern in files"""
        results = self.workspace.search_in_files(pattern, file_pattern, regex=regex)
        
        output_lines = []
        for filepath, line_num, line_content in results:
            rel_path = filepath.relative_to(self.workspace.root)
            output_lines.append(f"{rel_path}:{line_num}: {line_content}")
        
        return ToolResult(
            success=True,
            output="\n".join(output_lines) if output_lines else "No matches found",
            metadata={'matches': len(results), 'pattern': pattern}
        )


class AnalyzeCodeTool(Tool):
    """Tool to analyze code"""
    
    def __init__(self, workspace):
        super().__init__(
            name="analyze_code",
            description="Analyze code structure and statistics",
            parameters={
                "file_pattern": "File pattern to analyze (default: *.py)"
            }
        )
        self.workspace = workspace
    
    def execute(self, file_pattern: str = "*.py") -> ToolResult:
        """Analyze code"""
        stats = self.workspace.count_lines(file_pattern)
        
        output = f"""Code Analysis Results:
        
Total Files: {stats['total_files']}
Total Lines: {stats['total_lines']}
Code Lines: {stats['code_lines']}
Comment Lines: {stats['comment_lines']}
Blank Lines: {stats['blank_lines']}

Code Ratio: {stats['code_lines']/max(stats['total_lines'],1)*100:.1f}%
Comment Ratio: {stats['comment_lines']/max(stats['total_lines'],1)*100:.1f}%
"""
        
        return ToolResult(
            success=True,
            output=output,
            metadata=stats
        )


class RunCommandTool(Tool):
    """Tool to run terminal commands"""
    
    def __init__(self, workspace, safe_mode: bool = False):
        super().__init__(
            name="run_command",
            description="Execute a terminal/shell command. Use for running tests, installing packages, etc.",
            parameters={
                "command": {
                    "type": "string",
                    "description": "Full command to execute (e.g., 'python test.py' or 'pip install requests')"
                },
                "reason": {
                    "type": "string",
                    "description": "Brief explanation of why this command needs to run"
                }
            },
            requires_confirmation=True
        )
        self.workspace = workspace
        self.safe_mode = safe_mode
        # Expanded allowed commands for more functionality
        self.allowed_commands = [
            'python', 'python3', 'pip', 'pip3', 'node', 'npm', 'npx',
            'ls', 'dir', 'cat', 'type', 'echo', 'git', 'pytest', 'test'
        ]
    
    def execute(self, command: str, reason: str = "") -> ToolResult:
        """Run command"""
        # Parse command into parts
        import shlex
        try:
            cmd_parts = shlex.split(command)
        except:
            cmd_parts = command.split()
        
        if not cmd_parts:
            return ToolResult(
                success=False,
                output="",
                error="Empty command"
            )
        
        base_command = cmd_parts[0]
        
        # Check if command is allowed in safe mode
        if self.safe_mode:
            allowed = any(base_command.startswith(cmd) for cmd in self.allowed_commands)
            if not allowed:
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Command '{base_command}' not allowed in safe mode. Allowed: {', '.join(self.allowed_commands)}"
                )
        
        try:
            result = subprocess.run(
                cmd_parts,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(self.workspace.root),
                shell=False
            )
            
            output = result.stdout
            if result.stderr:
                output += f"\n[stderr]: {result.stderr}"
            
            return ToolResult(
                success=result.returncode == 0,
                output=output or "(no output)",
                error=None if result.returncode == 0 else f"Command exited with code {result.returncode}",
                metadata={'returncode': result.returncode, 'command': command, 'reason': reason}
            )
        
        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                output="",
                error="Command timed out after 60 seconds"
            )
        
        except FileNotFoundError:
            return ToolResult(
                success=False,
                output="",
                error=f"Command not found: {base_command}"
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Error running command: {str(e)}"
            )


class GetTreeTool(Tool):
    """Tool to get directory tree"""
    
    def __init__(self, workspace):
        super().__init__(
            name="get_tree",
            description="Get directory tree structure",
            parameters={
                "max_depth": "Maximum depth to traverse (default: 3)"
            }
        )
        self.workspace = workspace
    
    def execute(self, max_depth: int = 3) -> ToolResult:
        """Get directory tree"""
        tree = self.workspace.get_tree(max_depth)
        
        return ToolResult(
            success=True,
            output=tree,
            metadata={'max_depth': max_depth}
        )


class FileInfoTool(Tool):
    """Tool to get file information"""
    
    def __init__(self, workspace):
        super().__init__(
            name="file_info",
            description="Get information about a file",
            parameters={
                "filepath": "Path to the file"
            }
        )
        self.workspace = workspace
    
    def execute(self, filepath: str) -> ToolResult:
        """Get file info"""
        info = self.workspace.get_file_info(filepath)
        
        if info:
            output = f"""File Information:
Path: {info['path']}
Size: {info['size']} bytes
Extension: {info['extension']}
Type: {'File' if info['is_file'] else 'Directory'}
"""
            return ToolResult(
                success=True,
                output=output,
                metadata=info
            )
        else:
            return ToolResult(
                success=False,
                output="",
                error=f"File not found: {filepath}"
            )


def get_all_tools(workspace, safe_mode: bool = False) -> List[Tool]:
    """
    Get all available tools
    
    Args:
        workspace: Workspace instance
        safe_mode: Enable safe mode for command execution
        
    Returns:
        List of tool instances
    """
    return [
        ReadFileTool(workspace),
        CreateFileTool(workspace),
        WriteFileTool(workspace),
        ListFilesTool(workspace),
        SearchCodeTool(workspace),
        AnalyzeCodeTool(workspace),
        RunCommandTool(workspace, safe_mode=safe_mode),
        GetTreeTool(workspace),
        FileInfoTool(workspace)
    ]
