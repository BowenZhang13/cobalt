"""
Command-line interface for Cobalt
"""

import sys
from pathlib import Path

from cobalt.agent import CobaltAgent
from cobalt.config import Config
from cobalt.ui import UI


class CobaltCLI:
    """Main CLI application"""
    
    def __init__(self, config: Config):
        """
        Initialize CLI
        
        Args:
            config: Agent configuration
        """
        self.config = config
        self.agent = CobaltAgent(config)
        self.ui = UI()
        self.running = True
    
    def start(self):
        """Start the CLI loop"""
        self.agent.display_logo()
        self.agent.display_welcome()
        
        print("Type 'help' for commands or 'test' to verify LLM connection.")
        print()
        
        while self.running:
            try:
                user_input = input(self.ui._colorize("cobalt> ", UI().use_color and "\033[1m\033[34m" or "")).strip()
                
                if not user_input:
                    continue
                
                self.handle_command(user_input)
                
            except KeyboardInterrupt:
                print()
                self.ui.print_warning("Use 'exit' to quit")
                continue
            
            except EOFError:
                print()
                break
    
    def handle_command(self, user_input: str):
        """
        Handle user command
        
        Args:
            user_input: User input string
        """
        parts = user_input.split(maxsplit=1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        if command in ['exit', 'quit', 'q']:
            self.ui.print_info("Goodbye! Happy coding! 👋")
            self.running = False
        
        elif command == 'help':
            self.ui.display_help()
        
        elif command == 'test':
            self.agent.test_connection()
        
        elif command == 'model':
            if args:
                # Change model
                self.config.model = args
                # Recreate agent with new model
                self.agent = CobaltAgent(self.config)
                self.ui.print_success(f"Model changed to: {args}")
            else:
                # List models
                self.agent.list_models()
        
        elif command == 'tools':
            self.agent.display_tools()
        
        elif command == 'status':
            self.agent.display_status()
        
        elif command == 'list':
            self.handle_list(args)
        
        elif command == 'search':
            self.handle_search(args)
        
        elif command == 'tree':
            self.handle_tree()
        
        elif command == 'analyze':
            self.handle_analyze(args)
        
        elif command == 'provider':
            # Toggle provider
            old = self.config.provider
            self.config.provider = 'lmstudio' if old == 'ollama' else 'ollama'
            self.config.endpoint = "http://localhost:1234" if self.config.provider == 'lmstudio' else "http://localhost:11434"
            self.config.model = "local-model" if self.config.provider == 'lmstudio' else "codellama"
            # Recreate agent
            self.agent = CobaltAgent(self.config)
            self.ui.print_success(f"Provider switched: {old} -> {self.config.provider}")
            self.ui.print_info(f"Endpoint: {self.config.endpoint}")
            self.ui.print_info(f"Model: {self.config.model}")
        
        elif command == 'agent':
            if args:
                self.agent.execute_task(args)
            else:
                self.ui.print_error("Usage: agent <task description>")
        
        else:
            self.ui.print_error(f"Unknown command: {command}")
            print("Type 'help' for available commands.")
    
    def handle_list(self, args: str):
        """Handle list command"""
        pattern = args.strip() if args else "*.py"
        
        files = self.agent.workspace.list_files(pattern)
        
        self.ui.print_header(f"Files matching '{pattern}'")
        
        if files:
            for f in files[:50]:  # Limit to 50 files
                rel_path = f.relative_to(self.agent.workspace.root)
                print(f"  {rel_path}")
            
            if len(files) > 50:
                print(f"\n  ... and {len(files) - 50} more files")
            
            print(f"\nTotal: {len(files)} files")
        else:
            self.ui.print_warning("No files found")
    
    def handle_search(self, pattern: str):
        """Handle search command"""
        if not pattern:
            self.ui.print_error("Usage: search <pattern>")
            return
        
        self.ui.print_header(f"Searching for '{pattern}'")
        
        results = self.agent.workspace.search_in_files(pattern)
        
        if results:
            for filepath, line_num, line in results[:30]:
                rel_path = filepath.relative_to(self.agent.workspace.root)
                print(f"{rel_path}:{line_num}: {line}")
            
            if len(results) > 30:
                print(f"\n... and {len(results) - 30} more results")
            
            print(f"\nTotal: {len(results)} matches")
        else:
            self.ui.print_warning("No matches found")
    
    def handle_tree(self):
        """Handle tree command"""
        self.ui.print_header("Directory Tree")
        tree = self.agent.workspace.get_tree()
        print(tree)
    
    def handle_analyze(self, pattern: str):
        """Handle analyze command"""
        pattern = pattern.strip() if pattern else "*.py"
        
        self.ui.print_header(f"Code Analysis ({pattern})")
        
        stats = self.agent.workspace.count_lines(pattern)
        
        print(f"  Total Files:    {stats['total_files']}")
        print(f"  Total Lines:    {stats['total_lines']}")
        print(f"  Code Lines:     {stats['code_lines']}")
        print(f"  Comment Lines:  {stats['comment_lines']}")
        print(f"  Blank Lines:    {stats['blank_lines']}")
        print()
        
        if stats['total_lines'] > 0:
            code_ratio = stats['code_lines'] / stats['total_lines'] * 100
            comment_ratio = stats['comment_lines'] / stats['total_lines'] * 100
            print(f"  Code Ratio:     {code_ratio:.1f}%")
            print(f"  Comment Ratio:  {comment_ratio:.1f}%")
        
        print()


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Cobalt - AI-Powered Coding Agent',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--workspace', '-w',
        type=str,
        default='.',
        help='Workspace directory (default: current directory)'
    )
    
    parser.add_argument(
        '--provider', '-p',
        choices=['ollama', 'lmstudio'],
        default='lmstudio',
        help='LLM provider (default: lmstudio)'
    )
    
    parser.add_argument(
        '--endpoint', '-e',
        type=str,
        help='LLM endpoint URL'
    )
    
    parser.add_argument(
        '--model', '-m',
        type=str,
        help='Model name'
    )
    
    parser.add_argument(
        '--temperature', '-t',
        type=float,
        default=0.7,
        help='Temperature for generation (default: 0.7)'
    )
    
    parser.add_argument(
        '--max-tokens',
        type=int,
        default=4096,
        help='Maximum tokens to generate (default: 4096)'
    )
    
    parser.add_argument(
        '--timeout',
        type=int,
        default=120,
        help='Request timeout in seconds (default: 120)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--no-thinking',
        action='store_true',
        help='Disable thinking step display'
    )
    
    parser.add_argument(
        '--safe-mode',
        action='store_true',
        help='Enable safe mode (restrict command execution)'
    )
    
    args = parser.parse_args()
    
    # Create config
    config = Config(
        workspace=Path(args.workspace),
        provider=args.provider,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        timeout=args.timeout,
        verbose=args.verbose,
        show_thinking=not args.no_thinking,
        safe_mode=args.safe_mode
    )
    
    # Set endpoint and model based on provider if not specified
    if args.endpoint:
        config.endpoint = args.endpoint
    else:
        config.endpoint = "http://localhost:11434" if args.provider == 'ollama' else "http://localhost:1234"
    
    if args.model:
        config.model = args.model
    else:
        config.model = "codellama" if args.provider == 'ollama' else "local-model"
    
    try:
        config.validate()
    except ValueError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Start CLI
    cli = CobaltCLI(config)
    cli.start()


if __name__ == '__main__':
    main()
