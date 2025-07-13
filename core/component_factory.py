from typing import Dict, Any, Type, Optional
import importlib
import logging

from .base_vector_store import VectorStore
from .base_document_store import DocumentStore
from .base_memory_backend import MemoryBackend
from .base_config_provider import ConfigProvider, CompositeConfigProvider, EnvironmentConfigProvider
from .base_llm_provider import LLMProvider
from .base_embedding_provider import EmbeddingProvider
from .base_tool import BaseTool, ToolRegistry

logger = logging.getLogger(__name__)


class ComponentFactory:
    """Factory for creating components based on configuration."""
    
    # Registry of available implementations
    _vector_store_registry: Dict[str, Type[VectorStore]] = {}
    _document_store_registry: Dict[str, Type[DocumentStore]] = {}
    _memory_backend_registry: Dict[str, Type[MemoryBackend]] = {}
    _config_provider_registry: Dict[str, Type[ConfigProvider]] = {}
    _llm_provider_registry: Dict[str, Type[LLMProvider]] = {}
    _embedding_provider_registry: Dict[str, Type[EmbeddingProvider]] = {}
    _tool_registry: Dict[str, Type[BaseTool]] = {}
    
    @classmethod
    def register_vector_store(cls, name: str, implementation: Type[VectorStore]) -> None:
        """Register a vector store implementation."""
        cls._vector_store_registry[name] = implementation
        logger.debug(f"Registered vector store: {name}")
    
    @classmethod
    def register_document_store(cls, name: str, implementation: Type[DocumentStore]) -> None:
        """Register a document store implementation."""
        cls._document_store_registry[name] = implementation
        logger.debug(f"Registered document store: {name}")
    
    @classmethod
    def register_memory_backend(cls, name: str, implementation: Type[MemoryBackend]) -> None:
        """Register a memory backend implementation."""
        cls._memory_backend_registry[name] = implementation
        logger.debug(f"Registered memory backend: {name}")
    
    @classmethod
    def register_config_provider(cls, name: str, implementation: Type[ConfigProvider]) -> None:
        """Register a config provider implementation."""
        cls._config_provider_registry[name] = implementation
        logger.debug(f"Registered config provider: {name}")
    
    @classmethod
    def register_llm_provider(cls, name: str, implementation: Type[LLMProvider]) -> None:
        """Register an LLM provider implementation."""
        cls._llm_provider_registry[name] = implementation
        logger.debug(f"Registered LLM provider: {name}")
    
    @classmethod
    def register_embedding_provider(cls, name: str, implementation: Type[EmbeddingProvider]) -> None:
        """Register an embedding provider implementation."""
        cls._embedding_provider_registry[name] = implementation
        logger.debug(f"Registered embedding provider: {name}")
    
    @classmethod
    def register_tool(cls, name: str, implementation: Type[BaseTool]) -> None:
        """Register a tool implementation."""
        cls._tool_registry[name] = implementation
        logger.debug(f"Registered tool: {name}")
    
    @classmethod
    def create_vector_store(cls, config: Dict[str, Any]) -> VectorStore:
        """
        Create a vector store instance based on configuration.
        
        Args:
            config: Configuration dictionary with 'type' key
            
        Returns:
            VectorStore instance
            
        Raises:
            ValueError: If vector store type is not registered
        """
        store_type = config.get('type', 'chroma')  # Default to chroma
        
        if store_type not in cls._vector_store_registry:
            raise ValueError(f"Unknown vector store type: {store_type}")
        
        implementation = cls._vector_store_registry[store_type]
        return implementation(config)
    
    @classmethod
    def create_document_store(cls, config: Dict[str, Any]) -> DocumentStore:
        """
        Create a document store instance based on configuration.
        
        Args:
            config: Configuration dictionary with 'type' key
            
        Returns:
            DocumentStore instance
            
        Raises:
            ValueError: If document store type is not registered
        """
        store_type = config.get('type', 'filesystem')  # Default to filesystem
        
        if store_type not in cls._document_store_registry:
            raise ValueError(f"Unknown document store type: {store_type}")
        
        implementation = cls._document_store_registry[store_type]
        return implementation(config)
    
    @classmethod
    def create_memory_backend(cls, config: Dict[str, Any]) -> MemoryBackend:
        """
        Create a memory backend instance based on configuration.
        
        Args:
            config: Configuration dictionary with 'type' key
            
        Returns:
            MemoryBackend instance
            
        Raises:
            ValueError: If memory backend type is not registered
        """
        backend_type = config.get('type', 'in_memory')  # Default to in_memory
        
        if backend_type not in cls._memory_backend_registry:
            raise ValueError(f"Unknown memory backend type: {backend_type}")
        
        implementation = cls._memory_backend_registry[backend_type]
        return implementation(config)
    
    @classmethod
    def create_config_provider(cls, config: Optional[Dict[str, Any]] = None) -> ConfigProvider:
        """
        Create a config provider instance.
        
        Args:
            config: Optional configuration for custom provider setup
            
        Returns:
            ConfigProvider instance (defaults to composite provider)
        """
        if config and 'type' in config:
            provider_type = config['type']
            if provider_type in cls._config_provider_registry:
                implementation = cls._config_provider_registry[provider_type]
                return implementation(config)
        
        # Default: Create composite provider with standard hierarchy
        try:
            # Try to import and create YAML provider
            yaml_provider = cls._create_yaml_provider()
            providers = [
                EnvironmentConfigProvider(),
                yaml_provider,
                cls._create_default_provider()
            ]
        except ImportError:
            # Fallback to just environment and defaults
            providers = [
                EnvironmentConfigProvider(),
                cls._create_default_provider()
            ]
        
        return CompositeConfigProvider(providers)
    
    @classmethod
    def create_llm_provider(cls, config: Dict[str, Any]) -> LLMProvider:
        """
        Create an LLM provider instance based on configuration.
        
        Args:
            config: Configuration dictionary with 'type' key
            
        Returns:
            LLMProvider instance
            
        Raises:
            ValueError: If LLM provider type is not registered
        """
        provider_type = config.get('type', 'openai')  # Default to OpenAI
        
        if provider_type not in cls._llm_provider_registry:
            raise ValueError(f"Unknown LLM provider type: {provider_type}")
        
        implementation = cls._llm_provider_registry[provider_type]
        return implementation(config)
    
    @classmethod
    def create_embedding_provider(cls, config: Dict[str, Any]) -> EmbeddingProvider:
        """
        Create an embedding provider instance based on configuration.
        
        Args:
            config: Configuration dictionary with 'type' key
            
        Returns:
            EmbeddingProvider instance
            
        Raises:
            ValueError: If embedding provider type is not registered
        """
        provider_type = config.get('type', 'openai')  # Default to OpenAI
        
        if provider_type not in cls._embedding_provider_registry:
            raise ValueError(f"Unknown embedding provider type: {provider_type}")
        
        implementation = cls._embedding_provider_registry[provider_type]
        return implementation(config)
    
    @classmethod
    def create_tool_registry(cls, tool_configs: List[Dict[str, Any]]) -> ToolRegistry:
        """
        Create a tool registry with specified tools.
        
        Args:
            tool_configs: List of tool configurations
            
        Returns:
            ToolRegistry with registered tools
        """
        registry = ToolRegistry()
        
        for tool_config in tool_configs:
            tool_type = tool_config.get('type')
            if tool_type in cls._tool_registry:
                implementation = cls._tool_registry[tool_type]
                tool_instance = implementation(tool_config)
                registry.register_tool(tool_instance)
            else:
                logger.warning(f"Unknown tool type: {tool_type}")
        
        return registry
    
    @classmethod
    def _create_yaml_provider(cls):
        """Create YAML config provider (may raise ImportError)."""
        # Import here to avoid hard dependency
        try:
            from ..providers.yaml_config_provider import YAMLConfigProvider
            return YAMLConfigProvider()
        except ImportError:
            raise ImportError("YAML config provider not available")
    
    @classmethod
    def _create_default_provider(cls):
        """Create default config provider with fallback values."""
        try:
            from ..providers.default_config_provider import DefaultConfigProvider
            return DefaultConfigProvider()
        except ImportError:
            # If default provider not available, create a minimal one
            from .base_config_provider import ConfigProvider
            
            class MinimalDefaultProvider(ConfigProvider):
                def __init__(self):
                    self.defaults = {
                        'vector_store.type': 'chroma',
                        'vector_store.path': './data/vectors',
                        'memory.type': 'in_memory',
                        'llm.type': 'openai',
                        'llm.model': 'gpt-3.5-turbo',
                        'embedding.type': 'openai',
                        'embedding.model': 'text-embedding-ada-002'
                    }
                
                def get_config(self, key: str, default=None):
                    return self.defaults.get(key, default)
                
                def set_config(self, key: str, value):
                    self.defaults[key] = value
                    return True
                
                def has_config(self, key: str) -> bool:
                    return key in self.defaults
                
                def get_section(self, section: str) -> Dict[str, Any]:
                    result = {}
                    prefix = f"{section}."
                    for key, value in self.defaults.items():
                        if key.startswith(prefix):
                            result[key[len(prefix):]] = value
                    return result
                
                def list_keys(self, prefix=None) -> list:
                    if prefix:
                        return [k for k in self.defaults.keys() if k.startswith(prefix)]
                    return list(self.defaults.keys())
            
            return MinimalDefaultProvider()
    
    @classmethod
    def auto_register_implementations(cls) -> None:
        """
        Automatically discover and register implementations.
        This method will scan for implementations in the providers package.
        """
        try:
            # Import default implementations to trigger registration
            import providers.chroma_vector_store  # noqa
            import providers.filesystem_document_store  # noqa
            import providers.in_memory_backend  # noqa
            import providers.openai_llm_provider  # noqa
            import providers.openai_embedding_provider  # noqa
            import tools.web_search_tool  # noqa
            import tools.calculator_tool  # noqa
            import tools.file_operations_tool  # noqa
            import tools.code_execution_tool  # noqa
            logger.info("Auto-registered all available implementations")
        except ImportError as e:
            logger.warning(f"Some implementations not available for auto-registration: {e}")
    
    @classmethod
    def list_available_implementations(cls) -> Dict[str, list]:
        """
        List all available implementations by category.
        
        Returns:
            Dictionary mapping component types to available implementations
        """
        return {
            'vector_stores': list(cls._vector_store_registry.keys()),
            'document_stores': list(cls._document_store_registry.keys()),
            'memory_backends': list(cls._memory_backend_registry.keys()),
            'config_providers': list(cls._config_provider_registry.keys()),
            'llm_providers': list(cls._llm_provider_registry.keys()),
            'embedding_providers': list(cls._embedding_provider_registry.keys()),
            'tools': list(cls._tool_registry.keys())
        }