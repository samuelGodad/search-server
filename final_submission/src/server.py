"""
Main server module.
"""

import socket
import ssl
import threading
import json
from typing import Optional, Tuple
from concurrent.futures import ThreadPoolExecutor
# import time
from pathlib import Path
# import os

from config import Config
from search import FileSearcher, SearchAlgorithm
from utils import setup_logging, format_debug_message
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
            self.config.file_path, self.config.reread_on_query)
        self.server_socket: Optional[socket.socket] = None
        self.ssl_context: Optional[ssl.SSLContext] = None
        self.rate_limiter = RateLimiter(
            max_requests=self.config.max_requests_per_minute, window_seconds=60
        )
        self._running = False
        self._port = None
        self._shutdown_event = threading.Event()
        # Thread pool to limit concurrent connections
        self._thread_pool = ThreadPoolExecutor(max_workers=50)

    @property
    def port(self) -> Optional[int]:
        """Get the actual port the server is running on."""
        return self._port

    def setup_ssl(self) -> None:
        """Set up SSL context with strict security requirements."""
        try:
            cert_path = Path("certs")
            if not cert_path.exists():
                raise FileNotFoundError(
                    "SSL certificates not found. Run setup_ssl.sh first."
                )

            self.ssl_context = ssl.create_default_context(
                ssl.Purpose.CLIENT_AUTH)
            self.ssl_context.load_cert_chain(
                str(cert_path / "server.crt"), str(cert_path / "server.key")
            )

            # Always require client certificate verification
            self.ssl_context.verify_mode = ssl.CERT_REQUIRED
            self.ssl_context.load_verify_locations(str(cert_path / "ca.crt"))

            # Set minimum TLS version to 1.2 for better security
            self.ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2

            # Set secure cipher suites
            self.ssl_context.set_ciphers(
                "HIGH:!aNULL:!eNULL:!EXPORT:!SSLv2:!SSLv3"
            )

            self.logger.info(
                "SSL context configured successfully with strict security "
                "requirements"
            )
        except Exception as e:
            self.logger.error(f"SSL setup error: {str(e)}")
            raise RuntimeError(f"Failed to set up SSL: {str(e)}")

    def parse_request(
            self, data: str) -> Tuple[str, Optional[SearchAlgorithm], bool]:
        """
        Parse client request.

        Args:
            data: Raw request data

        Returns:
            Tuple of (query, algorithm, is_benchmark)

        Raises:
            ValueError: If the request is invalid
        """
        try:
            # Try to parse as JSON first
            request = json.loads(data)
            query = request.get("query", "").strip()
            algorithm_name = request.get("algorithm", "linear")
            is_benchmark = request.get("benchmark", False)

            if not query:
                raise ValueError("Empty query")

            try:
                algorithm = SearchAlgorithm(algorithm_name)
            except ValueError:
                algorithm = SearchAlgorithm.LINEAR

            return query, algorithm, is_benchmark
        except json.JSONDecodeError:
            # Only treat as legacy if it does NOT look like JSON
            if data.strip().startswith("{"):
                raise ValueError("Invalid JSON request")
            query = data.strip()
            if not query:
                raise ValueError("Empty query")
            return query, SearchAlgorithm.LINEAR, False

    def handle_client(
        self, client_socket: socket.socket, client_address: Tuple[str, int]
    ) -> None:
        """Handle a client connection."""
        self.logger.info(f"Handling client from {client_address}")
        try:
            # Read the request
            data = client_socket.recv(1024)
            if not data:
                return

            # Parse the request
            try:
                query, algorithm, benchmark = self.parse_request(
                    data.decode("utf-8")
                )
            except ValueError as e:
                self.logger.error(f"Invalid request: {str(e)}")
                client_socket.sendall(b"INVALID REQUEST\n")
                return
            except Exception as e:
                self.logger.error(f"Error parsing request: {str(e)}")
                client_socket.sendall(b"INVALID REQUEST\n")
                return

            # Check rate limit
            if not self.rate_limiter.check_rate_limit(client_address[0]):
                self.logger.warning(
                    f"Rate limit exceeded for {client_address[0]}")
                client_socket.sendall(b"RATE LIMIT EXCEEDED\n")
                return

            # Re-read file if needed
            try:
                if self.config.reread_on_query:
                    self.logger.debug(
                        f"Re-reading file for query: {query}, "
                        f"Algorithm: {algorithm}")
                    self.searcher = FileSearcher(
                        self.config.file_path, self.config.reread_on_query
                    )
            except FileNotFoundError as e:
                self.logger.error(f"File not found: {str(e)}")
                client_socket.sendall(b"FILE NOT FOUND\n")
                return
            except Exception as e:
                self.logger.error(f"Error reading file: {str(e)}")
                client_socket.sendall(b"INTERNAL ERROR\n")
                return

            # Perform search
            try:
                # Log debug info if benchmark mode
                if benchmark:
                    self.logger.debug(
                        f"Benchmark mode: Query={query}, Algorithm={algorithm}"
                        )

                # Perform the search
                found, execution_time = self.searcher.search(query, algorithm)

                # Log debug information
                debug_message = format_debug_message(
                    query, client_address[0], execution_time, found
                )
                self.logger.debug(debug_message)

                # Send response
                response = "STRING EXISTS\n" if found else "STRING NOT FOUND\n"
                client_socket.sendall(response.encode("utf-8"))

            except Exception as e:
                self.logger.error(f"Error during search: {str(e)}")
                client_socket.sendall(b"SEARCH ERROR\n")

        except Exception as e:
            self.logger.error(f"Error handling client: {str(e)}")
            try:
                client_socket.sendall(b"INTERNAL ERROR\n")
            except Exception:
                pass
        finally:
            client_socket.close()

    def _handle_connection(
        self, client_socket: socket.socket, client_address: Tuple[str, int]
    ) -> None:
        """Handle SSL wrapping and client processing."""
        try:
            # If SSL is enabled, wrap the socket immediately and verify
            if self.config.ssl_enabled:
                try:
                    # Perform SSL handshake with timeout
                    client_socket.settimeout(10.0)
                    client_socket = self.ssl_context.wrap_socket(
                        client_socket, server_side=True
                    )
                    # Verify client certificate
                    cert = client_socket.getpeercert()
                    if not cert:
                        raise ssl.SSLError(
                            "No client certificate provided"
                        )
                    self.logger.info(
                        "SSL handshake completed successfully"
                    )
                except ssl.SSLError as e:
                    self.logger.error(
                        f"SSL handshake failed from {client_address}: {str(e)}"
                    )
                    try:
                        client_socket.sendall(b"SSL_REQUIRED\n")
                    except Exception:
                        pass
                    client_socket.close()
                    return
                except Exception as e:
                    self.logger.error(
                        f"SSL connection error from {client_address}: {str(e)}"
                    )
                    client_socket.close()
                    return

            # Process the client request
            self.handle_client(client_socket, client_address)

        except Exception as e:
            self.logger.error(
                f"Error handling connection from {client_address}: {str(e)}"
            )
            try:
                client_socket.close()
            except Exception:
                pass

    def start(self) -> None:
        """Start the search server."""
        if self._running:
            self.logger.warning("Server is already running")
            return

        try:
            # Create server socket
            self.server_socket = socket.socket(
                socket.AF_INET, socket.SOCK_STREAM
            )
            self.server_socket.setsockopt(
                socket.SOL_SOCKET, socket.SO_REUSEADDR, 1
            )
            self.server_socket.bind(("localhost", self.config.port))
            self.server_socket.listen(5)
            # Set a timeout to allow checking shutdown event
            self.server_socket.settimeout(0.1)
            self._port = self.server_socket.getsockname()[1]
            self._running = True

            # Set up SSL if enabled
            if self.config.ssl_enabled:
                self.setup_ssl()
                if not self.ssl_context:
                    raise RuntimeError("SSL context not initialized")
                self.logger.info("SSL enabled - all connections must use SSL")

            self.logger.info(f"Server started on port {self._port}")

            while not self._shutdown_event.is_set():
                try:
                    # Accept client connection
                    client_socket, client_address = self.server_socket.accept()
                    self.logger.info(
                        f"Accepted connection from {client_address}"
                    )

                    # Submit connection handling to thread pool
                    self._thread_pool.submit(
                        self._handle_connection, client_socket, client_address
                    )

                except socket.timeout:
                    continue
                except Exception as e:
                    if not self._shutdown_event.is_set():
                        self.logger.error(
                            f"Error accepting connection: {str(e)}"
                        )

        except Exception as e:
            self.logger.error(f"Server error: {str(e)}")
            raise
        finally:
            self._running = False
            if self.server_socket:
                self.server_socket.close()
            # Shutdown thread pool gracefully
            self._thread_pool.shutdown(wait=True)

    def stop(self) -> None:
        """Stop the server."""
        if not self._running:
            return

        self._running = False
        self._shutdown_event.set()

        # Close the server socket to break the accept() call
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception as e:
                self.logger.error(f"Error closing server socket: {str(e)}")
            self.server_socket = None

        # Shutdown thread pool
        self._thread_pool.shutdown(wait=True)

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
