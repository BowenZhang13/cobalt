"""
LLM client implementations using LiteLLM
"""

import time
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import litellm
from litellm import completion
import os


@dataclass
class Message:
    """Chat message"""
    role: str  # system, user, assistant
    content: str


@dataclass
class LLMResponse:
    """LLM response with metadata"""
    content: str
    success: bool
    latency_ms: float
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    error: Optional[str] = None


class LMStudioClient:
    """LM Studio client using LiteLLM"""
    
    def __init__(self, endpoint: str = "http://localhost:1234", model: str = "local-model", timeout: int = 120):
        """
        Initialize LM Studio client
        
        Args:
            endpoint: LM Studio API endpoint (default: http://localhost:1234)
            model: Model name to use
            timeout: Request timeout in seconds
        """
        self.endpoint = endpoint.rstrip('/')
        self.model = model
        self.timeout = timeout
        
        # Configure environment for LM Studio (OpenAI-compatible)
        os.environ['OPENAI_API_KEY'] = 'dummy-key'  # LM Studio doesn't need a real key
        os.environ['OPENAI_API_BASE'] = f"{self.endpoint}/v1"
        
        # Disable litellm logging spam
        litellm.suppress_debug_info = True
        litellm.set_verbose = False


    def generate(self, messages: List[Message], temperature: float = 0.7, 
                max_tokens: int = 4096) -> LLMResponse:
        """
        Generate response from LM Studio
        
        Args:
            messages: List of chat messages
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            
        Returns:
            LLMResponse with generated content and metadata
        """
        start_time = time.time()
        
        try:
            # Convert messages to OpenAI format
            openai_messages = [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ]
            
            # Use litellm to call LM Studio (OpenAI-compatible)
            response = completion(
                model=f"openai/{self.model}",  # Use openai/ prefix for custom endpoints
                messages=openai_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                api_base=f"{self.endpoint}/v1",
                api_key="dummy-key",  # LM Studio doesn't need a real key
                timeout=self.timeout
            )
            
            latency = (time.time() - start_time) * 1000
            
            # Extract response
            content = response.choices[0].message.content
            
            return LLMResponse(
                content=content,
                success=True,
                latency_ms=latency,
                model=self.model,
                prompt_tokens=response.usage.prompt_tokens if hasattr(response, 'usage') else 0,
                completion_tokens=response.usage.completion_tokens if hasattr(response, 'usage') else 0,
                total_tokens=response.usage.total_tokens if hasattr(response, 'usage') else 0
            )
            
        except Exception as e:
            latency = (time.time() - start_time) * 1000
            error_msg = str(e)
            
            if "Connection" in error_msg or "connect" in error_msg.lower():
                error_msg = f"Connection failed: {error_msg}\n\nMake sure LM Studio is running:\n1. Open LM Studio\n2. Load a model\n3. Click 'Start Server' (local inference)\n4. Check it's running on {self.endpoint}"
            
            return LLMResponse(
                content="",
                success=False,
                latency_ms=latency,
                model=self.model,
                error=error_msg
            )
    
    def list_models(self) -> List[str]:
        """
        List available models from LM Studio
        
        Returns:
            List of model names
        """
        try:
            import requests
            response = requests.get(f"{self.endpoint}/v1/models", timeout=5)
            response.raise_for_status()
            
            data = response.json()
            models = [model['id'] for model in data.get('data', [])]
            return models if models else ["No models loaded - load a model in LM Studio"]
            
        except Exception as e:
            return [f"Error: {e}"]
    
    def test_connection(self) -> bool:
        """
        Test LM Studio connection
        
        Returns:
            True if connection successful
        """
        try:
            import requests
            response = requests.get(f"{self.endpoint}/v1/models", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def test_connection(self) -> bool:
        """
        Test LM Studio connection
        
        Returns:
            True if connection successful
        """
        try:
            url = f"{self.endpoint}/v1/models"
            response = self.session.get(url, timeout=5)
            return response.status_code == 200
        except:
            return False


def create_llm_client(endpoint: str = "http://localhost:1234", model: str = "local-model", 
                     timeout: int = 120) -> LMStudioClient:
    """
    Create LM Studio client using LiteLLM
    
    Args:
        endpoint: LM Studio endpoint URL (default: http://localhost:1234)
        model: Model name
        timeout: Request timeout in seconds
        
    Returns:
        LM Studio client instance
    """
    return LMStudioClient(endpoint, model, timeout)
