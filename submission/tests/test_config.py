"""
Tests for configuration handling.
"""

# import os
import pytest
from src.config import Config


@pytest.fixture
def config_file(tmp_path):
    """Create a temporary config file."""
    config_content = """
[server]
port = 44445
ssl_enabled = true
reread_on_query = false

[file]
linuxpath = /test/path/file.txt
"""
    config_path = tmp_path / "config.ini"
    config_path.write_text(config_content)
    return str(config_path)


def test_config_loading(config_file):
    """Test configuration loading."""
    config = Config(config_file)

    assert config.port == 44445
    assert config.ssl_enabled is True
    assert config.reread_on_query is False
    assert config.file_path == "/test/path/file.txt"


def test_config_defaults(tmp_path):
    """Test configuration defaults."""
    config_content = """
[server]
port = 44445

[file]
linuxpath = /test/path/file.txt
"""
    config_path = tmp_path / "config.ini"
    config_path.write_text(config_content)

    config = Config(str(config_path))

    assert config.ssl_enabled is False
    assert config.reread_on_query is False


def test_missing_file_path(tmp_path):
    """Test handling of missing file path."""
    config_content = """
[server]
port = 44445
"""
    config_path = tmp_path / "config.ini"
    config_path.write_text(config_content)

    config = Config(str(config_path))
    with pytest.raises(ValueError, match="File not found in config"):
        _ = config.file_path


def test_invalid_config_file():
    """Test handling of invalid config file."""
    with pytest.raises(FileNotFoundError):
        Config("nonexistent.ini")
