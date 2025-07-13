import os
import yaml
from typing import Any, Dict, List, Optional
from pathlib import Path

from core.base_config_provider import ConfigProvider


class YAMLConfigProvider(ConfigProvider):
    """YAML file-based configuration provider."""
    
    def __init__(self, config_paths: Optional[List[str]] = None):
        """
        Initialize YAML config provider.
        
        Args:
            config_paths: List of YAML file paths to load (in order of precedence)
        """
        self.config_data = {}
        
        # Default config paths if none provided
        if config_paths is None:
            config_paths = [
                './config/default.yaml',
                './config/local.yaml',
                './config/production.yaml'
            ]
        
        self.config_paths = config_paths
        self._load_configs()
    
    def _load_configs(self) -> None:
        """Load configuration from YAML files."""
        for config_path in self.config_paths:
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config_data = yaml.safe_load(f) or {}
                    
                    # Merge with existing config (later files override earlier ones)
                    self._deep_merge(self.config_data, config_data)
                    
                except Exception as e:
                    print(f"Warning: Failed to load config file {config_path}: {e}")
    
    def _deep_merge(self, target: Dict, source: Dict) -> None:
        """Deep merge source dictionary into target dictionary."""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_merge(target[key], value)
            else:
                target[key] = value
    
    def _get_nested_value(self, data: Dict, key_path: str, default: Any = None) -> Any:
        """Get value from nested dictionary using dot notation."""
        keys = key_path.split('.')
        current = data
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        
        return current
    
    def _set_nested_value(self, data: Dict, key_path: str, value: Any) -> None:
        """Set value in nested dictionary using dot notation."""
        keys = key_path.split('.')
        current = data
        
        # Navigate to the parent of the target key
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            elif not isinstance(current[key], dict):
                current[key] = {}
            current = current[key]
        
        # Set the final value
        current[keys[-1]] = value
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key."""
        return self._get_nested_value(self.config_data, key, default)
    
    def set_config(self, key: str, value: Any) -> bool:
        """Set a configuration value (in memory only)."""
        try:
            self._set_nested_value(self.config_data, key, value)
            return True
        except Exception:
            return False
    
    def has_config(self, key: str) -> bool:
        """Check if a configuration key exists."""
        return self._get_nested_value(self.config_data, key, object()) is not object()
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get an entire configuration section."""
        section_data = self._get_nested_value(self.config_data, section, {})
        return section_data if isinstance(section_data, dict) else {}
    
    def list_keys(self, prefix: Optional[str] = None) -> List[str]:
        """List all configuration keys, optionally filtered by prefix."""
        keys = []
        self._collect_keys(self.config_data, '', keys)
        
        if prefix:
            keys = [k for k in keys if k.startswith(prefix)]
        
        return sorted(keys)
    
    def _collect_keys(self, data: Dict, current_path: str, keys: List[str]) -> None:
        """Recursively collect all keys from nested dictionary."""
        for key, value in data.items():
            full_key = f"{current_path}.{key}" if current_path else key
            keys.append(full_key)
            
            if isinstance(value, dict):
                self._collect_keys(value, full_key, keys)
    
    def save_config(self, output_path: str) -> bool:
        """
        Save current configuration to a YAML file.
        
        Args:
            output_path: Path where to save the configuration
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure directory exists
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                yaml.dump(
                    self.config_data, 
                    f, 
                    default_flow_style=False,
                    sort_keys=True,
                    indent=2
                )
            return True
        except Exception:
            return False
    
    def reload_configs(self) -> bool:
        """Reload configuration from files."""
        try:
            self.config_data = {}
            self._load_configs()
            return True
        except Exception:
            return False
    
    def add_config_path(self, config_path: str) -> bool:
        """
        Add a new configuration file path and load it.
        
        Args:
            config_path: Path to additional YAML config file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f) or {}
                
                self._deep_merge(self.config_data, config_data)
                
                if config_path not in self.config_paths:
                    self.config_paths.append(config_path)
                
                return True
        except Exception:
            pass
        
        return False
    
    def get_config_info(self) -> Dict[str, Any]:
        """Get information about loaded configuration files."""
        info = {
            'config_paths': self.config_paths,
            'loaded_files': [],
            'total_keys': len(self.list_keys())
        }
        
        for path in self.config_paths:
            if os.path.exists(path):
                info['loaded_files'].append(path)
        
        return info


# Create default configuration content
DEFAULT_CONFIG_YAML = """
# AI Agent Base - Default Configuration

# Vector Store Configuration
vector_store:
  type: "chroma"
  path: "./data/vectors"
  collection_name: "ai_agents"
  allow_reset: false
  anonymized_telemetry: false

# Document Store Configuration  
document_store:
  type: "filesystem"
  path: "./data/documents"

# Memory Backend Configuration
memory:
  type: "in_memory"
  max_sessions: 1000
  session_timeout_hours: 24

# LLM Provider Configuration
llm:
  type: "openai"
  model: "gpt-3.5-turbo"
  temperature: 0.7
  max_tokens: 2000
  api_key: "${OPENAI_API_KEY}"

# Embedding Provider Configuration
embedding:
  type: "openai"
  model: "text-embedding-ada-002"
  api_key: "${OPENAI_API_KEY}"

# Agent Configurations
agents:
  general:
    system_prompt: |
      You are a helpful AI assistant that can answer questions and help with various tasks.
    tools:
      - web_search
      - calculator
    rag_settings:
      top_k: 5
      similarity_threshold: 0.7
    
  code_assistant:
    system_prompt: |
      You are an expert code assistant that helps developers write clean, 
      efficient code following best practices.
    tools:
      - web_search
      - file_operations
      - code_execution
    rag_settings:
      top_k: 7
      similarity_threshold: 0.8
    document_sources:
      - path: "./data/programming-docs/"
        types: ["pdf", "md", "txt"]
        recursive: true
    
  research_agent:
    system_prompt: |
      You are a research assistant that finds credible sources, 
      summarizes complex topics, and provides citations.
    tools:
      - web_search
    rag_settings:
      top_k: 10
      similarity_threshold: 0.6
    
  document_qa:
    system_prompt: |
      You are a document analysis assistant that answers questions 
      based on provided documents with accurate citations.
    tools: []
    rag_settings:
      top_k: 8
      similarity_threshold: 0.7

# Tool Configurations
tools:
  web_search:
    type: "web_search"
    cache_results: true
    max_results: 5
    
  calculator:
    type: "calculator"
    
  file_operations:
    type: "file_operations"
    allowed_paths: ["./data/", "./workspace/"]
    
  code_execution:
    type: "code_execution"
    timeout_seconds: 30
    allowed_languages: ["python", "javascript"]

# API Configuration
api:
  host: "0.0.0.0"
  port: 8000
  debug: false
  cors_enabled: true

# Logging Configuration
logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "./logs/ai_agent.log"
"""


def create_default_config_file(config_dir: str = "./config") -> bool:
    """
    Create default configuration file if it doesn't exist.
    
    Args:
        config_dir: Directory to create config file in
        
    Returns:
        True if successful, False otherwise
    """
    try:
        config_path = Path(config_dir)
        config_path.mkdir(parents=True, exist_ok=True)
        
        default_file = config_path / "default.yaml"
        if not default_file.exists():
            with open(default_file, 'w', encoding='utf-8') as f:
                f.write(DEFAULT_CONFIG_YAML)
            return True
        return True
    except Exception:
        return False


# Register with factory
from core.component_factory import ComponentFactory
ComponentFactory.register_config_provider('yaml', YAMLConfigProvider)