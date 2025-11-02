"""User interface and display utilities"""

import sys
import os


class Colors:
    """ANSI color codes"""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'


LOGO = """
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║     ██████╗ ██████╗ ██████╗  █████╗ ██╗  ████████╗            ║
    ║    ██╔════╝██╔═══██╗██╔══██╗██╔══██╗██║  ╚══██╔══╝            ║
    ║    ██║     ██║   ██║██████╔╝███████║██║     ██║               ║
    ║    ██║     ██║   ██║██╔══██╗██╔══██║██║     ██║               ║
    ║    ╚██████╗╚██████╔╝██████╔╝██║  ██║███████╗██║               ║
    ║     ╚═════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝               ║
    ║                                                               ║
    ║              AI-Powered Coding Agent (Local)                  ║
    ║                      Version 1.0.0                            ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
"""


class UI:
    """UI utilities for displaying formatted output"""
    
    def __init__(self, use_color: bool = None):
        """
        Initialize UI
        
        Args:
            use_color: Enable ANSI color codes (auto-detect if None)
        """
        if use_color is None:
            # Auto-detect: disable colors in basic Windows cmd/PowerShell
            # Enable if running in VS Code, Windows Terminal, or with ANSICON
            self.use_color = (
                os.environ.get('TERM_PROGRAM') == 'vscode' or  # VS Code
                os.environ.get('WT_SESSION') is not None or    # Windows Terminal
                os.environ.get('ANSICON') is not None or        # ANSICON
                sys.platform != 'win32'                         # Not Windows
            )
        else:
            self.use_color = use_color
    
    def _colorize(self, text: str, color: str) -> str:
        """Apply color to text if enabled"""
        if self.use_color:
            return f"{color}{text}{Colors.RESET}"
        return text
    
    def display_logo(self):
        """Display the Cobalt logo"""
        print(self._colorize(LOGO, Colors.CYAN))
    
    def print_success(self, message: str):
        """Print success message"""
        symbol = "✓"
        print(self._colorize(f"{symbol} {message}", Colors.GREEN))
    
    def print_error(self, message: str):
        """Print error message"""
        symbol = "✗"
        print(self._colorize(f"{symbol} {message}", Colors.RED))
    
    def print_warning(self, message: str):
        """Print warning message"""
        symbol = "⚠"
        print(self._colorize(f"{symbol} {message}", Colors.YELLOW))
    
    def print_info(self, message: str):
        """Print info message"""
        symbol = "ℹ"
        print(self._colorize(f"{symbol} {message}", Colors.BLUE))
    
    def print_bold(self, message: str):
        """Print bold text"""
        print(self._colorize(message, Colors.BOLD))
    
    def print_header(self, title: str):
        """Print section header"""
        print()
        print(self._colorize(f"═══ {title} ═══", Colors.CYAN + Colors.BOLD))
        print()
    
    def print_separator(self):
        """Print separator line"""
        print(self._colorize("═" * 60, Colors.GREEN))
    
    def display_thinking_step(self, step_num: int, title: str, description: str):
        """
        Display a thinking step
        
        Args:
            step_num: Step number
            title: Step title
            description: Step description
        """
        print(self._colorize(f"┌─ [STEP {step_num}] {title}", Colors.YELLOW + Colors.BOLD))
        print(self._colorize("│", Colors.YELLOW))
        
        # Word wrap description
        words = description.split()
        line = "│  "
        for word in words:
            if len(line) + len(word) + 1 > 70:
                print(self._colorize(line, Colors.YELLOW))
                line = "│  " + word + " "
            else:
                line += word + " "
        
        if line.strip() != "│":
            print(self._colorize(line, Colors.YELLOW))
        
        print(self._colorize("└" + "─" * 72, Colors.YELLOW))
        print()
    
    def display_tool_execution(self, tool_name: str, parameters: dict):
        """Display tool execution info"""
        print(self._colorize("╔═══ TOOL EXECUTION ═══", Colors.MAGENTA))
        print(self._colorize(f"║ {tool_name}", Colors.MAGENTA + Colors.BOLD))
        
        if parameters:
            print(self._colorize("╠═══ Parameters:", Colors.MAGENTA))
            for key, value in parameters.items():
                display_val = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
                print(self._colorize(f"║  • {key}: {display_val}", Colors.MAGENTA))
        
        print(self._colorize("╚" + "═" * 22, Colors.MAGENTA))
        print()
    
    def prompt(self, message: str, default: str = None) -> str:
        """
        Prompt user for input
        
        Args:
            message: Prompt message
            default: Default value
            
        Returns:
            User input
        """
        if default:
            prompt_text = f"{message} [{default}]: "
        else:
            prompt_text = f"{message}: "
        
        user_input = input(self._colorize(prompt_text, Colors.CYAN)).strip()
        
        if not user_input and default:
            return default
        
        return user_input
    
    def confirm(self, message: str, default: bool = True) -> bool:
        """
        Prompt user for yes/no confirmation
        
        Args:
            message: Confirmation message
            default: Default choice
            
        Returns:
            True if yes, False if no
        """
        choices = "[Y/n]" if default else "[y/N]"
        response = input(self._colorize(f"{message} {choices}: ", Colors.YELLOW)).strip().lower()
        
        if not response:
            return default
        
        return response in ['y', 'yes']
    
    def display_help(self):
        """Display help message"""
        print()
        print(self._colorize("Available Commands:", Colors.BOLD))
        print()
        
        commands = [
            ("agent <task>", "Execute an AI agent task"),
            ("test", "Test LLM connection"),
            ("models", "List available models"),
            ("list", "List files in workspace"),
            ("search <pattern>", "Search for code"),
            ("tools", "Show available tools"),
            ("status", "Show agent status"),
            ("help", "Show this help"),
            ("exit", "Exit Cobalt")
        ]
        
        for cmd, desc in commands:
            print(f"  {self._colorize(cmd, Colors.CYAN):<30} {desc}")
        
        print()
