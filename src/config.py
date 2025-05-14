"""
Configuration handling module.
"""
import configparser
from pathlib import Path
from typing import Optional


class Config:
    """Configuration handler for the search server."""

    def __init__(self, config_path: Optional[str] = None) -> None:
        """
        Initialize configuration handler.

        Args:
            config_path: Path to the configuration file. If None, looks for config.ini in the current directory.
        """
        self.config = configparser.ConfigParser()
        self.config_path = config_path or "config.ini"
        self.load_config()

    def load_config(self) -> None:
        """Load configuration from file."""
        if not Path(self.config_path).exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        self.config.read(self.config_path)

    @property
    def port(self) -> int:
        """Get server port from configuration."""
        return self.config.getint("server", "port", fallback=44445)

    @property
    def ssl_enabled(self) -> bool:
        """Get SSL enabled status from configuration."""
        return self.config.getboolean("server", "ssl_enabled", fallback=False)

    @property
    def reread_on_query(self) -> bool:
        """Get reread on query setting from configuration."""
        return self.config.getboolean("server", "reread_on_query", fallback=False)

    @property
    def file_path(self) -> str:
        """Get file path from configuration."""
        if not self.config.has_section("file"):
            raise ValueError("File path not found in configuration")
        
        path = self.config.get("file", "linuxpath", fallback=None)
        if not path:
            raise ValueError("File path not found in configuration")
        return path 