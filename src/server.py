"""
Main server module.
"""
import socket
import ssl
import threading
from typing import Optional

from config import Config
from search import FileSearcher
from utils import setup_logging, get_client_info, format_debug_message


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

    def setup_ssl(self) -> None:
        """Set up SSL context if enabled."""
        if self.config.ssl_enabled:
            self.ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            # TODO: Add certificate configuration
            self.logger.info("SSL enabled")

    def handle_client(self, client_socket: socket.socket) -> None:
        """
        Handle client connection.

        Args:
            client_socket: Client socket object
        """
        try:
            # Get client information
            ip_address, _ = get_client_info(client_socket)

            # Receive data
            data = client_socket.recv(1024).decode('utf-8')
            if not data:
                return

            # Search for string
            found, execution_time = self.searcher.search(data)

            # Prepare response
            response = "STRING EXISTS\n" if found else "STRING NOT FOUND\n"
            
            # Log debug information
            debug_msg = format_debug_message(data, ip_address, execution_time, found)
            self.logger.debug(debug_msg)

            # Send response
            client_socket.sendall(response.encode('utf-8'))

        except Exception as e:
            self.logger.error(f"Error handling client: {str(e)}")
        finally:
            client_socket.close()

    def start(self) -> None:
        """Start the server."""
        try:
            # Create server socket
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('', self.config.port))
            self.server_socket.listen(5)

            # Set up SSL if enabled
            self.setup_ssl()

            self.logger.info(f"Server started on port {self.config.port}")

            while True:
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
            self.logger.error(f"Server error: {str(e)}")
        finally:
            if self.server_socket:
                self.server_socket.close()

    def stop(self) -> None:
        """Stop the server."""
        if self.server_socket:
            self.server_socket.close()
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