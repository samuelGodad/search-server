"""
Client module for the search server.
"""
import socket
import ssl
import json
from typing import Optional, Tuple, Dict, Any, Union
from pathlib import Path

from config import Config
from search import SearchAlgorithm


class SearchClient:
    """Client for the search server."""

    def __init__(self, port: int, config_path: Optional[str] = None, timeout: float = 5.0) -> None:
        """
        Initialize search client.

        Args:
            port: Server port number
            config_path: Path to the configuration file (optional)
            timeout: Socket timeout in seconds

        Raises:
            ValueError: If port number is invalid
        """
        if not isinstance(port, int) or port < 0 or port > 65535:
            raise ValueError("Port must be an integer between 0 and 65535")
            
        self.port = port
        self.timeout = timeout
        self.config = Config(config_path) if config_path else None
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
            
            self.socket.connect(('localhost', self.port))
        except Exception as e:
            raise ConnectionError(f"Failed to connect to server: {str(e)}")

    def search(self, query: str) -> str:
        """
        Search for string using legacy protocol.

        Args:
            query: String to search for

        Returns:
            Search result

        Raises:
            ConnectionRefusedError: If connection to server fails
            socket.timeout: If request times out
        """
        try:
            self.connect()
            self.socket.sendall(f"{query}\n".encode('utf-8'))
            response = self.socket.recv(4096).decode('utf-8').strip()
            return response
        finally:
            self.close()

    def search_json(self, query: str, algorithm: Union[str, SearchAlgorithm] = 'linear', benchmark: bool = False) -> str:
        """
        Search for string using JSON protocol.

        Args:
            query: String to search for
            algorithm: Search algorithm to use
            benchmark: Whether to enable benchmarking

        Returns:
            Search result

        Raises:
            ConnectionRefusedError: If connection to server fails
            socket.timeout: If request times out
        """
        if isinstance(algorithm, str):
            try:
                algorithm = SearchAlgorithm(algorithm)
            except ValueError:
                algorithm = SearchAlgorithm.LINEAR

        request = {
            'query': query,
            'algorithm': algorithm.value,
            'benchmark': benchmark
        }

        try:
            self.connect()
            self.socket.sendall(f"{json.dumps(request)}\n".encode('utf-8'))
            response = self.socket.recv(4096).decode('utf-8').strip()
            return response
        finally:
            self.close()

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

    # Use config file to get port number
    config = Config()
    client = SearchClient(port=config.port, config_path='config.ini')
    
    try:
        response = client.search_json(query, algorithm)
        print(response)
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        client.close()


if __name__ == "__main__":
    main() 

