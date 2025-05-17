"""
Tests for client functionality.
"""
import socket
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
        f.write(f"""
[server]
port = 0
ssl_enabled = false
reread_on_query = false

[file]
linuxpath = {test_file}

[rate_limit]
max_requests_per_minute = 100
window_seconds = 60
""")
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


def test_client_legacy_protocol(server_config, test_file):
    """Test client with legacy protocol."""
    # Start server
    server = SearchServer(server_config)
    server_thread = threading.Thread(target=server.start)
    server_thread.daemon = True
    server_thread.start()
    time.sleep(0.1)  # Give server time to start

    try:
        # Create client
        client = SearchClient(server.port)
        
        # Test search
        result = client.search("test string")
        assert result == "STRING EXISTS"
        
        # Test non-existent string
        result = client.search("nonexistent")
        assert result == "STRING NOT FOUND"
        
    finally:
        server.stop()
        server_thread.join(timeout=1)


def test_client_json_protocol(server_config, test_file):
    """Test client with JSON protocol."""
    # Start server
    server = SearchServer(server_config)
    server_thread = threading.Thread(target=server.start)
    server_thread.daemon = True
    server_thread.start()
    time.sleep(0.1)  # Give server time to start

    try:
        # Create client
        client = SearchClient(server.port)
        
        # Test search with different algorithms
        for algorithm in SearchAlgorithm:
            result = client.search_json(
                query="test string",
                algorithm=algorithm,
                benchmark=True
            )
            assert result in ["STRING EXISTS", "STRING NOT FOUND"]
            
    finally:
        server.stop()
        server_thread.join(timeout=1)


def test_client_error_handling(server_config, test_file):
    """Test client error handling."""
    # Start server
    server = SearchServer(server_config)
    server_thread = threading.Thread(target=server.start)
    server_thread.daemon = True
    server_thread.start()
    time.sleep(0.1)  # Give server time to start

    try:
        # Create client
        client = SearchClient(server.port)
        
        # Test empty query
        result = client.search("")
        assert result == "STRING NOT FOUND"
        
        # Test with special characters
        result = client.search("test\nstring")
        assert result in ["STRING EXISTS", "STRING NOT FOUND"]
        
    finally:
        server.stop()
        server_thread.join(timeout=1)


def test_client_rate_limiting(server_config, test_file):
    """Test client rate limiting."""
    # Start server
    server = SearchServer(server_config)
    server_thread = threading.Thread(target=server.start)
    server_thread.daemon = True
    server_thread.start()
    time.sleep(0.1)  # Give server time to start

    try:
        # Create client
        client = SearchClient(server.port)
        
        # Make multiple requests quickly
        for _ in range(110):  # Exceed rate limit
            try:
                result = client.search("test string")
                if result == "RATE LIMIT EXCEEDED":
                    break
            except Exception:
                continue
        else:
            pytest.fail("Rate limiting not working")
            
    finally:
        server.stop()
        server_thread.join(timeout=1)


def test_client_connection_error():
    """Test client connection error handling."""
    client = SearchClient(99999)  # Invalid port
    with pytest.raises(ConnectionRefusedError):
        client.search("test string")


def test_client_timeout(server_config, test_file):
    """Test client timeout handling."""
    # Start server
    server = SearchServer(server_config)
    server_thread = threading.Thread(target=server.start)
    server_thread.daemon = True
    server_thread.start()
    time.sleep(0.1)  # Give server time to start

    try:
        # Create client with short timeout
        client = SearchClient(server.port, timeout=0.001)
        
        # Test timeout
        with pytest.raises(socket.timeout):
            client.search("test string")
            
    finally:
        server.stop()
        server_thread.join(timeout=1) 