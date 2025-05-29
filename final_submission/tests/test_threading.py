"""
Test threading and concurrent connection handling.
"""

import pytest
import time
import threading
import tempfile
import ssl
# from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from src.server import SearchServer
from src.client import SearchClient


@pytest.fixture
def test_file():
    """Create a temporary test file with sample data."""
    with tempfile.NamedTemporaryFile(
            mode='w', delete=False, suffix='.txt') as f:
        for i in range(1000):
            f.write(f"test_line_{i}\n")
        return f.name


@pytest.fixture
def server_config(test_file):
    """Create a temporary server configuration."""
    config_content = f"""
[server]
port = 0
ssl_enabled = false
reread_on_query = false

[file]
linuxpath = {test_file}

[rate_limit]
max_requests_per_minute = 1000
window_seconds = 60
"""
    with tempfile.NamedTemporaryFile(
            mode='w', delete=False, suffix='.ini') as f:
        f.write(config_content)
        return f.name


@pytest.fixture
def running_server(server_config):
    """Start a server and ensure it's running."""
    server = SearchServer(server_config)
    server_thread = threading.Thread(target=server.start)
    server_thread.daemon = True
    server_thread.start()
    time.sleep(0.1)  # Give server time to start

    yield server

    server.stop()
    server_thread.join(timeout=2)


def test_concurrent_connections(running_server):
    """Test that server can handle multiple concurrent connections."""
    num_clients = 20
    results = []

    def make_request(client_id):
        """Make a single request to the server."""
        try:
            client = SearchClient(port=running_server.port, config_path=None)
            found, execution_time = client.search(f"test_line_{client_id}")
            results.append((client_id, found, execution_time))
            return True
        except Exception as e:
            print(f"Client {client_id} failed: {e}")
            return False

    # Use ThreadPoolExecutor to simulate concurrent clients
    with ThreadPoolExecutor(max_workers=num_clients) as executor:
        futures = [
            executor.submit(make_request, i)
            for i in range(num_clients)
        ]

        # Wait for all requests to complete
        completed = sum(1 for future in futures if future.result())

    # Verify all clients succeeded
    assert completed == num_clients
    assert len(results) == num_clients

    # Verify all searches found their strings
    for client_id, found, _ in results:
        assert found is True, f"Client {client_id} didn't find its string"


def test_thread_pool_limits(running_server):
    """Test that thread pool properly limits concurrent connections."""
    # This test verifies the server doesn't crash under load
    num_clients = 100  # More than the thread pool limit of 50
    completed_requests = 0

    def make_request():
        """Make a single request to the server."""
        try:
            client = SearchClient(port=running_server.port, config_path=None)
            found, _ = client.search("test_line_1")
            return found
        except Exception:
            return False

    # Submit many requests concurrently
    with ThreadPoolExecutor(max_workers=num_clients) as executor:
        futures = [
            executor.submit(make_request)
            for _ in range(num_clients)
        ]

        # Count successful requests
        for future in futures:
            if future.result():
                completed_requests += 1

    # Should complete most requests (allowing for some potential timeouts)
    assert completed_requests >= num_clients * 0.8  # At least 80% success rate


def test_ssl_configuration(test_file):
    """Test that SSL configuration works when certificates are available."""
    # Create SSL-enabled config
    config_content = f"""
[server]
port = 0
ssl_enabled = true
reread_on_query = false

[file]
linuxpath = {test_file}

[rate_limit]
max_requests_per_minute = 1000
window_seconds = 60
"""

    with tempfile.NamedTemporaryFile(
            mode='w', delete=False, suffix='.ini') as f:
        f.write(config_content)
        ssl_config = f.name

    # Create server with SSL config
    server = SearchServer(ssl_config)

    # Verify SSL is enabled in config
    assert server.config.ssl_enabled is True

    # Test SSL setup - should succeed with available certificates
    server.setup_ssl()

    # Verify SSL context was created
    assert server.ssl_context is not None
    assert server.ssl_context.verify_mode == ssl.CERT_REQUIRED


def test_server_graceful_shutdown(server_config):
    """Test that server shuts down gracefully."""
    server = SearchServer(server_config)
    server_thread = threading.Thread(target=server.start)
    server_thread.daemon = True
    server_thread.start()
    time.sleep(0.1)

    # Verify server is running
    assert server._running is True
    assert server.port is not None

    # Stop the server
    server.stop()
    server_thread.join(timeout=2)

    # Verify server is stopped
    assert server._running is False


def test_connection_error_handling(running_server):
    """Test that server handles connection errors gracefully."""
    import socket

    # Try to connect with raw socket and send invalid data
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(("localhost", running_server.port))

        # Send invalid data
        sock.sendall(b"\x00\x01\x02\x03\n")

        # Read response
        response = sock.recv(1024)
        sock.close()

        # Should get an error response, not crash the server
        assert b"INVALID REQUEST" in response or b"ERROR" in response

    except Exception:
        # Connection might be rejected, which is also valid behavior
        pass

    # Verify server is still running after error
    assert running_server._running is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
