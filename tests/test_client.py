"""
Tests for client functionality.
"""

# import socket
import threading
import time
import pytest
from src.client import SearchClient
from src.server import SearchServer
from src.search import SearchAlgorithm


@pytest.fixture
def server_config(tmp_path, test_file):
    """Create a temporary config file."""
    config_path = tmp_path / "config.ini"
    with open(config_path, "w") as f:
        f.write(
            f"""
[server]
port = 0
ssl_enabled = true
reread_on_query = false

[file]
linuxpath = {test_file}

[rate_limit]
max_requests_per_minute = 100
window_seconds = 60
"""
        )
    return str(config_path)


@pytest.fixture
def client_config(tmp_path):
    """Create a temporary client config file."""
    config_path = tmp_path / "client_config.ini"
    with open(config_path, "w") as f:
        f.write(
            """
[server]
port = 0
ssl_enabled = true

[rate_limit]
max_requests_per_minute = 100
window_seconds = 60
"""
        )
    return str(config_path)


@pytest.fixture
def test_file(tmp_path):
    """Create a temporary test file."""
    file_content = """line1
line2
line3
test string
another line
search test
hello world"""
    file_path = tmp_path / "test.txt"
    file_path.write_text(file_content)
    return str(file_path)


def test_client_legacy_protocol(server_config, client_config, test_file):
    """Test client with legacy protocol."""
    # Start server
    server = SearchServer(server_config)
    server_thread = threading.Thread(target=server.start)
    server_thread.daemon = True
    server_thread.start()
    time.sleep(0.1)  # Give server time to start

    try:
        # Create client
        client = SearchClient(port=server.port, config_path=client_config)

        # Test search
        found, _ = client.search("test string", legacy=True)
        assert found is True

        # Test non-existent string
        found, _ = client.search("nonexistent", legacy=True)
        assert found is False

    finally:
        server.stop()
        server_thread.join(timeout=1)


def test_client_json_protocol(server_config, client_config, test_file):
    """Test client with JSON protocol."""
    # Start server
    server = SearchServer(server_config)
    server_thread = threading.Thread(target=server.start)
    server_thread.daemon = True
    server_thread.start()
    time.sleep(0.1)  # Give server time to start

    try:
        # Create client
        client = SearchClient(port=server.port, config_path=client_config)

        # Test search with different algorithms
        for algorithm in SearchAlgorithm:
            found, _ = client.search(
                query="test string", algorithm=algorithm.value, benchmark=True
            )
            assert isinstance(found, bool)

    finally:
        server.stop()
        server_thread.join(timeout=1)


def test_client_error_handling(server_config, client_config, test_file):
    """Test client error handling."""
    # Start server
    server = SearchServer(server_config)
    server_thread = threading.Thread(target=server.start)
    server_thread.daemon = True
    server_thread.start()
    time.sleep(0.1)  # Give server time to start

    try:
        # Create client
        client = SearchClient(port=server.port, config_path=client_config)

        # Test empty query
        with pytest.raises(ValueError, match="INVALID REQUEST"):
            found, _ = client.search("")

        # Test with special characters
        found, _ = client.search("test\nstring")
        assert isinstance(found, bool)

    finally:
        server.stop()
        server_thread.join(timeout=1)


def test_client_rate_limiting(server_config, client_config, test_file):
    """Test client rate limiting."""
    # Start server
    server = SearchServer(server_config)
    server_thread = threading.Thread(target=server.start)
    server_thread.daemon = True
    server_thread.start()
    time.sleep(0.1)  # Give server time to start

    try:
        # Create client
        client = SearchClient(port=server.port, config_path=client_config)

        # Make multiple requests quickly
        rate_limited = False
        for _ in range(110):  # Exceed rate limit
            try:
                found, _ = client.search("test string")
            except (RuntimeError, ConnectionError) as e:
                if (
                    "RATE LIMIT EXCEEDED" in str(e) or
                    "Connection closed" in str(e)
                        ):
                    rate_limited = True
                    break
                raise
        assert rate_limited, "Rate limiting not working"

    finally:
        server.stop()
        server_thread.join(timeout=1)


def test_client_connection_error():
    """Test client connection error handling."""
    client = SearchClient(port=99999)  # Invalid port
    with pytest.raises(ConnectionError):
        client.search("test string")


def test_client_timeout(server_config, client_config, test_file):
    """Test client timeout handling."""
    # Start server
    server = SearchServer(server_config)
    server_thread = threading.Thread(target=server.start)
    server_thread.daemon = True
    server_thread.start()
    time.sleep(0.1)  # Give server time to start

    try:
        # Create client with short timeout
        client = SearchClient(
            port=server.port, config_path=client_config, timeout=0.001
        )

        # Test timeout
        with pytest.raises((TimeoutError, ConnectionError)):
            client.search("__SLOW__")
    finally:
        server.stop()
        server_thread.join(timeout=1)
