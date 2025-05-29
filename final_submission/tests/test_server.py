"""
Tests for server functionality.
"""

import socket
import threading
import time
import json
import pytest
import ssl
from pathlib import Path
from src.server import SearchServer

# from src.search import SearchAlgorithm


def create_ssl_client():
    """Create an SSL-wrapped client socket."""
    # Create SSL context
    ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    ssl_context.load_verify_locations(str(Path("certs/ca.crt")))
    ssl_context.load_cert_chain(
        str(Path("certs/client.crt")), str(Path("certs/client.key"))
    )

    # Create socket and wrap with SSL
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    return ssl_context.wrap_socket(sock, server_hostname="localhost")


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
        # Connect to server with SSL
        client = create_ssl_client()
        client.connect(("localhost", server.port))

        # Send JSON request
        request = {
            "query": "test string", "algorithm": "linear", "benchmark": False
            }
        client.sendall(f"{json.dumps(request)}\n".encode("utf-8"))

        # Receive response
        response = client.recv(4096).decode("utf-8").strip()
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
        # Connect to server with SSL
        client = create_ssl_client()
        client.connect(("localhost", server.port))

        # Send benchmark request
        request = {
            "query": "test string", "algorithm": "linear", "benchmark": True
            }
        client.sendall(f"{json.dumps(request)}\n".encode("utf-8"))

        # Receive response
        response = client.recv(4096).decode("utf-8").strip()
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
        # Connect to server with SSL
        client = create_ssl_client()
        client.connect(("localhost", server.port))

        # Send invalid JSON
        client.sendall(b"invalid json\n")

        # Receive error response
        response = client.recv(4096).decode("utf-8").strip()
        assert response in ["INVALID REQUEST", "STRING NOT FOUND"]

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
        # Connect to server with SSL
        client = create_ssl_client()
        client.connect(("localhost", server.port))

        # Send legacy format request
        client.sendall(b"test string\n")

        # Receive response
        response = client.recv(4096).decode("utf-8").strip()
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
            client = create_ssl_client()
            client.connect(("localhost", server.port))
            client.sendall(b"test string\n")
            response = client.recv(4096).decode("utf-8")
            client.close()

            if "RATE LIMIT EXCEEDED" in response:
                break
        else:
            pytest.fail("Rate limiting not working")

    finally:
        server.stop()
        server_thread.join(timeout=1)


def test_server_high_load(server_config, test_file):
    """Test server behavior under high load conditions."""
    import threading
    import time
    from src.client import SearchClient
    from src.server import SearchServer
    import tempfile
    import os

    # Create a temporary config file with ssl_enabled = true
    with tempfile.NamedTemporaryFile("w+", delete=False) as tmp_config:
        tmp_config.write(
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
        tmp_config_path = tmp_config.name

    print("[DEBUG] Creating server with test config (SSL enabled)...")
    server = SearchServer(tmp_config_path)

    print("[DEBUG] Starting server thread...")
    server_thread = threading.Thread(target=server.start)
    server_thread.daemon = True
    server_thread.start()

    print("[DEBUG] Waiting for server to start...")
    time.sleep(1)
    server_port = server.port
    print(f"[DEBUG] Server started on port {server_port}")

    num_clients = 5
    clients = []
    for i in range(num_clients):
        print(f"[DEBUG] Creating client {i}...")
        client = SearchClient(port=server_port, config_path=tmp_config_path)
        clients.append(client)

    def search_task(client, idx, results):
        print(f"[DEBUG] Thread {idx} starting search_task...")
        try:
            start = time.time()
            # Use a query that exists in the test file and explicit algorithm
            result = client.search(
                "test string", algorithm="linear", benchmark=False
                )
            elapsed = time.time() - start
            print(
                f"[DEBUG] Thread {idx} finished search result: {result} in {
                    elapsed:.2f}s"
            )
            results[idx] = result
        except Exception as e:
            print(f"[DEBUG] Thread {idx} search_task exception: {e}")
            results[idx] = str(e)

    threads = []
    results = [None] * num_clients
    for idx, client in enumerate(clients):
        print(f"[DEBUG] Starting thread {idx} for client...")
        thread = threading.Thread(
            target=search_task, args=(client, idx, results)
            )
        threads.append(thread)
        thread.start()

    for idx, thread in enumerate(threads):
        print(f"[DEBUG] Joining thread {idx}...")
        thread.join(timeout=5)
        if thread.is_alive():
            print(
                f"[WARNING] Thread {idx} didn't finish in time &still alive!"
                )
        else:
            print(f"[DEBUG] Thread {idx} joined.")

    success_count = sum(
        1 for r in results if r is not None and not isinstance(r, str)
        )
    error_count = sum(1 for r in results if isinstance(r, str))
    print(
        f"[DEBUG] Success count: {success_count}, Error count: {error_count}"
        )

    assert success_count > error_count, "Server failed under high load"

    print("[DEBUG] Stopping server...")
    server.stop()
    print("[DEBUG] Server stopped. Joining server thread...")
    server_thread.join(timeout=5)
    print("[DEBUG] Server thread joined.")

    # Clean up temp config file
    os.remove(tmp_config_path)


def test_server_special_characters(server_config, test_file):
    """Test server handling of special characters in search queries."""
    server = SearchServer(server_config)
    server_thread = threading.Thread(target=server.start)
    server_thread.daemon = True
    server_thread.start()
    time.sleep(0.1)
    try:
        # Connect to server with SSL
        client = create_ssl_client()
        client.connect(("localhost", server.port))

        special_query = "!@#$%^&*()_+-=[]{}`~;:'\",.<>/?|"
        request = {
            "query": special_query, "algorithm": "linear", "benchmark": False
            }
        client.sendall(f"{json.dumps(request)}\n".encode("utf-8"))
        response = client.recv(4096).decode("utf-8").strip()
        print(f"[DEBUG] Special character query response: {response}")
        assert response in ["STRING EXISTS", "STRING NOT FOUND"]
    finally:
        client.close()
        server.stop()
        server_thread.join(timeout=1)
