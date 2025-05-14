"""
Tests for server functionality.
"""
import socket
import threading
import time
import pytest
from src.server import SearchServer


@pytest.fixture
def server_config(tmp_path, test_file):
    """Create a temporary server configuration."""
    config_content = f"""
[server]
port = 44445
ssl_enabled = false
reread_on_query = false

[file]
linuxpath = {test_file}
"""
    config_path = tmp_path / "config.ini"
    config_path.write_text(config_content)
    return str(config_path)


@pytest.fixture
def test_file(tmp_path):
    """Create a temporary test file."""
    file_content = """line1
line2
line3
test string
another line"""
    file_path = tmp_path / "test.txt"
    file_path.write_text(file_content)
    return str(file_path)


def test_server_start_stop(server_config, test_file):
    """Test server start and stop."""
    server = SearchServer(server_config)
    
    # Start server in a separate thread
    server_thread = threading.Thread(target=server.start)
    server_thread.daemon = True
    server_thread.start()
    
    # Give server time to start
    time.sleep(0.1)
    
    # Stop server
    server.stop()
    
    # Wait for thread to finish
    server_thread.join(timeout=1)
    assert not server_thread.is_alive()


def test_server_connection(server_config, test_file):
    """Test server connection and response."""
    server = SearchServer(server_config)
    
    # Start server in a separate thread
    server_thread = threading.Thread(target=server.start)
    server_thread.daemon = True
    server_thread.start()
    
    # Give server time to start
    time.sleep(0.1)
    
    try:
        # Connect to server
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('localhost', 44445))
        
        # Send test string
        client.sendall(b"test string\n")
        
        # Receive response
        response = client.recv(1024).decode('utf-8')
        assert response == "STRING EXISTS\n"
        
    finally:
        client.close()
        server.stop()
        server_thread.join(timeout=1)


def test_server_nonexistent_string(server_config, test_file):
    """Test server response for nonexistent string."""
    server = SearchServer(server_config)
    
    # Start server in a separate thread
    server_thread = threading.Thread(target=server.start)
    server_thread.daemon = True
    server_thread.start()
    
    # Give server time to start
    time.sleep(0.1)
    
    try:
        # Connect to server
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('localhost', 44445))
        
        # Send nonexistent string
        client.sendall(b"nonexistent\n")
        
        # Receive response
        response = client.recv(1024).decode('utf-8')
        assert response == "STRING NOT FOUND\n"
        
    finally:
        client.close()
        server.stop()
        server_thread.join(timeout=1) 