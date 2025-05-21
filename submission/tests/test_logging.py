"""
Tests for logging functionality.
"""

# import os
import pytest
import logging
import time
import threading
import socket
import json
from pathlib import Path
from src.server import SearchServer
from src.client import SearchClient
import ssl


@pytest.fixture
def log_config(tmp_path):
    """Create logging configuration."""
    config_path = tmp_path / "config.ini"
    with open(config_path, "w") as f:
        f.write(
            """
[server]
port = 0
ssl_enabled = true
reread_on_query = false

[file]
linuxpath = test.txt

[rate_limit]
max_requests_per_minute = 100
window_seconds = 60
"""
        )
    return str(config_path)


def test_server_logging(log_config, caplog):
    """Test server logging functionality."""
    caplog.set_level(logging.INFO)

    server = SearchServer(log_config)
    server_thread = threading.Thread(target=server.start)
    server_thread.daemon = True
    server_thread.start()
    time.sleep(0.1)  # Give server time to start

    try:
        # Verify server startup logs
        assert "Server started" in caplog.text
        assert "SSL enabled - all connections must use SSL" in caplog.text

        # Test client connection
        client = SearchClient(port=server.port)
        found, _ = client.search("test string")

        # Verify connection logs
        assert "Accepted connection" in caplog.text
        assert "SSL handshake completed" in caplog.text
        assert "Handling client" in caplog.text

    finally:
        server.stop()
        server_thread.join(timeout=1)


def test_error_logging(log_config, caplog):
    """Test error logging functionality."""
    caplog.set_level(logging.ERROR)

    # Create a config for this test with a non-existent file
    # This will trigger a FileNotFoundError when the server reads the file
    config_path = Path(log_config)
    with open(config_path, "w") as f:
        f.write(
            """
[server]
port = 0
ssl_enabled = true
# Force file reload on each request
reread_on_query = true

[file]
# Non-existent file to trigger error
linuxpath = nonexistent_file.txt

[rate_limit]
max_requests_per_minute = 100
window_seconds = 60
"""
        )

    server = SearchServer(str(config_path))
    server_thread = threading.Thread(target=server.start)
    server_thread.daemon = True
    server_thread.start()
    time.sleep(0.1)  # Give server time to start

    try:
        # Create SSL context for client
        ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        ssl_context.verify_mode = ssl.CERT_REQUIRED
        ssl_context.check_hostname = True
        ssl_context.load_verify_locations(str(Path("certs") / "ca.crt"))
        ssl_context.load_cert_chain(
            str(Path("certs") / "client.crt"), str(Path(
                "certs") / "client.key")
        )

        # Create a raw socket connection with SSL
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock = ssl_context.wrap_socket(sock, server_hostname="localhost")
        sock.connect(("localhost", server.port))

        # Send a valid request that will trigger a file not found error
        # The server will try to read the non-existent file and log the error
        request = {"query": "test", "algorithm": "linear", "benchmark": False}
        sock.sendall((json.dumps(request) + "\n").encode("utf-8"))

        # Wait for response
        response = sock.recv(1024)
        assert response  # Should receive some response

        # Check that the error was logged
        error_logs = [
            record for record in caplog.records if (
                record.levelno >= logging.ERROR
                )
        ]
        assert any(
            "File not found" in record.message for record in error_logs
        ), "Expected file not found error to be logged"

    finally:
        server.stop()
        server_thread.join(timeout=1)


def test_debug_logging(log_config, caplog):
    """Test debug logging functionality."""
    caplog.set_level(logging.DEBUG)

    server = SearchServer(log_config)
    server_thread = threading.Thread(target=server.start)
    server_thread.daemon = True
    server_thread.start()
    time.sleep(0.1)  # Give server time to start

    try:
        # Test search with debug info
        client = SearchClient(port=server.port)
        found, _ = client.search("test string", benchmark=True)

        # Verify debug logs
        assert "DEBUG: Query=" in caplog.text
        assert "Time=" in caplog.text
        assert "Result=" in caplog.text

    finally:
        server.stop()
        server_thread.join(timeout=1)


def test_rate_limit_logging(log_config, caplog):
    """Test rate limit logging functionality."""
    caplog.set_level(logging.WARNING)

    server = SearchServer(log_config)
    server_thread = threading.Thread(target=server.start)
    server_thread.daemon = True
    server_thread.start()
    time.sleep(0.1)  # Give server time to start

    try:
        # Test rate limiting
        client = SearchClient(port=server.port)
        for _ in range(110):  # Exceed rate limit
            try:
                client.search("test string")
            except Exception:
                break

        # Verify rate limit logs
        assert "Rate limit exceeded" in caplog.text

    finally:
        server.stop()
        server_thread.join(timeout=1)


def test_ssl_logging(log_config, caplog):
    """Test SSL-related logging functionality."""
    caplog.set_level(logging.INFO)

    server = SearchServer(log_config)
    server_thread = threading.Thread(target=server.start)
    server_thread.daemon = True
    server_thread.start()
    time.sleep(0.1)  # Give server time to start

    try:
        # Test SSL connection
        client = SearchClient(port=server.port)
        found, _ = client.search("test string")

        # Verify SSL logs
        assert "SSL context configured" in caplog.text
        assert "SSL handshake completed" in caplog.text

    finally:
        server.stop()
        server_thread.join(timeout=1)
