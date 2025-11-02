"""
Configuration management for Cobalt
"""

import os
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from pathlib import Path
import json


@dataclass
class Config:
    """Main configuration for Cobalt agent"""
    
    # Workspace settings
    workspace: Path = field(default_factory=lambda: Path.cwd())
    
    # LLM settings
    endpoint: str = "http://localhost:1234"
    model: str = "local-model"  # The model name shown in LM Studio
    
    # Generation settings
    temperature: float = 0.7
    max_tokens: int = 4096
    timeout: int = 120
    
    # Agent settings
    max_iterations: int = 10
    show_thinking: bool = True
    verbose: bool = False
    safe_mode: bool = False  # Restrict command execution to safe commands
    provider: str = "lmstudio"  # LLM provider
    
    # File settings
    ignore_patterns: list = field(default_factory=lambda: [
        "__pycache__",
        "*.pyc",
        ".git",
        ".venv",
        "venv",
        "node_modules",
        ".env"
    ])
    
    def __post_init__(self):
        """Validate and normalize configuration"""
        self.workspace = Path(self.workspace).resolve()
    
    @classmethod
    def from_file(cls, filepath: str) -> 'Config':
        """Load configuration from JSON file"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls(**data)
    
    @classmethod
    def from_env(cls) -> 'Config':
        """Load configuration from environment variables"""
        config = cls()
        
        if workspace := os.getenv('COBALT_WORKSPACE'):
            config.workspace = Path(workspace)
        
        if endpoint := os.getenv('COBALT_ENDPOINT'):
            config.endpoint = endpoint
        
        if model := os.getenv('COBALT_MODEL'):
            config.model = model
        
        if temp := os.getenv('COBALT_TEMPERATURE'):
            config.temperature = float(temp)
        
        if tokens := os.getenv('COBALT_MAX_TOKENS'):
            config.max_tokens = int(tokens)
        
        return config
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary"""
        return {
            'workspace': str(self.workspace),
            'provider': self.provider,
            'endpoint': self.endpoint,
            'model': self.model,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            'timeout': self.timeout,
            'max_iterations': self.max_iterations,
            'show_thinking': self.show_thinking,
            'verbose': self.verbose,
            'safe_mode': self.safe_mode
        }
    
    def save(self, filepath: str):
        """Save configuration to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    def validate(self) -> bool:
        """Validate configuration"""
        if not self.workspace.exists():
            raise ValueError(f"Workspace does not exist: {self.workspace}")
        
        if self.provider not in ['ollama', 'lmstudio']:
            raise ValueError(f"Invalid provider: {self.provider}")
        
        if self.temperature < 0 or self.temperature > 2:
            raise ValueError(f"Temperature must be between 0 and 2: {self.temperature}")
        
        if self.max_tokens < 1:
            raise ValueError(f"max_tokens must be positive: {self.max_tokens}")
        
        return True
