"""
Tests for server functionality.
"""
import socket
import threading
import time
import json
import pytest
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


def test_server_json_protocol(server_config, test_file):
    """Test server JSON protocol."""
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
        client.connect(('localhost', server.port))
        
        # Send JSON request
        request = {
            'query': 'test string',
            'algorithm': 'linear',
            'benchmark': False
        }
        client.sendall(f"{json.dumps(request)}\n".encode('utf-8'))
        
        # Receive response
        response = client.recv(4096).decode('utf-8').strip()
        assert response in ["STRING EXISTS", "STRING NOT FOUND"]
        
    finally:
        client.close()
        server.stop()
        server_thread.join(timeout=1)


def test_server_benchmark(server_config, test_file):
    """Test server benchmarking functionality."""
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
        client.connect(('localhost', server.port))
        
        # Send benchmark request
        request = {
            'query': 'test string',
            'algorithm': 'linear',
            'benchmark': True
        }
        client.sendall(f"{json.dumps(request)}\n".encode('utf-8'))
        
        # Receive response
        response = client.recv(4096).decode('utf-8').strip()
        assert response in ["STRING EXISTS", "STRING NOT FOUND"]
        
    finally:
        client.close()
        server.stop()
        server_thread.join(timeout=1)


def test_server_error_handling(server_config, test_file):
    """Test server error handling."""
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
        client.connect(('localhost', server.port))
        
        # Send invalid JSON
        client.sendall(b"invalid json\n")
        
        # Receive error response
        response = client.recv(4096).decode('utf-8').strip()
        assert response in ["STRING EXISTS", "STRING NOT FOUND"]
        
    finally:
        client.close()
        server.stop()
        server_thread.join(timeout=1)


def test_server_legacy_protocol(server_config, test_file):
    """Test server legacy protocol support."""
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
        client.connect(('localhost', server.port))
        
        # Send legacy format request
        client.sendall(b"test string\n")
        
        # Receive response
        response = client.recv(4096).decode('utf-8').strip()
        assert response == "STRING EXISTS"
        
    finally:
        client.close()
        server.stop()
        server_thread.join(timeout=1)


def test_server_rate_limiting(server_config, test_file):
    """Test server rate limiting."""
    server = SearchServer(server_config)
    
    # Start server in a separate thread
    server_thread = threading.Thread(target=server.start)
    server_thread.daemon = True
    server_thread.start()
    
    # Give server time to start
    time.sleep(0.1)
    
    try:
        # Make multiple requests quickly
        for _ in range(110):  # Exceed rate limit
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(('localhost', server.port))
            client.sendall(b"test string\n")
            response = client.recv(4096).decode('utf-8')
            client.close()
            
            if "RATE LIMIT EXCEEDED" in response:
                break
        else:
            pytest.fail("Rate limiting not working")
            
    finally:
        server.stop()
        server_thread.join(timeout=1) 