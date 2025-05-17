"""
Main server module.
"""
import socket
import ssl
import threading
import json
from typing import Optional, Tuple
import time
from pathlib import Path

from config import Config
from search import FileSearcher, SearchAlgorithm
from utils import setup_logging, get_client_info, format_debug_message
from rate_limiter import RateLimiter


class SearchServer:
    """TCP server for string search operations."""

    def __init__(self, config_path: Optional[str] = None) -> None:
        """
        Initialize search server.

        Args:
            config_path: Path to the configuration file
        """
        self.config = Config(config_path)
        self.logger = setup_logging()
        self.searcher = FileSearcher(
            self.config.file_path,
            self.config.reread_on_query
        )
        self.server_socket: Optional[socket.socket] = None
        self.ssl_context: Optional[ssl.SSLContext] = None
        self.rate_limiter = RateLimiter(
            max_requests=self.config.max_requests_per_minute,
            time_window=60
        )
        self._running = False
        self._port = None

    @property
    def port(self) -> Optional[int]:
        """Get the actual port the server is running on."""
        return self._port

    def setup_ssl(self) -> None:
        """Set up SSL context if enabled."""
        if not self.config.ssl_enabled:
            return

        try:
            cert_path = Path('certs')
            if not cert_path.exists():
                self.logger.error("SSL certificates not found. Please run setup_ssl.sh first.")
                return

            self.ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            self.ssl_context.load_cert_chain(
                certfile=str(cert_path / 'server.crt'),
                keyfile=str(cert_path / 'server.key')
            )
            # Don't require client certificate for now
            self.ssl_context.verify_mode = ssl.CERT_NONE
            self.ssl_context.check_hostname = False
            
            self.logger.info("SSL context configured successfully")
        except Exception as e:
            self.logger.error(f"Failed to set up SSL: {str(e)}")
            raise

    def parse_request(self, data: str) -> Tuple[str, Optional[SearchAlgorithm], bool]:
        """
        Parse client request.

        Args:
            data: Raw request data

        Returns:
            Tuple of (query, algorithm, is_benchmark)
        """
        try:
            request = json.loads(data)
            query = request.get('query', '').strip()
            algorithm_name = request.get('algorithm', 'linear')
            is_benchmark = request.get('benchmark', False)
            
            try:
                algorithm = SearchAlgorithm(algorithm_name)
            except ValueError:
                algorithm = SearchAlgorithm.LINEAR
                
            return query, algorithm, is_benchmark
        except json.JSONDecodeError:
            # Legacy format: plain string
            return data.strip(), SearchAlgorithm.LINEAR, False

    def handle_client(self, client_socket: socket.socket) -> None:
        """
        Handle client connection.

        Args:
            client_socket: Client socket object
        """
        try:
            # Get client information
            ip_address, _ = get_client_info(client_socket)

            # Check rate limit
            is_allowed, remaining = self.rate_limiter.is_allowed(ip_address)
            if not is_allowed:
                response = "Rate limit exceeded"
                client_socket.sendall(f"{response}\n".encode('utf-8'))
                self.logger.warning(f"Rate limit exceeded for client {ip_address}")
                return

            # Receive data
            data = client_socket.recv(1024).decode('utf-8').strip()
            if not data:
                return

            # Remove null characters
            data = data.rstrip('\x00')
            
            # Parse request
            query, algorithm, is_benchmark = self.parse_request(data)
            
            # Search for string
            start_time = time.time()
            found, execution_time = self.searcher.search(query, algorithm)
            execution_time_ms = execution_time * 1000  # Convert to ms
            
            # Log debug info
            debug_msg = format_debug_message(
                query=query,
                ip_address=ip_address,
                execution_time=execution_time_ms,
                found=found
            )
            self.logger.debug(debug_msg)
            
            # Send response
            response = "STRING EXISTS" if found else "STRING NOT FOUND"
            client_socket.sendall(f"{response}\n".encode('utf-8'))
            
        except Exception as e:
            self.logger.error(f"Error handling client: {str(e)}")
            error_response = "Error processing request"
            client_socket.sendall(f"{error_response}\n".encode('utf-8'))
        finally:
            client_socket.close()

    def start(self) -> None:
        """Start the server."""
        try:
            # Create server socket
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('', self.config.port))
            self._port = self.server_socket.getsockname()[1]
            self.server_socket.listen(5)

            # Set up SSL if enabled
            self.setup_ssl()

            self._running = True
            self.logger.info(f"Server started on port {self._port}")

            while self._running:
                try:
                    client_socket, _ = self.server_socket.accept()
                    
                    # Wrap socket with SSL if enabled
                    if self.ssl_context:
                        client_socket = self.ssl_context.wrap_socket(
                            client_socket,
                            server_side=True
                        )

                    # Handle client in a new thread
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket,)
                    )
                    client_thread.start()
                except Exception as e:
                    if self._running:
                        self.logger.error(f"Error accepting connection: {str(e)}")

        except Exception as e:
            self.logger.error(f"Server error: {str(e)}")
        finally:
            self.stop()

    def stop(self) -> None:
        """Stop the server."""
        self._running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception as e:
                self.logger.error(f"Error closing server socket: {str(e)}")
            self.server_socket = None
            self.logger.info("Server stopped")


def main() -> None:
    """Main entry point."""
    server = SearchServer()
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()


if __name__ == "__main__":
    main() 
    