"""
Tests for SSL functionality.
"""

# import os
import pytest
import ssl
import time
import threading
from pathlib import Path
from src.server import SearchServer
from src.client import SearchClient


@pytest.fixture
def ssl_config(tmp_path):
    """Create SSL configuration."""
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


def test_ssl_connection(ssl_config):
    """Test SSL connection establishment proper certificate verification."""
    server = SearchServer(ssl_config)
    server_thread = threading.Thread(target=server.start)
    server_thread.daemon = True
    server_thread.start()
    time.sleep(0.1)  # Give server time to start

    try:
        client = SearchClient(port=server.port)
        client.connect()  # Should establish SSL connection with certificate
        found, _ = client.search("test string")
        assert isinstance(found, bool)
    finally:
        server.stop()
        server_thread.join(timeout=1)


def test_ssl_certificate_verification(ssl_config):
    """Test SSL certificate verification requirements."""
    server = SearchServer(ssl_config)
    server_thread = threading.Thread(target=server.start)
    server_thread.daemon = True
    server_thread.start()
    time.sleep(0.1)  # Give server time to start

    try:
        # Create client with strict SSL verification
        client = SearchClient(port=server.port)

        # Create a new SSL context with strict verification
        client.ssl_context = ssl.create_default_context(
            ssl.Purpose.SERVER_AUTH
            )
        client.ssl_context.verify_mode = ssl.CERT_REQUIRED
        client.ssl_context.check_hostname = True

        # Try to load CA certificate (should fail if not found)
        cert_path = Path("certs")
        if not cert_path.exists():
            pytest.skip(
                "SSL certificates not found. Please run setup_ssl.sh first."
                )

        try:
            client.ssl_context.load_verify_locations(str(cert_path / "ca.crt"))
        except Exception as e:
            pytest.skip(f"Failed to load CA certificate: {e}")

        # Expect a successful connection since the CA is trusted
        client.connect()
    finally:
        server.stop()
        server_thread.join(timeout=1)


def test_ssl_protocol_negotiation(ssl_config):
    """Test SSL protocol negotiation with minimum TLS version."""
    server = SearchServer(ssl_config)
    server_thread = threading.Thread(target=server.start)
    server_thread.daemon = True
    server_thread.start()
    time.sleep(0.1)  # Give server time to start

    try:
        # Test with modern SSL protocols
        protocols = [
            ssl.PROTOCOL_TLS_CLIENT,  # Modern TLS client protocol
            ssl.PROTOCOL_TLS_CLIENT,  # Generic TLS protocol
        ]

        for protocol in protocols:
            client = SearchClient(port=server.port)
            client.ssl_context = ssl.SSLContext(protocol)
            client.ssl_context.verify_mode = ssl.CERT_REQUIRED
            client.ssl_context.check_hostname = True
            client.ssl_context.load_verify_locations(
                str(Path("certs") / "ca.crt")
                )
            client.ssl_context.load_cert_chain(
                str(
                    Path("certs") / "client.crt"), str(
                        Path("certs") / "client.key"
                        )
            )
            client.connect()  # Should establish SSL connection
            found, _ = client.search("test string")
            assert isinstance(found, bool)
            client.close()  # Properly close the connection
    finally:
        server.stop()
        server_thread.join(timeout=1)


def test_ssl_cipher_suites(ssl_config):
    """Test SSL cipher suite negotiation with secure defaults."""
    server = SearchServer(ssl_config)
    server_thread = threading.Thread(target=server.start)
    server_thread.daemon = True
    server_thread.start()
    time.sleep(0.1)  # Give server time to start

    try:
        client = SearchClient(port=server.port)
        client.connect()  # Should establish SSL connection
        # Get the negotiated cipher
        cipher = client.socket.cipher()
        assert cipher is not None
        assert len(cipher) >= 3  # Should return (name, version, bits)
        # Verify we're using a strong cipher
        assert "TLSv1.2" in cipher[1] or "TLSv1.3" in cipher[1]
    finally:
        server.stop()
        server_thread.join(timeout=1)


def test_ssl_certificate_chain(ssl_config):
    """Test SSL certificate chain verification."""
    server = SearchServer(ssl_config)
    server_thread = threading.Thread(target=server.start)
    server_thread.daemon = True
    server_thread.start()
    time.sleep(0.1)  # Give server time to start

    try:
        client = SearchClient(port=server.port)
        client.connect()  # Should establish SSL connection
        # Get the peer certificate
        cert = client.socket.getpeercert()
        assert cert is not None
        # Verify certificate chain
        assert client.ssl_context.verify_mode == ssl.CERT_REQUIRED
    finally:
        server.stop()
        server_thread.join(timeout=1)
