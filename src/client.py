"""
Client module for the search server.
"""
import socket
import ssl
import json
from typing import Optional, Tuple, Dict, Any
from pathlib import Path

from config import Config


class SearchClient:
    """Client for the search server."""

    def __init__(self, config_path: Optional[str] = None) -> None:
        """
        Initialize search client.

        Args:
            config_path: Path to the configuration file
        """
        self.config = Config(config_path)
        self.socket: Optional[socket.socket] = None
        self.ssl_context: Optional[ssl.SSLContext] = None

    def setup_ssl(self) -> None:
        """Set up SSL context if enabled."""
        if not self.config.ssl_enabled:
            return

        try:
            cert_path = Path('certs')
            if not cert_path.exists():
                raise FileNotFoundError("SSL certificates not found. Please run setup_ssl.sh first.")

            self.ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
            self.ssl_context.load_verify_locations(str(cert_path / 'server.crt'))
            # Don't verify hostname for local development
            self.ssl_context.check_hostname = False
            self.ssl_context.verify_mode = ssl.CERT_NONE
        except Exception as e:
            raise RuntimeError(f"Failed to set up SSL: {str(e)}")

    def connect(self) -> None:
        """Connect to the server."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            if self.config.ssl_enabled:
                self.setup_ssl()
                self.socket = self.ssl_context.wrap_socket(
                    self.socket,
                    server_hostname='localhost'
                )
            
            self.socket.connect(('localhost', self.config.port))
        except Exception as e:
            raise ConnectionError(f"Failed to connect to server: {str(e)}")

    def search(self, query: str, algorithm: str = 'linear', benchmark: bool = False) -> Tuple[bool, float]:
        """
        Search for a string on the server.

        Args:
            query: String to search for
            algorithm: Search algorithm to use
            benchmark: Whether to run in benchmark mode

        Returns:
            Tuple of (found, execution_time)
        """
        if not self.socket:
            self.connect()

        try:
            # Prepare request
            request = {
                'query': query,
                'algorithm': algorithm,
                'benchmark': benchmark
            }
            request_data = json.dumps(request).encode('utf-8')

            # Send request
            self.socket.sendall(request_data)

            # Receive response
            response = self.socket.recv(1024).decode('utf-8').strip()
            
            # Parse response
            if response == "STRING EXISTS":
                return True, 0.0
            elif response == "STRING NOT FOUND":
                return False, 0.0
            else:
                raise RuntimeError(f"Unexpected response: {response}")

        except Exception as e:
            raise RuntimeError(f"Search failed: {str(e)}")

    def close(self) -> None:
        """Close the connection."""
        if self.socket:
            self.socket.close()
            self.socket = None


def main() -> None:
    """Main entry point."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python client.py <query> [algorithm]")
        sys.exit(1)

    query = sys.argv[1]
    algorithm = sys.argv[2] if len(sys.argv) > 2 else 'linear'

    client = SearchClient()
    try:
        found, _ = client.search(query, algorithm)
        print("STRING EXISTS" if found else "STRING NOT FOUND")
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        client.close()


if __name__ == "__main__":
    main() 

