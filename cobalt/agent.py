"""
Main agent orchestration with multi-turn autonomous tool calling
"""

import time
import json
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from cobalt.config import Config
from cobalt.llm import create_llm_client, Message, LLMResponse
from cobalt.workspace import Workspace
from cobalt.tools import get_all_tools, ToolResult, ToolCall, Tool
from cobalt.ui import UI


@dataclass
class ExecutionStep:
    """Represents a step in agent execution"""
    name: str
    description: str
    status: str
    duration_ms: float = 0
    output: str = ""
    error: Optional[str] = None


class CobaltAgent:
    """Main agent that orchestrates LLM and tools with multi-turn conversation"""
    
    def __init__(self, config: Config):
        self.config = config
        self.workspace = Workspace(config.workspace, config.ignore_patterns)
        self.llm = create_llm_client(config.endpoint, config.model, config.timeout)
        safe_mode = getattr(config, 'safe_mode', False)
        self.tools = get_all_tools(self.workspace, safe_mode=safe_mode)
        self.ui = UI()
        self.execution_history: List[ExecutionStep] = []
    
    def display_logo(self):
        self.ui.display_logo()
    
    def display_welcome(self):
        self.ui.print_info(f"Workspace:  {self.config.workspace}")
        self.ui.print_info(f"Provider:   {self.config.provider}")
        self.ui.print_info(f"Endpoint:   {self.config.endpoint}")
        self.ui.print_info(f"Model:      {self.config.model}")
        self.ui.print_info(f"Autonomous Mode: Enabled (Multi-turn conversation)")
        print()
    
    def test_connection(self) -> bool:
        self.ui.print_header("Testing LLM Connection")
        test_messages = [
            Message(role="system", content="You are a helpful assistant."),
            Message(role="user", content="Say 'Hello, I am working!' and nothing else.")
        ]
        response = self.llm.generate(test_messages, temperature=0.5, max_tokens=50)
        
        if response.success:
            self.ui.print_success(f"LLM is working!")
            self.ui.print_info(f"Response: {response.content}")
            self.ui.print_info(f"Latency: {response.latency_ms:.0f}ms")
            self.ui.print_info(f"Tokens: {response.total_tokens}")
            return True
        else:
            self.ui.print_error("LLM connection failed")
            self.ui.print_error(response.error or "Unknown error")
            return False
    
    def list_models(self):
        self.ui.print_header("Available Models")
        models = self.llm.list_models()
        if models:
            for i, model in enumerate(models, 1):
                marker = "✓" if model == self.config.model else " "
                print(f"  {marker} {i}. {model}")
        else:
            self.ui.print_warning("No models found or connection failed")
    
    def execute_task(self, task: str, max_turns: int = 10):
        """Execute task with multi-turn conversation"""
        self.ui.print_separator()
        self.ui.print_bold("AGENT EXECUTION STARTED")
        self.ui.print_separator()
        print()
        self.ui.print_bold(f"Task: {task}")
        print()
        
        # Initialize conversation
        messages = [
            Message(role="system", content=self._get_system_prompt()),
            Message(role="user", content=f"Task: {task}\\nWorkspace: {self.config.workspace}")
        ]
        
        # Multi-turn loop
        for turn in range(1, max_turns + 1):
            print(f"\n[Turn {turn}/{max_turns}]")
            
            # Get AI response
            self.ui.print_info(f"Requesting AI action...")
            response = self.llm.generate(messages, temperature=self.config.temperature, max_tokens=self.config.max_tokens)
            
            if not response.success:
                self.ui.print_error("LLM failed")
                break
            
            self.ui.print_success(f"Response ({response.latency_ms:.0f}ms)")
            ai_response = response.content
            messages.append(Message(role="assistant", content=ai_response))
            
            # Show response (only if meaningful)
            # Skip showing raw AI response - it contains special tokens
            
            # Extract tool calls
            tool_calls = self._extract_tool_calls(ai_response)
            
            if not tool_calls:
                # Debug: show what AI said and attempt manual parse
                print(f"\nDEBUG - AI Response:\n{ai_response}\n")
                
                # Try to manually fix incomplete JSON
                if '<|constrain|>json<|message|>' in ai_response or '<|message|>' in ai_response:
                    # Extract everything after the tag
                    for tag in ['<|constrain|>json<|message|>', '<|message|>']:
                        if tag in ai_response:
                            json_part = ai_response.split(tag)[-1].strip()
                            # Try to find where JSON might end (before next tag or end of string)
                            json_part = json_part.split('<|')[0]
                            # If missing closing brace, add it
                            if json_part.count('{') > json_part.count('}'):
                                json_part += '}' * (json_part.count('{') - json_part.count('}'))
                            try:
                                data = json.loads(json_part)
                                if isinstance(data, dict) and 'tool' in data:
                                    print(f"\nRecovered tool call: {data['tool']}\n")
                                    tool_calls = [ToolCall(
                                        tool_name=data['tool'],
                                        parameters=data.get('parameters', {}),
                                        reasoning=data.get('reason', '')
                                    )]
                                    break
                            except:
                                pass
                
                                    # Check if done
                    done_words = ['done', 'completed', 'finished', 'success', 'task completed']
                    if any(word in ai_response.lower() for word in done_words):
                        self.ui.print_success("Task completed!")
                        break
                    else:
                        self.ui.print_warning("No tool calls detected. Model may not understand the format.")
                        break
            
            # Execute tools
            results = []
            for i, tc in enumerate(tool_calls, 1):
                result = self._exec_tool(tc, i, len(tool_calls))
                if result:
                    results.append(f"{tc.tool_name}: {result}")
            
            # Send results back
            if results:
                results_msg = "Results:\\n" + "\\n".join(results) + "\\n\\nContinue or say 'Task completed'."
                messages.append(Message(role="user", content=results_msg))
            else:
                break
        
        print()
        self.ui.print_separator()
        self.ui.print_bold("AGENT EXECUTION COMPLETED")
        self.ui.print_separator()
        print()
    
    def _get_system_prompt(self) -> str:
        return f"""You MUST respond with tool calls. Do NOT write explanatory text.

AVAILABLE TOOLS:
- create_file(filepath, content, reason): Create new file
- write_file(filepath, content): Modify existing file  
- read_file(filepath): Read file content
- run_command(command, reason): Execute terminal command
- list_files(pattern): List files

FORMAT (use EXACTLY this):
```json
{{"tool": "create_file", "parameters": {{"filepath": "test.cpp", "content": "#include <iostream>\\nint main() {{ std::cout << \\"hello\\"; }}", "reason": "Create C++ file"}}}}
```

EXAMPLES:

1. Create C++ file:
```json
{{"tool": "create_file", "parameters": {{"filepath": "main.cpp", "content": "#include <iostream>\\nint main() {{ std::cout << \\"test\\"; return 0; }}", "reason": "Create C++ program"}}}}
```

2. Compile and run:
```json
{{"tool": "run_command", "parameters": {{"command": "g++ main.cpp -o main && ./main", "reason": "Compile and execute"}}}}
```

3. For Python:
```json
{{"tool": "create_file", "parameters": {{"filepath": "test.py", "content": "print('hello')", "reason": "Create Python file"}}}}
```
```json
{{"tool": "run_command", "parameters": {{"command": "python test.py", "reason": "Run Python"}}}}
```

IMPORTANT:
- ONLY output ```json blocks
- NO explanations or text outside JSON
- After tools execute, you get results and continue
- Say "Task completed" when done

Workspace: {self.config.workspace}

Respond with ```json block now."""
    
    def _format_tools_for_prompt(self) -> str:
        lines = []
        for tool in self.tools:
            params = []
            for k, v in tool.parameters.items():
                desc = v.get('description', '') if isinstance(v, dict) else str(v)
                params.append(f"{k}: {desc}")
            lines.append(f"- {tool.name}({', '.join(params)}): {tool.description}")
        return "\\n".join(lines)
    
    def _extract_tool_calls(self, response: str) -> List[ToolCall]:
        """Extract tool calls from response - handles multiple formats"""
        tool_calls = []
        
        # Method 1: ```json blocks
        json_pattern = r'```json\s*\n(.*?)\n```'
        for block in re.findall(json_pattern, response, re.DOTALL | re.IGNORECASE):
            try:
                data = json.loads(block.strip())
                if isinstance(data, dict) and 'tool' in data:
                    tool_calls.append(ToolCall(
                        tool_name=data['tool'],
                        parameters=data.get('parameters', {}),
                        reasoning=data.get('reason', '')
                    ))
            except json.JSONDecodeError:
                continue
        
        # Method 2: Special model formats (<|message|>, <|constrain|>json<|message|>)
        if not tool_calls:
            # Find any <|constrain|>json<|message|> or <|message|> followed by JSON
            special_patterns = [
                r'<\|constrain\|>json<\|message\|>',
                r'<\|message\|>'
            ]
            
            for pattern in special_patterns:
                matches = list(re.finditer(pattern, response))
                for match in matches:
                    start = match.end()
                    # Find complete JSON object starting from here
                    if start < len(response):
                        # Skip whitespace
                        while start < len(response) and response[start] in ' \n\t':
                            start += 1
                        
                        if start < len(response) and response[start] == '{':
                            brace_count = 0
                            for j in range(start, len(response)):
                                if response[j] == '{':
                                    brace_count += 1
                                elif response[j] == '}':
                                    brace_count -= 1
                                    if brace_count == 0:
                                        try:
                                            json_str = response[start:j+1]
                                            data = json.loads(json_str)
                                            if isinstance(data, dict) and 'tool' in data:
                                                tool_calls.append(ToolCall(
                                                    tool_name=data['tool'],
                                                    parameters=data.get('parameters', {}),
                                                    reasoning=data.get('reason', '')
                                                ))
                                        except json.JSONDecodeError:
                                            pass
                                        break
                if tool_calls:
                    break
        
        # Method 3: Any JSON with "tool" key (last resort)
        if not tool_calls:
            for i in range(len(response)):
                if response[i] == '{':
                    brace_count = 0
                    for j in range(i, len(response)):
                        if response[j] == '{':
                            brace_count += 1
                        elif response[j] == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                try:
                                    data = json.loads(response[i:j+1])
                                    if isinstance(data, dict) and 'tool' in data:
                                        tool_calls.append(ToolCall(
                                            tool_name=data['tool'],
                                            parameters=data.get('parameters', {}),
                                            reasoning=data.get('reason', '')
                                        ))
                                except:
                                    pass
                                break
        
        return tool_calls

    def _clean_ai_response(self, response: str) -> str:
        """Remove special tokens from AI response"""
        # Remove <|channel|>, <|constrain|>, <|message|> tags
        cleaned = re.sub(r'<\|[^|]+\|>[^<]*', '', response)
        # Remove extra whitespace
        cleaned = '\n'.join(line for line in cleaned.split('\n') if line.strip())
        return cleaned.strip()
    
    def _exec_tool(self, tool_call: ToolCall, index: int, total: int) -> str:
        """Execute tool and return result"""
        tool = None
        for t in self.tools:
            if t.name == tool_call.tool_name:
                tool = t
                break
        
        if not tool:
            self.ui.print_error(f"Tool not found: {tool_call.tool_name}")
            return f"Error: Tool {tool_call.tool_name} not found"
        
        # Display
        self.ui.print_separator()
        print(f"\n>> AI wants to: {tool_call.tool_name}")
        if tool_call.reasoning:
            print(f"   Reason: {tool_call.reasoning}")
        print(f"\n   Parameters:")
        for key, value in tool_call.parameters.items():
            if key == 'content' and len(str(value)) > 200:
                print(f"     - {key}: {str(value)[:200]}... ({len(str(value))} chars)")
            else:
                print(f"     - {key}: {value}")
        print()
        
        # Confirm if needed
        if tool.requires_confirmation:
            choice = input(">> Execute? [y/n/v]: ").strip().lower()
            if choice == 'v' and 'content' in tool_call.parameters:
                print("\n" + "="*80)
                print(tool_call.parameters['content'])
                print("="*80 + "\\n")
                choice = input(">> Execute? [y/n]: ").strip().lower()
            
            if choice not in ['y', 'yes']:
                print(">> Cancelled")
                return "Cancelled by user"
        
        # Execute
        try:
            print(f">> Executing...")
            result = tool.execute(**tool_call.parameters)
            
            if result.success:
                print(f">> Success!")
                if result.output:
                    print(result.output)
                print()
                return result.output or "Success"
            else:
                print(f">> Failed:", end=" ")
                if result.error:
                    print(result.error)
                print()
                return f"Error: {result.error}"
        except Exception as e:
            print(f">> Error: {e}")
            print()
            return f"Error: {str(e)}"
    
    def _find_tool(self, name: str) -> Optional[Tool]:
        for t in self.tools:
            if t.name == name:
                return t
        return None
    
    def display_tools(self):
        self.ui.print_header("Available Tools")
        print()
        for i, tool in enumerate(self.tools, 1):
            conf = "[Confirm]" if tool.requires_confirmation else "[Auto]"
            print(f"  {i}. {tool.name} {conf}")
            print(f"     {tool.description}")
            print()
    
    def display_status(self):
        self.ui.print_header("Agent Status")
        print()
        print(f"  Workspace:   {self.config.workspace}")
        print(f"  Provider:    {self.config.provider}")
        print(f"  Model:       {self.config.model}")
        print(f"  Endpoint:    {self.config.endpoint}")
        print(f"  Tools:       {len(self.tools)}")
        print(f"  Autonomous:  Enabled")
        print()
