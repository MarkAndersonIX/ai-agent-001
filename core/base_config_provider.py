import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class ConfigProvider(ABC):
    """Abstract base class for configuration providers."""

    @abstractmethod
    def get_config(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by key.

        Args:
            key: Configuration key (supports dot notation, e.g., 'llm.temperature')
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        pass

    @abstractmethod
    def set_config(self, key: str, value: Any) -> bool:
        """
        Set a configuration value.

        Args:
            key: Configuration key
            value: Value to set

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def has_config(self, key: str) -> bool:
        """
        Check if a configuration key exists.

        Args:
            key: Configuration key to check

        Returns:
            True if key exists, False otherwise
        """
        pass

    @abstractmethod
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get an entire configuration section.

        Args:
            section: Section name

        Returns:
            Dictionary containing section configuration
        """
        pass

    @abstractmethod
    def list_keys(self, prefix: Optional[str] = None) -> List[str]:
        """
        List all configuration keys, optionally filtered by prefix.

        Args:
            prefix: Optional key prefix filter

        Returns:
            List of configuration keys
        """
        pass


class CompositeConfigProvider(ConfigProvider):
    """Configuration provider that chains multiple providers with precedence."""

    def __init__(self, providers: List[ConfigProvider]):
        """
        Initialize with ordered list of providers (highest precedence first).

        Args:
            providers: List of config providers in precedence order
        """
        self.providers = providers

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get config value from first provider that has it."""
        for provider in self.providers:
            if provider.has_config(key):
                return provider.get_config(key, default)
        return default

    def set_config(self, key: str, value: Any) -> bool:
        """Set config value in the first provider that supports writing."""
        for provider in self.providers:
            try:
                return provider.set_config(key, value)
            except NotImplementedError:
                continue
        return False

    def has_config(self, key: str) -> bool:
        """Check if any provider has the key."""
        return any(provider.has_config(key) for provider in self.providers)

    def get_section(self, section: str) -> Dict[str, Any]:
        """Merge section from all providers (highest precedence wins)."""
        result = {}
        # Reverse order so highest precedence overwrites
        for provider in reversed(self.providers):
            try:
                section_data = provider.get_section(section)
                result.update(section_data)
            except (KeyError, NotImplementedError):
                continue
        return result

    def list_keys(self, prefix: Optional[str] = None) -> List[str]:
        """Combine keys from all providers."""
        all_keys = set()
        for provider in self.providers:
            try:
                keys = provider.list_keys(prefix)
                all_keys.update(keys)
            except NotImplementedError:
                continue
        return sorted(list(all_keys))


class EnvironmentConfigProvider(ConfigProvider):
    """Configuration provider that reads from environment variables."""

    def __init__(self, prefix: str = "AGENT_"):
        """
        Initialize with optional environment variable prefix.

        Args:
            prefix: Prefix for environment variables (e.g., 'AGENT_')
        """
        self.prefix = prefix

    def _env_key(self, key: str) -> str:
        """Convert config key to environment variable name."""
        # Convert dot notation to uppercase with underscores
        env_key = key.replace(".", "_").upper()
        return f"{self.prefix}{env_key}"

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get config from environment variable."""
        env_key = self._env_key(key)
        value = os.getenv(env_key, default)

        # Try to convert string values to appropriate types
        if isinstance(value, str):
            # Boolean conversion
            if value.lower() in ("true", "false"):
                return value.lower() == "true"
            # Integer conversion
            try:
                return int(value)
            except ValueError:
                pass
            # Float conversion
            try:
                return float(value)
            except ValueError:
                pass

        return value

    def set_config(self, key: str, value: Any) -> bool:
        """Set environment variable (for current process only)."""
        env_key = self._env_key(key)
        os.environ[env_key] = str(value)
        return True

    def has_config(self, key: str) -> bool:
        """Check if environment variable exists."""
        env_key = self._env_key(key)
        return env_key in os.environ

    def get_section(self, section: str) -> Dict[str, Any]:
        """Get all environment variables for a section."""
        section_prefix = self._env_key(f"{section}.")
        result = {}

        for env_key, value in os.environ.items():
            if env_key.startswith(section_prefix):
                # Convert back to config key
                config_key = env_key[len(self.prefix) :].lower().replace("_", ".")
                # Remove section prefix
                if config_key.startswith(f"{section}."):
                    key = config_key[len(section) + 1 :]
                    result[key] = self.get_config(config_key)

        return result

    def list_keys(self, prefix: Optional[str] = None) -> List[str]:
        """List all environment variables as config keys."""
        keys = []
        env_prefix = self.prefix
        if prefix:
            env_prefix += prefix.replace(".", "_").upper()

        for env_key in os.environ.keys():
            if env_key.startswith(env_prefix):
                # Convert to config key format
                config_key = env_key[len(self.prefix) :].lower().replace("_", ".")
                keys.append(config_key)

        return sorted(keys)
